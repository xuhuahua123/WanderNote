-- WanderNote Backend Database Schema
-- Version: 0.1.0
-- Date: 2026-05-29

-- 创建数据库
CREATE DATABASE IF NOT EXISTS wandernote DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE wandernote;

-- 访问会话表
CREATE TABLE IF NOT EXISTS access_session (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    token_hash VARCHAR(64) NOT NULL COMMENT 'Token 哈希值',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    expires_at DATETIME NOT NULL COMMENT '过期时间',
    last_seen_at DATETIME COMMENT '最后活跃时间',
    revoked_at DATETIME COMMENT '撤销时间',
    user_agent VARCHAR(512) COMMENT '用户代理',
    client_ip VARCHAR(64) COMMENT '客户端 IP',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_token_hash (token_hash),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='访问会话表';

-- Agent 状态表
CREATE TABLE IF NOT EXISTS agent (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    agent_id VARCHAR(128) NOT NULL COMMENT 'Agent 唯一标识',
    name VARCHAR(256) COMMENT 'Agent 名称',
    version VARCHAR(64) COMMENT 'Agent 版本',
    status VARCHAR(32) DEFAULT 'idle' COMMENT '状态: idle, scanning, syncing',
    last_heartbeat_at DATETIME COMMENT '最近心跳时间',
    last_scan_at DATETIME COMMENT '最近扫描时间',
    last_sync_at DATETIME COMMENT '最近同步时间',
    photo_count INT DEFAULT 0 COMMENT '照片总数',
    gps_photo_count INT DEFAULT 0 COMMENT '有 GPS 的照片数量',
    thumb_synced_count INT DEFAULT 0 COMMENT '缩略图已同步数量',
    preview_synced_count INT DEFAULT 0 COMMENT '预览图已同步数量',
    failed_count INT DEFAULT 0 COMMENT '失败数量',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_agent_id (agent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent 状态表';

-- 行政区划表
CREATE TABLE IF NOT EXISTS district (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    adcode VARCHAR(16) NOT NULL COMMENT '行政区划代码',
    name VARCHAR(128) NOT NULL COMMENT '名称',
    full_name VARCHAR(256) COMMENT '全称',
    level VARCHAR(32) NOT NULL COMMENT '级别: province, city, district',
    parent_adcode VARCHAR(16) COMMENT '父级 adcode',
    province_adcode VARCHAR(16) COMMENT '所属省份 adcode',
    province_name VARCHAR(128) COMMENT '所属省份名称',
    city_adcode VARCHAR(16) COMMENT '所属城市 adcode',
    city_name VARCHAR(128) COMMENT '所属城市名称',
    lat DECIMAL(10, 6) COMMENT '纬度',
    lng DECIMAL(10, 6) COMMENT '经度',
    source VARCHAR(32) DEFAULT 'tencent' COMMENT '数据来源',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE INDEX idx_adcode (adcode),
    INDEX idx_level (level),
    INDEX idx_province_adcode (province_adcode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='行政区划表';

-- POI 缓存表
CREATE TABLE IF NOT EXISTS poi_cache (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    keyword VARCHAR(256) NOT NULL COMMENT '关键词',
    region_adcode VARCHAR(16) COMMENT '区域 adcode',
    region_name VARCHAR(128) COMMENT '区域名称',
    provider VARCHAR(32) DEFAULT 'tencent' COMMENT '数据来源',
    provider_poi_id VARCHAR(128) COMMENT 'POI ID',
    title VARCHAR(256) COMMENT '标题',
    address VARCHAR(512) COMMENT '地址',
    category VARCHAR(256) COMMENT '分类',
    province_name VARCHAR(128) COMMENT '省份名称',
    city_name VARCHAR(128) COMMENT '城市名称',
    district_name VARCHAR(128) COMMENT '区县名称',
    lat DECIMAL(10, 6) COMMENT '纬度',
    lng DECIMAL(10, 6) COMMENT '经度',
    raw_json TEXT COMMENT '原始 JSON',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_keyword_region (keyword, region_adcode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='POI 缓存表';

-- 照片索引主表
CREATE TABLE IF NOT EXISTS photo (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    agent_id VARCHAR(128) NOT NULL COMMENT '所属 Agent ID',
    local_photo_id VARCHAR(128) NOT NULL COMMENT '本地照片 ID',
    relative_path VARCHAR(512) COMMENT '相对路径',
    file_name VARCHAR(256) COMMENT '文件名',
    file_size BIGINT COMMENT '文件大小（字节）',
    content_hash VARCHAR(128) COMMENT '内容哈希',
    mtime DATETIME COMMENT '文件修改时间',
    taken_at DATETIME COMMENT '拍摄时间',
    lat DECIMAL(10, 6) COMMENT '纬度',
    lng DECIMAL(10, 6) COMMENT '经度',
    width INT COMMENT '宽度',
    height INT COMMENT '高度',
    has_gps TINYINT(1) DEFAULT 0 COMMENT '是否有 GPS 信息',
    sync_status VARCHAR(32) DEFAULT 'indexed' COMMENT '同步状态',
    last_error VARCHAR(512) COMMENT '最近错误信息',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_agent_local (agent_id, local_photo_id),
    INDEX idx_taken_at (taken_at),
    INDEX idx_lat_lng (lat, lng),
    INDEX idx_has_gps (has_gps)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='照片索引主表';

-- 照片派生资源表
CREATE TABLE IF NOT EXISTS photo_asset (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    photo_id BIGINT NOT NULL COMMENT '关联的照片 ID',
    asset_type VARCHAR(32) NOT NULL COMMENT '资源类型: thumb, preview',
    storage_provider VARCHAR(32) DEFAULT 'cos' COMMENT '存储提供商标识',
    bucket VARCHAR(128) COMMENT '存储桶',
    region VARCHAR(64) COMMENT '存储区域',
    storage_key VARCHAR(512) COMMENT '存储键（路径）',
    width INT COMMENT '宽度',
    height INT COMMENT '高度',
    file_size BIGINT COMMENT '文件大小',
    sync_status VARCHAR(32) DEFAULT 'pending' COMMENT '同步状态',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_photo_asset (photo_id, asset_type),
    INDEX idx_sync_status (sync_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='照片派生资源表';

-- 路线表
CREATE TABLE IF NOT EXISTS route (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(256) NOT NULL COMMENT '路线名称',
    year INT COMMENT '年份',
    cover_photo_id BIGINT COMMENT '封面照片 ID',
    summary VARCHAR(512) COMMENT '摘要',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_year (year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='路线表';

-- 路线城市表
CREATE TABLE IF NOT EXISTS route_city (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    route_id BIGINT NOT NULL COMMENT '路线 ID',
    city_adcode VARCHAR(16) NOT NULL COMMENT '城市 adcode',
    city_name VARCHAR(128) NOT NULL COMMENT '城市名称',
    province_adcode VARCHAR(16) COMMENT '省份 adcode',
    province_name VARCHAR(128) COMMENT '省份名称',
    sort_order INT DEFAULT 0 COMMENT '排序',
    note VARCHAR(512) COMMENT '备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_route_id (route_id),
    INDEX idx_sort_order (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='路线城市表';

-- 路线地点表
CREATE TABLE IF NOT EXISTS route_place (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    route_city_id BIGINT NOT NULL COMMENT '路线城市 ID',
    name VARCHAR(256) NOT NULL COMMENT '地点名称',
    source_type VARCHAR(32) DEFAULT 'custom' COMMENT '来源类型: custom, tencent_poi',
    tencent_poi_id VARCHAR(128) COMMENT '腾讯 POI ID',
    resolved_title VARCHAR(256) COMMENT '解析后的标题',
    resolved_address VARCHAR(512) COMMENT '解析后的地址',
    category VARCHAR(256) COMMENT '分类',
    lat DECIMAL(10, 6) COMMENT '纬度',
    lng DECIMAL(10, 6) COMMENT '经度',
    match_status VARCHAR(32) DEFAULT 'pending' COMMENT '匹配状态: matched, unmatched, pending',
    match_photo_count INT DEFAULT 0 COMMENT '匹配照片数量',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_route_city_id (route_city_id),
    INDEX idx_lat_lng (lat, lng)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='路线地点表';

-- 地点照片绑定表
CREATE TABLE IF NOT EXISTS route_place_photo (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    route_place_id BIGINT NOT NULL COMMENT '地点 ID',
    photo_id BIGINT NOT NULL COMMENT '照片 ID',
    match_source VARCHAR(32) DEFAULT 'gps_auto' COMMENT '匹配来源: gps_auto, manual, system_recommend',
    distance_meters DECIMAL(10, 2) COMMENT '距离（米）',
    score DECIMAL(5, 2) COMMENT '匹配分数',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_place_photo (route_place_id, photo_id),
    INDEX idx_photo_id (photo_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='地点照片绑定表';

-- 文章草稿表
CREATE TABLE IF NOT EXISTS article_draft (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    target_type VARCHAR(32) NOT NULL COMMENT '目标类型: route, place',
    target_id BIGINT NOT NULL COMMENT '目标 ID',
    title VARCHAR(256) COMMENT '标题',
    content TEXT COMMENT '正文',
    image_captions_json TEXT COMMENT '图片说明 JSON',
    selected_photo_ids_json TEXT COMMENT '选中照片 ID JSON',
    mood VARCHAR(128) COMMENT '情绪',
    user_note TEXT COMMENT '用户备注',
    status VARCHAR(32) DEFAULT 'draft' COMMENT '状态',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_target (target_type, target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文章草稿表';

-- AI 生成日志表
CREATE TABLE IF NOT EXISTS article_generation_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    target_type VARCHAR(32) NOT NULL COMMENT '目标类型',
    target_id BIGINT NOT NULL COMMENT '目标 ID',
    action_type VARCHAR(32) NOT NULL COMMENT '动作类型: generate, regenerate, make_plainer, make_more_emotional',
    model_provider VARCHAR(64) COMMENT '模型供应商',
    model_name VARCHAR(128) COMMENT '模型名称',
    request_json TEXT COMMENT '请求 JSON',
    response_json TEXT COMMENT '响应 JSON',
    input_token_count INT COMMENT '输入 token 数',
    output_token_count INT COMMENT '输出 token 数',
    cost_amount DECIMAL(10, 4) COMMENT '成本',
    success TINYINT(1) DEFAULT 1 COMMENT '是否成功',
    error_message VARCHAR(1024) COMMENT '错误信息',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_target (target_type, target_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI 生成日志表';
