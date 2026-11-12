-- 管理后台侧边栏菜单种子数据（与前端 /user/admin/* 页面一一对应）
-- Docker 首次初始化时由 /docker-entrypoint-initdb.d 按文件名顺序自动执行：
--   01_create_databases.sql 建库 -> 本脚本建 sys_menu 表并写入菜单
-- （其余业务表由后端启动时的 create_tables 自动补建）
-- 注意：初始化脚本只在数据卷为空的首次启动执行；不要对已有数据的库手动执行（会主键冲突）

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

-- type=0 目录项即侧边栏导航；icon 为 lucide-react 组件名（见 frontend/components/sidebar/admin-sidebar.tsx ICON_MAP）
INSERT INTO `sys_menu`
  (`id`, `title`, `name`, `path`, `sort`, `icon`, `type`, `component`, `perms`, `status`, `display`, `cache`, `remark`, `parent_id`, `created_time`, `updated_time`)
VALUES
  (1, '系统概览', 'dashboard',         '/user/admin',            1, 'LayoutDashboard', 0, NULL, NULL, 1, 1, 1, NULL, NULL, NOW(), NULL),
  (2, 'MCP管理',  'mcp-manage',        '/user/admin/mcp',        2, 'Server',          0, NULL, NULL, 1, 1, 1, NULL, NULL, NOW(), NULL),
  (3, 'Agent管理','agent-manage',      '/user/admin/agent',      3, 'Bot',             0, NULL, NULL, 1, 1, 1, NULL, NULL, NOW(), NULL),
  (4, 'Skill管理','skill-manage',      '/user/admin/skill',      4, 'Zap',             0, NULL, NULL, 1, 1, 1, NULL, NULL, NOW(), NULL),
  (5, '用户管理', 'user-manage',       '/user/admin/user',       5, 'Users',           0, NULL, NULL, 1, 1, 1, NULL, NULL, NOW(), NULL),
  (6, '权限管理', 'permission-manage', '/user/admin/permission', 6, 'Shield',          0, NULL, NULL, 1, 1, 1, NULL, NULL, NOW(), NULL),
  (7, '操作日志', 'log-manage',        '/user/admin/log',        7, 'FileText',        0, NULL, NULL, 1, 1, 1, NULL, NULL, NOW(), NULL),
  (8, '部署日志', 'deploy-log',        '/user/admin/deploy',     8, 'History',         0, NULL, NULL, 1, 1, 1, NULL, NULL, NOW(), NULL),
  (9, '商家审核', 'enterprise-review', '/user/admin/review',     9, 'ClipboardCheck',  0, NULL, NULL, 1, 1, 1, NULL, NULL, NOW(), NULL);
