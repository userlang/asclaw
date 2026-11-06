-- 创建业务库与聊天记录库（Docker 首次初始化时自动执行）
CREATE DATABASE IF NOT EXISTS `asclaw` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS `asclaw_chat` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
