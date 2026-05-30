# WanderNote Photo Agent

家庭电脑照片同步 Agent，负责把本地照片同步成云端可用的照片索引和 COS 图片资源。

## 技术栈

- Python 3.11+
- SQLite
- Pillow（图像处理）
- pillow-heif（HEIC 支持）
- exifread（EXIF 数据读取）
- httpx（HTTP 客户端）
- PyYAML（配置解析）

## 主要职责

- 扫描本地照片目录
- 读取 EXIF 拍摄时间和 GPS
- 生成 thumb（长边 360px）和 preview（长边 1280px）的 WebP 图片
- 批量上传照片索引到后端
- 申请 COS 临时上传 URL
- 直传 thumb/preview 到 COS
- 通知后端上传完成
- 30 秒心跳上报
- 10 分钟增量扫描
- 上传失败重试

## 项目结构

```
photo-agent/
├── pyproject.toml           # Python 项目配置和依赖
├── config.example.yaml      # YAML 配置文件示例
├── .env.example             # 环境变量配置示例
├── .env                     # 基础环境变量配置（不提交）
├── .env.dev                 # 开发环境配置（不提交）
├── .env.prod                # 生产环境配置（不提交）
├── README.md                # 项目说明
├── start.ps1                # 默认环境启动脚本
├── start.bat                # Windows 批处理启动脚本
├── start-dev.ps1            # 开发环境启动脚本
├── start-prod.ps1           # 生产环境启动脚本
├── install-dev.ps1          # 开发环境安装脚本
├── data/                    # SQLite 数据库目录
├── logs/                    # 日志目录
├── agent/
│   ├── __init__.py          # 版本号 0.1.0
│   ├── main.py              # 入口点、CLI、信号处理
│   ├── config.py            # 配置加载
│   ├── database.py          # SQLite 操作
│   ├── scanner.py           # 目录扫描
│   ├── exif_reader.py       # EXIF 提取
│   ├── image_processor.py   # WebP thumb/preview 生成
│   ├── api_client.py        # 后端 API 通信
│   ├── cos_uploader.py      # COS 临时 URL 上传
│   ├── heartbeat.py         # 心跳上报（30s）
│   ├── sync_orchestrator.py # 同步流程编排
│   └── metrics.py           # 轻量指标收集
└── tests/                   # 单元测试
```

## 快速开始

### 1. 安装依赖

```bash
cd photo-agent
pip install -e .
```

### 2. 配置

复制配置文件示例：

```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml`，填写以下必填项：

```yaml
agent_id: home-mac-001          # Agent 唯一标识
server_url: http://localhost:8080  # 后端服务器地址
photo_root: "/path/to/photos"   # 照片根目录
```

设置 Agent Token（二选一）：

**方式一：环境变量（推荐）**

```bash
export AGENT_TOKEN="your-token-here"
```

**方式二：配置文件**

```yaml
agent_token: "your-token-here"
```

### 3. 启动

```bash
# 使用命令行入口
photo-agent

# 或使用 Python 模块
python -m agent.main
```

## 多环境配置

Photo-Agent 支持多环境配置，可以方便地在开发环境和生产环境之间切换。

### 配置文件说明

| 文件 | 说明 | 是否提交 |
|------|------|---------|
| `.env` | 基础配置 | ❌ 被忽略 |
| `.env.dev` | 开发环境配置 | ❌ 被忽略 |
| `.env.prod` | 生产环境配置 | ❌ 被忽略 |
| `.env.example` | 配置示例 | ✅ 已提交 |
| `config.yaml` | YAML 配置 | ❌ 被忽略 |
| `config.example.yaml` | YAML 配置示例 | ✅ 已提交 |

### 配置优先级

```
环境变量 > .env.{AGENT_ENV} > .env > config.yaml > 默认值
```

### 环境切换方式

**方式一：设置环境变量**

```powershell
# Windows PowerShell
$env:AGENT_ENV = "dev"   # 开发环境
$env:AGENT_ENV = "prod"  # 生产环境
python -m agent.main
```

```bash
# Linux/macOS
export AGENT_ENV=dev     # 开发环境
export AGENT_ENV=prod    # 生产环境
python -m agent.main
```

**方式二：使用启动脚本**

```powershell
.\start-dev.ps1    # 开发环境
.\start-prod.ps1   # 生产环境
.\start.ps1        # 默认环境
```

### 使用示例

#### 1. 创建开发环境配置

```bash
# 复制示例文件
cp .env.example .env.dev

# 编辑 .env.dev，填写开发环境配置
# AGENT_ID=dev-mac-001
# SERVER_URL=http://localhost:8080
# AGENT_TOKEN=dev-token-for-testing
# PHOTO_ROOT=./tests/fixtures/photos
# LOG_LEVEL=DEBUG
# SCAN_INTERVAL_MINUTES=1
```

#### 2. 创建生产环境配置

```bash
# 复制示例文件
cp .env.example .env.prod

# 编辑 .env.prod，填写生产环境配置
# AGENT_ID=home-mac-001
# SERVER_URL=https://api.example.com
# AGENT_TOKEN=your-production-token
# PHOTO_ROOT=/Users/xxx/Pictures/旅行照片
# LOG_LEVEL=INFO
# SCAN_INTERVAL_MINUTES=10
```

#### 3. 启动开发环境

```powershell
# 方式一：设置环境变量
$env:AGENT_ENV = "dev"
python -m agent.main

# 方式二：使用启动脚本
.\start-dev.ps1
```

#### 4. 启动生产环境

```powershell
# 方式一：设置环境变量
$env:AGENT_ENV = "prod"
python -m agent.main

# 方式二：使用启动脚本
.\start-prod.ps1
```

### 环境变量列表

