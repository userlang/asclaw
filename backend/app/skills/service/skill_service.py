# 作者：langjunnan
# 开发时间：2025年7月23日

import re

import httpx
import yaml
from loguru import logger
from sqlalchemy import Select

from app.admin.crud.crud_user import user_dao
from app.skills.crud.crud_skill import skill_dao
from app.skills.crud.crud_skill_category import skill_category_dao
from app.skills.crud.crud_skill_content import skill_content_dao
from app.skills.model import AgentSkill, SkillContent
from common.exception import errors
from database.db import async_db_session

# GitHub 目录 URL → raw 文件 URL 的两种形态：
#   https://github.com/{owner}/{repo}/tree/{ref}/{dir}  → main 分支
#   https://github.com/{owner}/{repo}/blob/{ref}/{dir}  → 同样按目录处理
_GITHUB_URL_RE = re.compile(
    r'^https?://(?:www\.)?github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)'
    r'/(?:tree|blob)/(?P<ref>[^/]+)/(?P<dir>.+?)/?$'
)

# SKILL.md frontmatter 里允许提取的字段
_ALLOWED_META = {'name', 'description'}


class SkillError(errors.BaseExceptionError):
    """skill 模块业务异常

    继承 BaseExceptionError 以命中全局自定义异常处理器，
    保证 code/msg 原样返回（RequestError 系列会变成无信息的 500）。
    """

    def __init__(self, *, code: int = 400, msg: str = 'Bad Request'):
        self.code = code
        super().__init__(msg=msg)


