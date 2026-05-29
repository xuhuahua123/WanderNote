# 007. 项目技术架构与目录规划

## 状态

已确认。

## 背景

当前已经确认：

- 前端 MVP 功能
- Photo-Agent 边界
- 后端数据模型
- AI 写作服务
- 后端接口协议
- 外部服务和密钥安全

下一步进入工程实现前，需要先确定项目目录、技术栈、配置方式和部署方式，避免代码开始后结构混乱。

## 总体架构

```text
H5 前端
  -> 云端后端
      -> MySQL
      -> Redis
      -> 腾讯地图 WebService
      -> 腾讯 COS
      -> MiMo-V2.5

Photo-Agent
  -> 云端后端
  -> 腾讯 COS 临时上传 URL
```

核心原则：

- H5 只调用云端后端。
- Photo-Agent 只调用云端后端和后端签发的 COS 临时上传 URL。
- 前端不保存外部服务密钥。
- Photo-Agent 不保存腾讯地图、COS、MiMo 密钥。
- 云端后端负责外部服务调用、签名、鉴权和业务规则。

## 推荐目录结构

项目根目录：

```text
WanderNote/
  docs/
    decisions/
      001-frontend-mvp.md
      002-photo-agent.md
      003-backend-data-model.md
      004-ai-writing-service.md
      005-api-contract.md
      006-external-services-and-secrets.md
      007-project-architecture.md

  frontend/
    README.md
    package.json
    src/

  backend/
    README.md
    pom.xml
    src/

  photo-agent/
    README.md
    pyproject.toml
    agent/

  deploy/
    README.md
    nginx/
    systemd/
    env/

  scripts/
    README.md
```

说明：

- `docs/decisions/` 保存产品和技术决策记录。
- `frontend/` 保存 H5 前端。
- `backend/` 保存 Spring Boot 后端。
- `photo-agent/` 保存家庭电脑上的 Python Agent。
- `deploy/` 保存部署相关配置模板。
- `scripts/` 保存开发或维护脚本。

不允许把临时文件、测试图片、生成产物散落在项目根目录。

UI 原型图继续放：

```text
UI原型图/
```

如果后续要规范化，可改名为：

```text
design/prototypes/
```

但当前不强制调整，避免打断已有资料。

## 前端技术栈

推荐：

```text
Vue 3
Vite
TypeScript
Vant UI
Pinia
Axios
```

原因：

- 移动端 H5 适配成熟。
- Vant 组件适合手机端。
- Vue 3 开发效率高。
- 项目规模不大，维护成本低。

前端重点：

- 大字体
- 大按钮
- 简洁页面
- 清晰文案
- 图片网格性能
- 自动保存状态提示
- 图片签名 URL 过期后的刷新机制

前端不做：

- 复杂后台管理
- 富文本排版器
- 地图轨迹
- 多用户权限
- 公众号自动发布

## 后端技术栈

推荐：

```text
Java 21 或 Java 17
Spring Boot
Spring Web
Spring Validation
Spring Security 轻量配置
MyBatis-Plus 或 Spring Data JPA
MySQL
Redis
腾讯 COS Java SDK
HTTP Client
```

说明：

- Spring Boot 负责业务 API。
- MySQL 保存业务数据。
- Redis 保存 Agent 在线状态、短期缓存和限流状态。
- 腾讯 COS SDK 用于生成签名上传/下载 URL。
- 腾讯地图和 MiMo 使用后端 HTTP Client 调用。

后端部署在 2C2G 云服务器时需要控制 JVM 内存：

```text
-Xms256m -Xmx768m
```

后端必须：

- 流式处理请求，避免大对象进内存。
- 不代理图片上传文件流。
- 不在日志中输出密钥。
- 统一错误响应。
- 对 Agent 上传节奏支持限流和重试。

## Photo-Agent 技术栈

推荐：

```text
Python 3.11+
SQLite
Pillow
requests 或 httpx
exifread / pillow-heif / piexif
APScheduler 或简单定时循环
```

Agent 负责：

- 扫描本地照片目录。
- 读取 EXIF 时间和 GPS。
- 生成 thumb / preview。
- 本地 SQLite 保存同步状态。
- 上传照片索引到后端。
- 申请 COS 临时上传 URL。
- 直传 thumb / preview 到 COS。
- 通知后端上传完成。
- 上报心跳。

Agent 不负责：

- 路线
- 地点
- AI 写作
- 腾讯地图调用
- COS 永久密钥管理
- 本地开放端口

## 数据库