| 环境变量 | 说明 | 示例 |
|----------|------|------|
| `AGENT_ENV` | 环境名称 | `dev` / `prod` |
| `AGENT_ID` | Agent 唯一标识 | `home-mac-001` |
| `SERVER_URL` | 后端服务器地址 | `http://localhost:8080` |
| `AGENT_TOKEN` | Agent 认证 token | `your-token-here` |
| `PHOTO_ROOT` | 照片根目录 | `./tests/fixtures/photos` |
| `LOG_LEVEL` | 日志级别 | `DEBUG` / `INFO` |
| `SCAN_INTERVAL_MINUTES` | 扫描间隔（分钟） | `10` |
| `THUMB_LONG_EDGE` | 缩略图长边尺寸 | `360` |
| `PREVIEW_LONG_EDGE` | 预览图长边尺寸 | `1280` |
| `INDEX_BATCH_SIZE` | 索引上传批量大小 | `100` |
| `THUMB_UPLOAD_CONCURRENCY` | 缩略图上传并发数 | `3` |
| `PREVIEW_UPLOAD_CONCURRENCY` | 预览图上传并发数 | `1` |

## 配置说明

### YAML 配置文件

复制 `config.example.yaml` 为 `config.yaml`，填写以下配置：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| agent_id | Agent 唯一标识 | 必填 |
| server_url | 后端服务器地址 | 必填 |
| agent_token | Agent 认证 token | 必填（优先读取环境变量 AGENT_TOKEN） |
| photo_root | 照照片根目录 | 必填 |
| scan_interval_minutes | 增量扫描间隔（分钟） | 10 |
| thumb_long_edge | 缩略图长边尺寸（像素） | 360 |
| preview_long_edge | 预览图长边尺寸（像素） | 1280 |
| index_batch_size | 索引上传批量大小 | 100 |
| thumb_upload_concurrency | 缩略图上传并发数 | 3 |
| preview_upload_concurrency | 预览图上传并发数 | 1 |
| log_level | 日志级别 | INFO |

### 环境变量

环境变量会覆盖 YAML 配置文件中的值。详见"多环境配置"部分。

## SQLite 表结构

### photos 表

```sql
CREATE TABLE photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    local_photo_id TEXT NOT NULL UNIQUE,  -- SHA256(relative_path + file_size + mtime)
    relative_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    mtime REAL NOT NULL,
    content_hash TEXT,                    -- 保留字段，默认不计算
    taken_at TEXT,
    lat REAL,
    lng REAL,
    width INTEGER,
    height INTEGER,
    thumb_path TEXT,
    preview_path TEXT,
    index_sync_status TEXT DEFAULT 'pending',  -- pending/synced/failed
    thumb_sync_status TEXT DEFAULT 'pending',
    preview_sync_status TEXT DEFAULT 'pending',
    server_photo_id TEXT,
    last_error TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### sync_stats 表

```sql
CREATE TABLE sync_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    photo_count INTEGER DEFAULT 0,
    gps_photo_count INTEGER DEFAULT 0,
    thumb_synced_count INTEGER DEFAULT 0,
    preview_synced_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    upload_success_count INTEGER DEFAULT 0,
    upload_failed_count INTEGER DEFAULT 0,
    current_upload_queue_size INTEGER DEFAULT 0,
    last_sync_duration_seconds REAL DEFAULT 0,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## 同步流程

1. **启动**：加载配置 → 初始化数据库 → 全量扫描
2. **扫描**：遍历目录 → 读取 EXIF → 计算 hash → 更新数据库
3. **处理**：为新增/修改照片生成 thumb/preview
4. **上传索引**：批量上传照片元数据到后端
5. **上传图片**：获取 COS URL → 上传 thumb/preview → 通知后端
6. **心跳**：每 30 秒上报状态
7. **增量**：每 10 分钟重复扫描-上传周期
8. **重试**：失败任务在下个周期重试

## 测试照片目录

```bash
# 创建测试目录
mkdir -p tests/fixtures/photos/2025/西藏
mkdir -p tests/fixtures/photos/2025/新疆

# 放入测试照片（jpg/png/heic）
# 运行测试
pytest tests/
```

## 日志

日志文件位置：`logs/agent.log`

- 单文件大小：10MB
- 保留历史文件：5 个
- 日志格式：`%(asctime)s - %(name)s - %(levelname)s - %(message)s`

## 优雅关闭

Agent 支持 SIGINT（Ctrl+C）和 SIGTERM 信号的优雅关闭：

1. 停止接受新任务
2. 等待当前上传完成（超时 30 秒）
3. 保存 SQLite 状态
4. 写入关闭日志
5. 退出

## 后端 API 接口

Agent 使用以下后端接口：

| 接口 | 说明 |
|------|------|
| POST /api/agent/heartbeat | 心跳上报 |
| POST /api/agent/photos/batch | 批量上传照片索引 |
| POST /api/agent/assets/upload-ticket | 申请 COS 上传地址 |
| POST /api/agent/assets/upload-complete | 通知上传完成 |

## 参考文档

- `../docs/decisions/002-photo-agent.md` - Photo-Agent 功能决策记录
- `../docs/decisions/005-api-contract.md` - 后端接口协议草案
- `../docs/decisions/006-external-services-and-secrets.md` - 外部服务与密钥安全
- `../docs/decisions/007-project-architecture.md` - 项目技术架构
- `../docs/decisions/008-mvp-roadmap.md` - MVP 开发路线图

## 注意事项

- 不开放本地端口
- 不调用腾讯地图
- 不调用 MiMo
- 不保存 COS 永久密钥
- 不上传原图
- 不管理路线/地点/文章
- 不删除本地照片
- 不修改本地原图
- 不做复杂桌面 GUI