class SkillService:
    @staticmethod
    async def get_select(*, keyword: str, category_id: int) -> Select:
        return await skill_dao.get_list(keyword=keyword, category_id=category_id)

    @staticmethod
    async def get_my_skills(*, user_id: int) -> Select:
        return await skill_dao.get_my_skills(user_id=user_id)

    @staticmethod
    async def get_skill_by_user(username: str, skill_name: str) -> AgentSkill | None:
        async with async_db_session() as db:
            user = await user_dao.get_by_username(db, username)
            if not user:
                raise errors.NotFoundError(msg='用户不存在')
            return await skill_dao.get_skill_by_user(db, skill_name, user.id)

    @staticmethod
    async def get_public_skill_by_user(username: str, skill_name: str) -> AgentSkill | None:
        """获取用户已公开的 skill 详情（仅 is_public=1），用于详情页展示"""
        async with async_db_session() as db:
            user = await user_dao.get_by_username(db, username)
            if not user:
                raise errors.NotFoundError(msg='用户不存在')
            return await skill_dao.get_public_skill_by_user(db, skill_name, user.id)

    @staticmethod
    async def get_categories() -> list:
        async with async_db_session() as db:
            stmt = await skill_category_dao.get_all_categories()
            result = await db.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def publish_skill(
        *,
        user_id: int,
        name: str,
        title: str,
        description: str,
        category_id: int | None = None,
        source_url: str | None = None,
        body: str | None = None,
    ) -> AgentSkill:
        """发布 skill：解析来源（GitHub SKILL.md）或使用手填正文，落库并返回实例"""
        async with async_db_session.begin() as db:
            user = await user_dao.get(db, user_id)
            if not user:
                raise SkillError(msg='用户不存在')

            existing = await skill_dao.get_by_name_and_user(db, name, user_id)
            if existing:
                raise SkillError(msg=f'你已存在同名 skill：{name}')

            if category_id is not None:
                stmt = await skill_category_dao.get_all_categories()
                result = await db.execute(stmt)
                valid_ids = {c.id for c in result.scalars().all()}
                if category_id not in valid_ids:
                    raise SkillError(msg='分类不存在')

            fetched_body: str | None = None
            repository = ''
            path = f'/skills/{name}'
            content_files: list[dict] = []

            if source_url:
                fetched_body, repository, content_files = await SkillService._fetch_source(source_url)

            final_body = body or fetched_body
            if not final_body:
                raise SkillError(msg='缺少 SKILL.md 正文：请填写来源 URL（含 SKILL.md）或直接粘贴正文')

            skill = AgentSkill(
                name=name,
                title=title,
                avatar='',
                description=description,
                repository=repository,
                path=path,
                body=final_body,
                source_url=source_url,
                is_public=True,
                status=1,
                category_id=category_id,
                user_id=user_id,
            )
            db.add(skill)
            await db.flush()

            # 附加文件落库（SKILL.md 之外的 scripts/references 等）
            for f in content_files:
                db.add(
                    SkillContent(skill_id=skill.id, file_path=f['file_path'], content=f['content'])
                )

        # 事务提交后用新会话回查并预加载 user/category 关联：
        # 同一事务内刚 flush 的实例命中 identity map，selectinload 不会补关联，
        # 直接返回会导致响应序列化取 data.user.username 失败
        async with async_db_session() as db:
            return await skill_dao.get_public_skill_by_user(db, name, user_id)

    @staticmethod
    async def delete_my_skill(*, user_id: int, skill_id: int) -> int:
        """删除自己的 skill（含附加内容）"""
        async with async_db_session.begin() as db:
            skill = await skill_dao.select_model(db, pk=skill_id)
            if not skill:
                raise SkillError(code=404, msg='Skill 不存在')
            if skill.user_id != user_id:
                raise SkillError(code=403, msg='无权删除他人的 skill')
            await skill_content_dao.delete_by_skill(db, skill_id)
            return await skill_dao.delete_model(db, skill_id)

    @staticmethod
    async def increment_install_count(skill_id: int) -> None:
        """在线体验时累计使用次数（失败不阻塞聊天）"""
        try:
            async with async_db_session.begin() as db:
                skill = await skill_dao.select_model(db, pk=skill_id)
                if skill:
                    skill.install_count += 1
        except Exception as e:
            logger.warning('Failed to increment install_count for skill {}: {}', skill_id, e)

    @staticmethod
    async def get_skill_contents(skill_id: int) -> list:
        async with async_db_session() as db:
            return await skill_content_dao.get_by_skill(db, skill_id)

    # ---------- 内部：来源抓取 ----------

    @staticmethod
    def _parse_github_dir(url: str) -> tuple[str, str, str, str] | None:
        """解析 GitHub 目录 URL → (owner, repo, ref, dir)；非 GitHub 返回 None"""
        m = _GITHUB_URL_RE.match(url.strip())
        if not m:
            return None
        return m.group('owner'), m.group('repo'), m.group('ref'), m.group('dir')

    @staticmethod
    async def _fetch_github_file(owner: str, repo: str, ref: str, path: str) -> httpx.Response:
        url = f'https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}'
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url)
            return resp

    @staticmethod
    async def _fetch_source(source_url: str) -> tuple[str | None, str, list[dict]]:
        """抓取来源：目前支持 GitHub 目录 URL。

        返回 (SKILL.md 正文, repository, 附加文件列表)。
        抓取失败不阻塞发布：正文回退为 None（由调用方决定报错或用手填 body）。
        """
        gh = SkillService._parse_github_dir(source_url)
        if not gh:
            # 非 GitHub 链接：记录并按直接 URL 试试（例如指向 raw SKILL.md 的链接）
            if source_url.rstrip('/').endswith('.md'):
                try:
                    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                        resp = await client.get(source_url)
                        if resp.status_code == 200:
                            return resp.text, source_url, []
                except Exception as e:
                    logger.warning('Failed to fetch skill source {}: {}', source_url, e)
            return None, source_url, []

        owner, repo, ref, directory = gh
        repository = f'{owner}/{repo}'
        try:
            resp = await SkillService._fetch_github_file(owner, repo, ref, f'{directory}/SKILL.md')
            if resp.status_code != 200:
                logger.warning('SKILL.md not found at {} (HTTP {})', source_url, resp.status_code)
                return None, repository, []
            skill_md = resp.text
        except Exception as e:
            logger.warning('Failed to fetch SKILL.md from {}: {}', source_url, e)
            return None, repository, []

        # 提取 frontmatter 里的 name/description（若有），供调用方参考（当前仅日志）
        try:
            if skill_md.lstrip().startswith('---'):
                _, fm, _body = skill_md.split('---', 2)
                meta = yaml.safe_load(fm) or {}
                if isinstance(meta, dict):
                    unknown = set(meta) - _ALLOWED_META
                    if unknown:
                        logger.info('SKILL.md frontmatter extra fields ignored: {}', sorted(unknown))
        except Exception as e:
            logger.warning('Failed to parse SKILL.md frontmatter: {}', e)

        # 附加文件：SKILL.md 里引用的 scripts/**、references/**（纯文本，大小限制 64KB）
        content_files: list[dict] = []
        for rel in set(re.findall(r'(?:scripts|references)/[\w./-]+', skill_md)):
            if rel.endswith(('/', '.')):
                continue
            try:
                fresp = await SkillService._fetch_github_file(owner, repo, ref, f'{directory}/{rel}')
                if fresp.status_code == 200 and len(fresp.text) <= 64 * 1024:
                    content_files.append({'file_path': rel, 'content': fresp.text})
            except Exception as e:
                logger.warning('Failed to fetch skill file {}: {}', rel, e)

        return skill_md, repository, content_files


skill_service: SkillService = SkillService()
