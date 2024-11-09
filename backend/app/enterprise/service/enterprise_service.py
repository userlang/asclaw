# 作者：langjunnan
# 开发时间：2025年7月23日

from __future__ import annotations

import bcrypt

from app.admin.crud.crud_user import user_dao
from app.admin.model import User
from app.admin.model.m2m import user_role
from app.admin.schema.token import GetLoginToken
from app.admin.schema.user import AuthLoginParam
from app.admin.service.auth_service import auth_service
from app.admin.service.login_log_service import login_log_service
from common.context import ctx
from common.enums import LoginLogStatusType
from common.exception import errors
from common.exception.errors import BaseExceptionError
from common.security.jwt import create_access_token, create_refresh_token
from core.conf import settings
from database.db import async_db_session
from fastapi import BackgroundTasks, Request, Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.password_security import get_hash_password, password_verify
from utils.timezone import timezone

from app.enterprise.crud.crud_enterprise import enterprise_dao
from app.enterprise.model.enterprise import Enterprise
from app.enterprise.schema.enterprise import (
    EnterpriseApplyParam,
    EnterpriseReviewParam,
    UpdateEnterpriseParam,
)


class EnterpriseError(BaseExceptionError):
    """企业模块业务异常

    继承 BaseExceptionError 以命中全局自定义异常处理器，
    保证 code/msg 原样返回（BaseExceptionMixin 不在任何 handler 注册树里，
    直接抛 RequestError 会变成无信息的 500）。
    """

    def __init__(self, *, code: int = 400, msg: str = 'Bad Request'):
        self.code = code
        super().__init__(msg=msg)


