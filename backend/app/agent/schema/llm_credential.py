# 作者：langjunnan
# 开发时间：2025年7月23日

from __future__ import annotations

from typing import Optional

from common.schema import SchemaBase
from pydantic import field_validator


class LlmCredentialParam(SchemaBase):
    """保存个人/企业共享的模型密钥（BYOK，OpenAI 兼容网关）

    api_key 留空表示沿用已保存的密钥（仅调整网关/模型），首次配置必须填写。
    """

    api_key: str = ''
    # 留空回落平台默认（DashScope 兼容模式）
    base_url: Optional[str] = None
    chat_model: Optional[str] = None
    title_model: Optional[str] = None

    @field_validator('base_url', 'chat_model', 'title_model')
    @classmethod
    def blank_to_none(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            return None
        return v.strip() if v else v

    @field_validator('base_url')
    @classmethod
    def base_url_must_be_http(cls, v: str | None) -> str | None:
        if v is not None and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('网关地址必须以 http:// 或 https:// 开头')
        return v


class LlmCredentialTestParam(SchemaBase):
    """测试连通性：直接用提交的表单值试连，不必先保存"""

    api_key: str
    base_url: Optional[str] = None
    chat_model: Optional[str] = None
