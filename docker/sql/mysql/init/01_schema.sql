-- ============================================================================
-- AsClaw 数据库初始化脚本 01_schema.sql
-- 职责：创建数据库 + 全部表结构（幂等，可重复执行，不删除任何数据）
-- 初始化数据请执行 02_data.sql
--
-- 执行方式：
--   1) 全新数据卷：docker compose 首次启动时自动按文件名顺序执行
--   2) 已有数据卷：docker exec -i mysql mysql -uroot -p'<密码>' \
--        --default-character-set=utf8mb4 < docker/sql/mysql/init/01_schema.sql
-- ============================================================================

SET NAMES utf8mb4;

-- ----------------------------------------------------------------------------
-- 1. 业务库 asclaw
-- ----------------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS `asclaw` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `asclaw`;

--
-- Table structure for table `agent_category`
--

CREATE TABLE IF NOT EXISTS `agent_category` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `name` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '类目名称',
  `is_recommend` tinyint(1) NOT NULL COMMENT '是否推荐类目',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `ix_agent_category_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='agent category';

--
-- Table structure for table `agent_chat`
--

CREATE TABLE IF NOT EXISTS `agent_chat` (
  `thread_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `first_query` text COLLATE utf8mb4_unicode_ci,
  `start_time` datetime NOT NULL,
  `end_time` datetime DEFAULT NULL,
  `chat_title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title_generated` tinyint(1) NOT NULL,
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`thread_id`),
  KEY `ix_agent_chat_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Table structure for table `agent_server`
--

CREATE TABLE IF NOT EXISTS `agent_server` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'agent name',
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'agent name',
  `avatar` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'agent avatar',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT 'agent描述',
  `system_prompt` text COLLATE utf8mb4_unicode_ci COMMENT '系统提示词',
  `prologue` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '开场白',
  `tools` json DEFAULT NULL COMMENT '工具列表',
  `knowledge` json DEFAULT NULL COMMENT '知识库列表',
  `databases` json DEFAULT NULL COMMENT '数据库列表',
  `skills` json DEFAULT NULL COMMENT 'skills列表',
  `enable_search` tinyint(1) DEFAULT NULL COMMENT '是否开启联网搜索',
  `enable_multimodal` tinyint(1) DEFAULT NULL COMMENT '是否多模态',
  `enable_suggest` tinyint(1) DEFAULT NULL COMMENT '问题建议',
  `is_public` tinyint(1) DEFAULT NULL COMMENT '是否公开',
  `category_id` bigint DEFAULT NULL COMMENT 'agent 分类ID',
  `user_id` bigint DEFAULT NULL COMMENT '用户关联ID',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime DEFAULT NULL COMMENT '更新时间',
  `mcps` json DEFAULT NULL COMMENT '绑定的 MCP 服务器列表 ["owner/name", ...]',
  `enterprise_id` bigint DEFAULT NULL COMMENT '企业关联ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_agent_server_id` (`id`),
  KEY `ix_agent_server_category_id` (`category_id`),
  KEY `ix_agent_server_user_id` (`user_id`),
  KEY `ix_agent_server_enterprise_id` (`enterprise_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='agent server';

--
-- Table structure for table `agent_skill`
--

CREATE TABLE IF NOT EXISTS `agent_skill` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'skill name',
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'skill title',
  `avatar` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'agent avatar',
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'skill description',
  `repository` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'agent repository',
  `path` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'skill path',
  `is_public` tinyint(1) DEFAULT NULL COMMENT '是否公开',
  `category_id` bigint DEFAULT NULL COMMENT 'skill 分类ID',
  `user_id` bigint DEFAULT NULL COMMENT '用户关联ID',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime DEFAULT NULL COMMENT '更新时间',
  `body` text COLLATE utf8mb4_unicode_ci COMMENT 'SKILL.md 正文（Markdown）',
  `source_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '导入来源 URL',
  `install_count` int NOT NULL DEFAULT '0' COMMENT '安装/使用次数',
  `status` smallint NOT NULL DEFAULT '1' COMMENT '0待审核 1已发布 2已下架',
  `enterprise_id` bigint DEFAULT NULL COMMENT '企业关联ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_agent_skill_id` (`id`),
  KEY `ix_agent_skill_category_id` (`category_id`),
  KEY `ix_agent_skill_user_id` (`user_id`),
  KEY `ix_agent_skill_enterprise_id` (`enterprise_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='agent server';

--
-- Table structure for table `alembic_version`
--

CREATE TABLE IF NOT EXISTS `alembic_version` (
  `version_num` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Table structure for table `deploy_log`
--

CREATE TABLE IF NOT EXISTS `deploy_log` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `task_id` varchar(155) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Celery 任务 ID',
  `task_status` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务状态',
  `task_result` text COLLATE utf8mb4_unicode_ci COMMENT '任务结果',
  `traceback` text COLLATE utf8mb4_unicode_ci COMMENT '错误回溯',
  `user_id` bigint DEFAULT NULL COMMENT '用户 ID',
  `server_title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'MCP Server 名称',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_deploy_log_id` (`id`),
  UNIQUE KEY `ix_deploy_log_task_id` (`task_id`),
  KEY `ix_deploy_log_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部署日志表';

--
-- Table structure for table `enterprise`
--

CREATE TABLE IF NOT EXISTS `enterprise` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '企业名称',
  `credit_code` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '统一社会信用代码（营业执照）',
  `contact_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '联系人',
  `contact_phone` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '联系电话',
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '登录用户名',
  `password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码哈希（bcrypt）',
  `user_id` bigint DEFAULT NULL COMMENT '关联用户ID（sys_user）',
  `legal_person` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '法定代表人',
  `contact_email` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '联系邮箱',
  `license_url` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '营业执照文件地址',
  `address` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '注册地址',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '企业简介',
  `status` int NOT NULL COMMENT '审核状态（0待审核 1已通过 2已拒绝）',
  `reject_reason` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '拒绝原因',
  `reviewed_by` bigint DEFAULT NULL COMMENT '审核人用户ID',
  `reviewed_time` datetime DEFAULT NULL COMMENT '审核时间',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_enterprise_id` (`id`),
  UNIQUE KEY `ix_enterprise_username` (`username`),
  KEY `ix_enterprise_status` (`status`),
  KEY `ix_enterprise_user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='企业入驻申请';

--
-- Table structure for table `llm_user_credential`
--

CREATE TABLE IF NOT EXISTS `llm_user_credential` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `user_id` bigint NOT NULL COMMENT '配置密钥的用户ID',
  `api_key` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '加密的模型 API Key',
  `enterprise_id` bigint DEFAULT NULL COMMENT '企业ID（空=个人密钥）',
  `base_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'OpenAI 兼容网关地址',
  `chat_model` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '对话模型名',
  `title_model` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '标题生成模型名',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_llm_user_credential_id` (`id`),
  UNIQUE KEY `uix_user_llm_credential` (`user_id`,`enterprise_id`),
  KEY `ix_llm_user_credential_enterprise_id` (`enterprise_id`),
  KEY `ix_llm_user_credential_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Table structure for table `mcp_category`
--

CREATE TABLE IF NOT EXISTS `mcp_category` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `name` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '类目名称',
  `is_recommend` int NOT NULL COMMENT '是否推荐类目',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `ix_mcp_category_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='mcp category';

--
-- Table structure for table `mcp_server`
--

CREATE TABLE IF NOT EXISTS `mcp_server` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `server_title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'mcp server title',
  `server_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'mcp server name',
  `transport` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'streamable-http、sse、stdio',
  `server_type` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'hosted、local',
  `compile_type` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '编译类型',
  `server_config` json DEFAULT NULL COMMENT 'server config',
  `envs` json DEFAULT NULL COMMENT '环境变量',
  `git` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '项目地址',
  `readme` text COLLATE utf8mb4_unicode_ci COMMENT '项目介绍',
  `avatar` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '项目头像',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '项目描述',
  `server_metadata` json DEFAULT NULL COMMENT 'mcp server config',
  `tools` json DEFAULT NULL COMMENT '工具列表',
  `prompts` json DEFAULT NULL COMMENT '提示词列表',
  `resources` json DEFAULT NULL COMMENT '资源列表',
  `is_public` tinyint(1) NOT NULL COMMENT '是否公开',
  `is_recommend` tinyint(1) NOT NULL COMMENT '是否推荐',
  `category_id` bigint DEFAULT NULL COMMENT 'MCP 分类ID',
  `user_id` bigint DEFAULT NULL COMMENT '用户关联ID',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime DEFAULT NULL COMMENT '更新时间',
  `cover` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '封面图',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_mcp_server_id` (`id`),
  UNIQUE KEY `uix_user_server_name` (`user_id`,`server_name`),
  KEY `ix_mcp_server_category_id` (`category_id`),
  KEY `ix_mcp_server_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Table structure for table `mcp_user_credential`
--

CREATE TABLE IF NOT EXISTS `mcp_user_credential` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `user_id` bigint NOT NULL COMMENT '配置凭证的用户ID',
  `mcp_server_id` bigint NOT NULL COMMENT 'MCP 服务器ID',
  `credential` text COLLATE utf8mb4_unicode_ci COMMENT '加密的用户凭证',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime DEFAULT NULL COMMENT '更新时间',
  `enterprise_id` bigint DEFAULT NULL COMMENT '企业ID（空=个人凭证）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_mcp_user_credential_id` (`id`),
  UNIQUE KEY `uix_user_mcp_credential` (`user_id`,`mcp_server_id`,`enterprise_id`),
  KEY `ix_mcp_user_credential_mcp_server_id` (`mcp_server_id`),
  KEY `ix_mcp_user_credential_user_id` (`user_id`),
  KEY `ix_mcp_user_credential_enterprise_id` (`enterprise_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Table structure for table `skill_category`
--

CREATE TABLE IF NOT EXISTS `skill_category` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `name` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '类目名称',
  `is_recommend` tinyint(1) NOT NULL COMMENT '是否推荐类目',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `ix_skill_category_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='skill category';

--
-- Table structure for table `skill_content`
--

CREATE TABLE IF NOT EXISTS `skill_content` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `skill_id` bigint NOT NULL COMMENT '关联 agent_skill.id',
  `file_path` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '相对路径，如 SKILL.md / scripts/run.py',
  `content` text COLLATE utf8mb4_unicode_ci COMMENT '文件文本内容',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_skill_content_skill_path` (`skill_id`,`file_path`),
  KEY `ix_skill_content_skill_id` (`skill_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Table structure for table `sys_login_log`
--

CREATE TABLE IF NOT EXISTS `sys_login_log` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `user_uuid` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户UUID',
  `username` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户名',
  `status` int NOT NULL COMMENT '登录状态(0失败 1成功)',
  `ip` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '登录IP地址',
  `country` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '国家',
  `region` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '地区',
  `city` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '城市',
  `user_agent` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '请求头',
  `os` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '操作系统',
  `browser` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '浏览器',
  `device` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '设备',
  `msg` longtext COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '提示消息',
  `login_time` datetime NOT NULL COMMENT '登录时间',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_sys_login_log_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='登录日志表';

--
-- Table structure for table `sys_menu`
--

CREATE TABLE IF NOT EXISTS `sys_menu` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `title` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '菜单标题',
  `name` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '菜单名称',
  `path` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '路由地址',
  `sort` int NOT NULL COMMENT '排序',
  `icon` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '菜单图标',
  `type` int NOT NULL COMMENT '菜单类型（0目录 1菜单 2按钮）',
  `component` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '组件路径',
  `perms` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '权限标识',
  `status` int NOT NULL COMMENT '菜单状态（0停用 1正常）',
  `display` int NOT NULL COMMENT '是否显示（0否 1是）',
  `cache` int NOT NULL COMMENT '是否缓存（0否 1是）',
  `remark` longtext COLLATE utf8mb4_unicode_ci COMMENT '备注',
  `parent_id` bigint DEFAULT NULL COMMENT '父菜单ID',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_sys_menu_id` (`id`),
  KEY `ix_sys_menu_parent_id` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='菜单表';

--
-- Table structure for table `sys_opera_log`
--

CREATE TABLE IF NOT EXISTS `sys_opera_log` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `trace_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '请求跟踪 ID',
  `username` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户名',
  `method` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '请求类型',
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作模块',
  `path` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '请求路径',
  `ip` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'IP地址',
  `country` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '国家',
  `region` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '地区',
  `city` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '城市',
  `user_agent` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '请求头',
  `os` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '操作系统',
  `browser` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '浏览器',
  `device` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '设备',
  `args` json DEFAULT NULL COMMENT '请求参数',
  `status` int NOT NULL COMMENT '操作状态（0异常 1正常）',
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作状态码',
  `msg` longtext COLLATE utf8mb4_unicode_ci COMMENT '提示消息',
  `cost_time` float NOT NULL COMMENT '请求耗时（ms）',
  `opera_time` datetime NOT NULL COMMENT '操作时间',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_sys_opera_log_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

--
-- Table structure for table `sys_role`
--

CREATE TABLE IF NOT EXISTS `sys_role` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `name` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '角色名称',
  `status` int NOT NULL COMMENT '角色状态（0停用 1正常）',
  `remark` longtext COLLATE utf8mb4_unicode_ci COMMENT '备注',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `ix_sys_role_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';

--
-- Table structure for table `sys_role_menu`
--

CREATE TABLE IF NOT EXISTS `sys_role_menu` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `role_id` bigint NOT NULL COMMENT '角色ID',
  `menu_id` bigint NOT NULL COMMENT '菜单ID',
  PRIMARY KEY (`id`,`role_id`,`menu_id`),
  UNIQUE KEY `ix_sys_role_menu_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Table structure for table `sys_user`
--

CREATE TABLE IF NOT EXISTS `sys_user` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `uuid` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `username` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户名',
  `nickname` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '昵称',
  `password` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '密码',
  `salt` varbinary(255) DEFAULT NULL COMMENT '加密盐',
  `email` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '邮箱',
  `phone` varchar(11) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '手机号',
  `avatar` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '头像',
  `status` int NOT NULL COMMENT '用户账号状态(0停用 1正常)',
  `is_superuser` tinyint(1) NOT NULL COMMENT '超级权限(0否 1是)',
  `is_staff` tinyint(1) NOT NULL COMMENT '后台管理登陆(0否 1是)',
  `join_time` datetime NOT NULL COMMENT '注册时间',
  `last_login_time` datetime DEFAULT NULL COMMENT '上次登录时间',
  `last_password_changed_time` datetime DEFAULT NULL COMMENT '上次密码变更时间',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  UNIQUE KEY `ix_sys_user_id` (`id`),
  UNIQUE KEY `ix_sys_user_username` (`username`),
  UNIQUE KEY `ix_sys_user_email` (`email`),
  KEY `ix_sys_user_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

--
-- Table structure for table `sys_user_role`
--

CREATE TABLE IF NOT EXISTS `sys_user_role` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `role_id` bigint NOT NULL COMMENT '角色ID',
  PRIMARY KEY (`id`,`user_id`,`role_id`),
  UNIQUE KEY `ix_sys_user_role_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Table structure for table `task_result`
--

CREATE TABLE IF NOT EXISTS `task_result` (
  `id` int NOT NULL AUTO_INCREMENT,
  `task_id` varchar(155) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `result` blob,
  `date_done` datetime DEFAULT NULL,
  `traceback` text COLLATE utf8mb4_unicode_ci,
  `name` varchar(155) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `args` blob,
  `kwargs` blob,
  `worker` varchar(155) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `retries` int DEFAULT NULL,
  `queue` varchar(155) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`)
) ENGINE=InnoDB AUTO_INCREMENT=97 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务结果表';

--
-- Table structure for table `task_scheduler`
--

CREATE TABLE IF NOT EXISTS `task_scheduler` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务名称',
  `task` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '要运行的 Celery 任务',
  `args` json DEFAULT NULL COMMENT '任务可接收的位置参数',
  `kwargs` json DEFAULT NULL COMMENT '任务可接收的关键字参数',
  `queue` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'CELERY_TASK_QUEUES 中定义的队列',
  `exchange` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '低级别 AMQP 路由的交换机',
  `routing_key` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '低级别 AMQP 路由的路由密钥',
  `start_time` datetime DEFAULT NULL COMMENT '任务开始触发的时间',
  `expire_time` datetime DEFAULT NULL COMMENT '任务不再触发的截止时间',
  `expire_seconds` int DEFAULT NULL COMMENT '任务不再触发的秒数时间差',
  `type` int NOT NULL COMMENT '调度类型（0间隔 1定时）',
  `interval_every` int DEFAULT NULL COMMENT '任务再次运行前的间隔周期数',
  `interval_period` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '任务运行之间的周期类型',
  `crontab` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '任务运行的 Crontab 计划',
  `one_off` tinyint(1) NOT NULL COMMENT '是否仅运行一次',
  `enabled` tinyint(1) NOT NULL COMMENT '是否启用任务',
  `total_run_count` int NOT NULL COMMENT '任务触发的总次数',
  `last_run_time` datetime DEFAULT NULL COMMENT '任务最后触发的时间',
  `remark` longtext COLLATE utf8mb4_unicode_ci COMMENT '备注',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `ix_task_scheduler_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务调度表';

--
-- Table structure for table `task_set_result`
--

CREATE TABLE IF NOT EXISTS `task_set_result` (
  `id` int NOT NULL AUTO_INCREMENT,
  `taskset_id` varchar(155) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `result` blob,
  `date_done` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `taskset_id` (`taskset_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务集结果表';

-- ----------------------------------------------------------------------------
-- 2. alembic 迁移版本标记（与 backend/alembic/versions 最新版本保持一致）
--    快速开始不再执行 alembic upgrade head，这里直接写入最新版本号；
--    后续日常增量开发仍可用 alembic revision --autogenerate / upgrade head
-- ----------------------------------------------------------------------------
INSERT IGNORE INTO `alembic_version` (`version_num`) VALUES ('9dbf4cf40281');

-- ----------------------------------------------------------------------------
-- 3. 聊天记录库 asclaw_chat（agent 会话记忆，agentscope 使用）
-- ----------------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS `asclaw_chat` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `asclaw_chat`;

-- Table structure for table `users`
CREATE TABLE IF NOT EXISTS `users` (
  `id` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for table `session`
CREATE TABLE IF NOT EXISTS `session` (
  `id` varchar(255) NOT NULL,
  `user_id` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `session_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for table `message`
CREATE TABLE IF NOT EXISTS `message` (
  `id` varchar(255) NOT NULL,
  `msg` json NOT NULL,
  `session_id` varchar(255) NOT NULL,
  `index` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `session_id` (`session_id`),
  KEY `ix_message_index` (`index`),
  CONSTRAINT `message_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `session` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for table `message_mark`
CREATE TABLE IF NOT EXISTS `message_mark` (
  `msg_id` varchar(255) NOT NULL,
  `mark` varchar(255) NOT NULL,
  PRIMARY KEY (`msg_id`,`mark`),
  CONSTRAINT `message_mark_ibfk_1` FOREIGN KEY (`msg_id`) REFERENCES `message` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
