"""为每个 MCP server 合成「工具组描述」，供 agentscope create_tool_group 的 description 使用。

默认 dry-run：只打印结果，不写库。确认质量后加 --write 写入 server_metadata.tool_group_description。

用法（cwd=backend/，依赖 .env 的 DATABASE_* 与 DASHSCOPE_* 配置）：
    uv run python scripts/synthesize_tool_group_descriptions.py            # dry-run
    uv run python scripts/synthesize_tool_group_descriptions.py --limit 3  # 只跑前 3 个
    uv run python scripts/synthesize_tool_group_descriptions.py --write    # 写库
"""

import argparse
import asyncio
import json
import sys

from openai import AsyncOpenAI
from sqlalchemy import select

from app.mcp.model.mcp import McpServer
from core.conf import settings
from database.db import async_db_session

PROMPT = """\
你是 MCP 工具编排系统的配置助手。下面给出一个 MCP Server 的名称和它全部工具的名称与描述。
请把这些工具汇总成一段「工具组描述」，它将作为大模型决定"当前任务是否要装备这一组工具"的唯一依据。

要求：
1. 先一句话概括这组工具覆盖的能力域（如：GitHub 仓库的 issue/PR/代码搜索操作）。
2. 按功能聚类列出主要能力（读操作/写操作/查询类等），工具多时可以多写几句，不要为精简而遗漏重要能力。
3. 如果存在破坏性操作（删除/关闭/强制推送等），在末尾用一句话提醒。
4. 用中文输出，纯文本，不要 markdown 标题或列表符号，不超过 300 字。
5. 只输出描述本身，不要任何前后缀说明。

MCP Server 名称：{title}

工具列表：
{tools}
"""


def _render_tools(tools: list[dict]) -> str:
    """tools JSON -> 每行 'name: description'，附破坏性标记。"""
    lines = []
    for t in tools:
        desc = (t.get('description') or '').strip().replace('\n', ' ')
        if len(desc) > 200:  # 单条描述过长截断，控制输入 token
            desc = desc[:200] + '…'
        destructive = (t.get('annotations') or {}).get('destructiveHint')
        flag = ' [破坏性]' if destructive else ''
        lines.append(f"- {t.get('name', '?')}: {desc}{flag}")
    return '\n'.join(lines)


async def _summarize(client: AsyncOpenAI, title: str, tools_json: list[dict]) -> str:
    resp = await client.chat.completions.create(
        model=settings.DASHSCOPE_CHAT_MODEL,
        messages=[{'role': 'user', 'content': PROMPT.format(title=title, tools=_render_tools(tools_json))}],
        temperature=0.3,
        max_tokens=600,
        extra_body={'enable_thinking': False},
    )
    usage = resp.usage
    print(
        f'    [token] in={usage.prompt_tokens} out={usage.completion_tokens}',
        file=sys.stderr,
    )
    return (resp.choices[0].message.content or '').strip()


async def main(limit: int | None, write: bool) -> None:
    async with async_db_session() as db:
        rows = (await db.execute(select(McpServer).order_by(McpServer.id))).scalars().all()

    # ---- 覆盖率报告 ----
    empty = [r for r in rows if not (r.tools and isinstance(r.tools, list))]
    todo = [r for r in rows if r.tools and isinstance(r.tools, list)]
    print(f'共 {len(rows)} 个 server：可合成 {len(todo)}，tools 为空（需先重跑编译）{len(empty)}')
    for r in empty:
        print(f'  [空 tools] id={r.id} {r.server_title}')
    print()

    if limit:
        todo = todo[:limit]

    client = AsyncOpenAI(api_key=settings.DASHSCOPE_API_KEY, base_url=settings.DASHSCOPE_BASE_URL)
    sem = asyncio.Semaphore(5)

    async def one(row: McpServer) -> tuple[McpServer, str | None]:
        async with sem:
            try:
                text = await _summarize(client, row.server_title, row.tools)
                return row, text
            except Exception as e:  # noqa: BLE001
                print(f'  [失败] id={row.id} {row.server_title}: {e!r}', file=sys.stderr)
                return row, None

    results = await asyncio.gather(*(one(r) for r in todo))

    # ---- 输出 ----
    to_write = []
    for row, text in results:
        if text is None:
            continue
        n = len(row.tools)
        old = (row.description or '').strip().replace('\n', ' ')
        print(f'== id={row.id} {row.server_title}（{n} 个工具）')
        print(f'  旧 description: {old[:80] or "（无）"}')
        print(f'  新组描述: {text}')
        print()
        to_write.append((row, text))

    if not write:
        print(f'--- dry-run 结束：{len(to_write)} 条结果未写库。确认质量后加 --write ---')
        return

    async with async_db_session.begin() as db:
        for row, text in to_write:
            # 重新加载受管对象后合并 metadata，避免整列覆盖丢数据
            fresh = await db.get(McpServer, row.id)
            meta = dict(fresh.server_metadata or {})
            meta['tool_group_description'] = text
            fresh.server_metadata = meta
    print(f'--- 已写入 {len(to_write)} 条到 server_metadata.tool_group_description ---')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, default=None, help='只处理前 N 个 server')
    parser.add_argument('--write', action='store_true', help='写库（默认 dry-run）')
    args = parser.parse_args()
    asyncio.run(main(args.limit, args.write))
