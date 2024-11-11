# 作者：langjunnan
# 开发时间：2025年7月23日

from __future__ import annotations

from common.model import Base, id_key
from sqlalchemy import BigInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class LlmUserCredential(Base):
    """用户/商户自己的大模型密钥（BYOK，加密存储）

    聊天与标题生成不再烧平台 key：个人配置（enterprise_id 为空）与企业共享配置
    各自成行，解析时个人优先、企业共享兜底，均未配置则拦截聊天并引导配置。
    api_key 为 AES-CBC 加密后的 hex 字符串；网关地址与模型名留空时回落平台默认。
    """

    __tablename__ = 'llm_user_credential'
    id: Mapped[id_key] = mapped_column(init=False)

    # 配置人（企业凭证时为操作成员，便于审计）
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, comment='配置密钥的用户ID')
    # 加密后的 api_key（hex 字符串）
    api_key: Mapped[str] = mapped_column(Text, comment='加密的模型 API Key')

    # 企业维度共享密钥：为空表示个人密钥；有值表示该企业下所有用户可用
    enterprise_id: Mapped[int | None] = mapped_column(
        BigInteger, default=None, index=True, comment='企业ID（空=个人密钥）'
    )
    # OpenAI 兼容网关地址（如 DashScope compatible-mode），空=平台默认
    base_url: Mapped[str | None] = mapped_column(String(500), default=None, comment='OpenAI 兼容网关地址')
    # 对话模型名，空=平台默认
    chat_model: Mapped[str | None] = mapped_column(String(100), default=None, comment='对话模型名')
    # 标题生成模型名，空=平台默认
    title_model: Mapped[str | None] = mapped_column(String(100), default=None, comment='标题生成模型名')

    # 唯一性：个人（enterprise_id 为空）与企业共享两条互不覆盖；
    # MySQL 唯一索引对 NULL 不去重，定位行时显式用 enterprise_id IS NULL 过滤
    __table_args__ = (
        UniqueConstraint('user_id', 'enterprise_id', name='uix_user_llm_credential'),
    )
