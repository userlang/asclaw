-- ============================================================
-- 企业入驻模块
-- 表: enterprise (asclaw 库)
-- 说明: 商家提交入驻申请 -> 管理员审核 -> 通过后可登录
--       status: 0=待审核 1=已通过 2=已拒绝
--       user_id: 审核通过后关联的 sys_user.id（企业登录账号统一存用户表）
-- 对应模型: backend/app/enterprise/model/enterprise.py
-- 用法: docker exec -i mysql mysql -uroot -p'<密码见 backend/.env>' \
--         --default-character-set=utf8mb4 asclaw < backend/sql/enterprise.sql
-- 注意: 表结构日常由 alembic 管理，此脚本仅用于手动建表或核对结构
-- ============================================================

CREATE TABLE IF NOT EXISTS `enterprise` (
  `id`            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `name`          VARCHAR(100) NOT NULL COMMENT '企业名称',
  `credit_code`   VARCHAR(64)  NOT NULL COMMENT '统一社会信用代码（营业执照）',
  `legal_person`  VARCHAR(50)           DEFAULT NULL COMMENT '法定代表人',
  `contact_name`  VARCHAR(50)  NOT NULL COMMENT '联系人',
  `contact_phone` VARCHAR(20)  NOT NULL COMMENT '联系电话',
  `contact_email` VARCHAR(100)          DEFAULT NULL COMMENT '联系邮箱',
  `license_url`   VARCHAR(255)          DEFAULT NULL COMMENT '营业执照文件地址',
  `address`       VARCHAR(255)          DEFAULT NULL COMMENT '注册地址',
  `description`   TEXT                  COMMENT '企业简介',
  `username`      VARCHAR(50)  NOT NULL COMMENT '登录用户名',
  `password`      VARCHAR(255) NOT NULL COMMENT '密码哈希（bcrypt）',
  `user_id`       BIGINT                DEFAULT NULL COMMENT '关联用户ID（sys_user）',
  `status`        TINYINT      NOT NULL DEFAULT 0 COMMENT '审核状态（0待审核 1已通过 2已拒绝）',
  `reject_reason` VARCHAR(255)          DEFAULT NULL COMMENT '拒绝原因',
  `reviewed_by`   BIGINT                DEFAULT NULL COMMENT '审核人用户ID',
  `reviewed_time` DATETIME              DEFAULT NULL COMMENT '审核时间',
  `created_time`  DATETIME              DEFAULT NULL COMMENT '创建时间',
  `updated_time`  DATETIME              DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ux_enterprise_username` (`username`),
  KEY `ix_enterprise_status` (`status`),
  KEY `ix_enterprise_user_id` (`user_id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT ='企业入驻申请';
