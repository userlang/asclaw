# 作者：langjunnan
# 开发时间：2025年7月23日

from openai import AsyncOpenAI


async def call_model(query: str, *, api_key: str, base_url: str, model: str):
    """轻量模型调用（聊天标题生成等），密钥/网关由调用方解析传入（BYOK）"""
    client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=30)
    try:
        # enable_thinking 仅百炼 qwen 系认识，透传给其他网关可能报未知参数
        extra = {'extra_body': {'enable_thinking': False}} if model.lower().startswith('qwen') else {}
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'user', 'content': f'用10字以内总结以下问题的主题，只返回标题文本，不要加引号和标点：{query}'}
            ],
            **extra,
        )
        return response.choices[0].message.content
    finally:
        await client.close()