class EnterpriseService:
    @staticmethod
    async def apply(db: AsyncSession, obj: EnterpriseApplyParam) -> Enterprise:
        """提交入驻申请（待审核状态）"""
        if await enterprise_dao.get_by_username(db, obj.username):
            raise EnterpriseError(msg='该用户名已被使用，请更换')
        enterprise = Enterprise(
            **obj.model_dump(exclude={'password'}),
            password=get_hash_password(obj.password, bcrypt.gensalt()),
            status=0,
        )
        return await enterprise_dao.create(db, enterprise)

    @staticmethod
    async def _ensure_enterprise_user(db: AsyncSession, enterprise: Enterprise) -> User:
        """确保企业拥有对应的 sys_user 账号（企业登录信息以用户表为准）

        - 已关联：直接复用，并把密码与企业表同步（管理员重置密码可能只改了一侧）
        - 未关联（历史数据/首次登录）：用企业表凭据自动创建用户并建立关联
        """
        if enterprise.user_id:
            user = await db.get(User, enterprise.user_id)
            if user:
                if user.password != enterprise.password:
                    user.password = enterprise.password
                return user
            # 关联的用户已被删除，走下方重建逻辑

        # sys_user.username 唯一：与企业用户名冲突时追加企业 ID 避让
        username = enterprise.username
        if await user_dao.get_by_username(db, username):
            username = f'{enterprise.username}_{enterprise.id}'
        user = User(
            username=username,
            nickname=enterprise.name[:20],
            password=enterprise.password,
            salt=None,
        )
        db.add(user)
        await db.flush()
        enterprise.user_id = user.id
        return user

    async def login(
        self,
        *,
        request: Request,
        response: Response,
        background_tasks: BackgroundTasks,
        username: str,
        password: str,
    ) -> GetLoginToken:
        """企业登录：审核通过后创建/关联 sys_user 并签发标准用户 JWT"""
        async with async_db_session.begin() as db:
            enterprise = await enterprise_dao.get_by_username(db, username)
            if not enterprise:
                # 非企业用户（如平台管理员）走标准用户名密码登录；
                # auth_service.login 读取 request.state.*，而 StateMiddleware 只写 ctx，
                # 此处从 ctx 桥接补齐，否则 AttributeError
                request.state.ip = ctx.ip
                request.state.os = ctx.os
                request.state.browser = ctx.browser
                request.state.device = ctx.device
                # auth_service 抛出的 RequestError 系会变成无信息 500，这里转成业务异常
                try:
                    return await auth_service.login(
                        request=request,
                        response=response,
                        obj=AuthLoginParam(username=username, password=password),
                        background_tasks=background_tasks,
                    )
                except errors.NotFoundError as e:
                    raise EnterpriseError(msg=e.msg) from e
                except errors.AuthorizationError as e:
                    raise EnterpriseError(code=e.code, msg=e.msg) from e
                except errors.RequestError as e:
                    raise EnterpriseError(code=e.code, msg=e.msg) from e

            if not password_verify(password, enterprise.password):
                raise EnterpriseError(msg='用户名或密码错误')
            if enterprise.status == 0:
                raise EnterpriseError(code=403, msg='入驻申请审核中，暂不能登录')
            if enterprise.status == 2:
                reason = enterprise.reject_reason or '请联系管理员'
                raise EnterpriseError(code=403, msg=f'入驻申请未通过：{reason}')

            user = await self._ensure_enterprise_user(db, enterprise)
            if not user.status:
                raise EnterpriseError(code=403, msg='账号已被锁定，请联系管理员')
            await user_dao.update_login_time(db, user.username)

        access_token = await create_access_token(
            user.id,
            username=user.username,
            nickname=user.nickname,
            last_login_time=timezone.to_str(timezone.now()),
            ip=ctx.ip,
            os=ctx.os,
            browser=ctx.browser,
            device=ctx.device,
        )
        refresh_token = await create_refresh_token(access_token.session_uuid, user.id)
        response.set_cookie(
            key=settings.COOKIE_REFRESH_TOKEN_KEY,
            value=refresh_token.refresh_token,
            max_age=settings.COOKIE_REFRESH_TOKEN_EXPIRE_SECONDS,
            expires=timezone.to_utc(refresh_token.refresh_token_expire_time),
            httponly=True,
        )

        background_tasks.add_task(
            login_log_service.create,
            **dict(
                user_uuid=user.uuid,
                username=user.username,
                login_time=timezone.now(),
                status=LoginLogStatusType.success.value,
                msg='企业账号登录成功',
            ),
        )

        return GetLoginToken(
            access_token=access_token.access_token,
            access_token_expire_time=access_token.access_token_expire_time,
            session_uuid=access_token.session_uuid,
            user=user,  # type: ignore
        )

    @staticmethod
    async def get_detail(pk: int) -> Enterprise | None:
        async with async_db_session() as db:
            return await enterprise_dao.get_by_id(db, pk)

    @staticmethod
    async def get_select(status: int | None = None, keyword: str | None = None) -> select:
        """管理端分页查询 select"""
        return await enterprise_dao.get_select(status=status, keyword=keyword)

    @staticmethod
    async def update(db: AsyncSession, pk: int, obj: UpdateEnterpriseParam) -> None:
        """管理员修改企业信息 / 重置密码（同步到关联的用户账号）"""
        enterprise = await enterprise_dao.get_by_id(db, pk)
        if not enterprise:
            raise EnterpriseError(code=404, msg='企业不存在')
        data = obj.model_dump(exclude_unset=True, exclude={'password'})
        old_username = enterprise.username
        if obj.username and obj.username != old_username:
            if await enterprise_dao.get_by_username(db, obj.username):
                raise EnterpriseError(msg='该用户名已被使用，请更换')
        for field, value in data.items():
            setattr(enterprise, field, value)
        if obj.password:
            enterprise.password = get_hash_password(obj.password, bcrypt.gensalt())

        # 同步关联用户：密码始终一致；用户名仅在当初未加避让后缀时跟随修改
        if enterprise.user_id:
            user = await db.get(User, enterprise.user_id)
            if user:
                user.password = enterprise.password
                if obj.username and user.username == old_username:
                    if not await user_dao.get_by_username(db, obj.username):
                        user.username = obj.username

    @staticmethod
    async def review(db: AsyncSession, obj: EnterpriseReviewParam, reviewed_by: int) -> int:
        """批量审核：通过（1）或拒绝（2）；通过时自动创建/关联用户账号"""
        count = 0
        for pk in obj.pks:
            enterprise = await enterprise_dao.get_by_id(db, pk)
            if not enterprise:
                continue
            enterprise.status = obj.status
            enterprise.reject_reason = obj.reject_reason if obj.status == 2 else None
            enterprise.reviewed_by = reviewed_by
            enterprise.reviewed_time = timezone.now()
            if obj.status == 1:
                await EnterpriseService._ensure_enterprise_user(db, enterprise)
            count += 1
        return count

    @staticmethod
    async def delete_batch(db: AsyncSession, pks: list[int]) -> int:
        """批量删除企业，并清理自动创建的关联用户账号"""
        result = await db.execute(select(Enterprise).where(Enterprise.id.in_(pks)))
        user_ids = [e.user_id for e in result.scalars() if e.user_id]
        count = await enterprise_dao.delete_batch(db, pks)
        if user_ids:
            await db.execute(delete(user_role).where(user_role.c.user_id.in_(user_ids)))
            await db.execute(delete(User).where(User.id.in_(user_ids)))
        return count


enterprise_service: EnterpriseService = EnterpriseService()