MySQL 用于业务数据。

核心表：

- access_session
- agent
- district
- poi_cache
- photo
- photo_asset
- route
- route_city
- route_place
- route_place_photo
- article_draft
- article_generation_log

Redis 用于：

- Agent 在线状态
- access token 活跃续期辅助
- 短期限流
- 可选缓存

Agent 本地 SQLite 用于：

- 本地照片索引
- 缩略图/预览图生成状态
- 上传状态
- 失败重试状态

## 外部服务

腾讯地图：

- 行政区划列表
- 地点提示 / POI 候选

腾讯 COS：

- 私有读写桶
- thumb 存储
- preview 存储
- 后端生成短期上传 URL
- 后端生成短期下载 URL

MiMo-V2.5：

- AI 游记生成
- 重新生成
- 更朴实一点
- 更有感情一点

## 配置方式

生产环境使用环境变量。

后端：

```text
SPRING_PROFILES_ACTIVE=prod
DB_URL=
DB_USERNAME=
DB_PASSWORD=
REDIS_HOST=
REDIS_PORT=

ACCESS_CODE=
AGENT_TOKEN=

TENCENT_MAP_KEY=

COS_REGION=ap-guangzhou
COS_BUCKET=baizhi-wandernote-1318597275
COS_SECRET_ID=
COS_SECRET_KEY=
COS_UPLOAD_URL_TTL_SECONDS=600
COS_DOWNLOAD_URL_TTL_SECONDS=900

MIMO_API_BASE_URL=
MIMO_API_KEY=
MIMO_MODEL=mimo-v2.5
```

Photo-Agent：

```yaml
agent_id: home-mac-001
server_url: https://api.example.com
agent_token: 本地配置
photo_root: /Users/xxx/Pictures/旅行照片
scan_interval_minutes: 10
```

仓库中只能提交：

```text
.env.example
config.example.yaml
```

不能提交真实密钥。

## 部署方式

MVP 推荐单机部署：

```text
云服务器 2C2G
  - Nginx
  - Spring Boot
  - MySQL
  - Redis
```

图片文件不走云服务器上传流量。

thumb 和 preview 由 Photo-Agent 直传 COS。

前端部署方式：

- H5 静态文件由 Nginx 托管。
- 或前期直接由后端静态资源托管。

建议：

```text
Nginx 托管 frontend dist
Nginx 反向代理 /api 到 Spring Boot
```

## 开发环境

本地开发建议：

```text
frontend: npm run dev
backend: Spring Boot 本地启动
mysql/redis: Docker 或本机服务
photo-agent: Python 本地运行
```

开发阶段可使用测试照片目录。

禁止用真实密钥写死在代码里。

## 日志与排查

后端日志需要记录：

- request id
- agent id
- route id
- photo id
- storage_key
- 腾讯地图请求状态
- COS 签名生成状态
- AI 调用成功/失败

不能记录：

- access code
- access token
- agent token
- COS SecretKey
- MiMo API key
- 腾讯地图 key

前端同步状态页用于远程排查。

Agent 本地也应保存简短日志，方便后续查看同步失败原因。

## 性能边界

MVP 目标：

```text
单用户 / 单家庭
1 个 Photo-Agent
1-2 万张照片
每篇文章最多 10 张照片
低并发访问
```

2C2G 云服务器可用，但需要：

- 控制 JVM 内存。
- MySQL/Redis 使用轻量配置。
- Agent 分批上传索引。
- Agent 控制 COS 上传并发。
- 后端支持 429 限流和 Retry-After。
- 日志控制大小。

Agent 上传建议：

```text
索引上传：每批 100 张
thumb 上传并发：3
preview 上传并发：1
失败重试：指数退避
服务器忙：按 Retry-After 等待
```

## 开发顺序建议

建议按以下顺序落地：

1. backend 基础工程、数据库、Redis、访问码登录。
2. district 行政区划初始化和查询接口。
3. COS 签名上传/下载接口。
4. Photo-Agent 扫描、生成图片、上传索引、直传 COS。
5. route / route_city / route_place 后端接口。
6. 地点解析和照片 GPS 匹配。
7. frontend 页面和接口联调。
8. AI 写作服务。
9. 同步状态页和异常处理。
10. MVP 验收。

## 产品原则

工程结构必须保持清晰。

```text
前端负责体验。
后端负责业务和外部服务。
Photo-Agent 负责本地照片同步。
文档负责记录决策。
密钥只在安全配置中。
临时文件不进项目目录。
```
