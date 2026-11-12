-- 增量脚本：skill / agent 企业隔离 —— 给 agent_skill、agent_server 增加 enterprise_id
-- 说明：发布时按作者关联的已审核企业落定；空 = 无企业归属的个人数据。
--       可见性规则：公开（is_public=1）所有人可见；私有仅作者本人 + 同企业成员可见。
-- 对应 alembic 迁移：2026-11-12-14_06_44-9dbf4cf40281_add_enterprise_id_to_agent_skill_and_.py
--
-- 执行方式（见 README.md）：
--   docker exec -i mysql mysql -uroot -p'<密码见 backend/.env>' \
--     --default-character-set=utf8mb4 asclaw < backend/sql/2026-11-12_agent_skill_agent_server_add_enterprise_id.sql
--
-- 幂等：已存在该列时跳过（MySQL 8 不支持 ADD COLUMN IF NOT EXISTS，用存储过程判断）

USE `asclaw`;

-- agent_server
SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = 'asclaw'
    AND TABLE_NAME = 'agent_server'
    AND COLUMN_NAME = 'enterprise_id'
);
SET @ddl = IF(
  @col_exists = 0,
  'ALTER TABLE `agent_server` ADD COLUMN `enterprise_id` bigint DEFAULT NULL COMMENT ''企业关联ID''',
  'SELECT ''agent_server.enterprise_id 已存在，跳过'''
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- agent_server 索引
SET @idx_exists = (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = 'asclaw'
    AND TABLE_NAME = 'agent_server'
    AND INDEX_NAME = 'ix_agent_server_enterprise_id'
);
SET @ddl = IF(
  @idx_exists = 0,
  'ALTER TABLE `agent_server` ADD KEY `ix_agent_server_enterprise_id` (`enterprise_id`)',
  'SELECT ''agent_server 索引已存在，跳过'''
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- agent_skill
SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = 'asclaw'
    AND TABLE_NAME = 'agent_skill'
    AND COLUMN_NAME = 'enterprise_id'
);
SET @ddl = IF(
  @col_exists = 0,
  'ALTER TABLE `agent_skill` ADD COLUMN `enterprise_id` bigint DEFAULT NULL COMMENT ''企业关联ID''',
  'SELECT ''agent_skill.enterprise_id 已存在，跳过'''
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- agent_skill 索引
SET @idx_exists = (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = 'asclaw'
    AND TABLE_NAME = 'agent_skill'
    AND INDEX_NAME = 'ix_agent_skill_enterprise_id'
);
SET @ddl = IF(
  @idx_exists = 0,
  'ALTER TABLE `agent_skill` ADD KEY `ix_agent_skill_enterprise_id` (`enterprise_id`)',
  'SELECT ''agent_skill 索引已存在，跳过'''
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
