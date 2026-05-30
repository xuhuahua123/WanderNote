# WanderNote Backend

云端 Spring Boot 后端服务。

## 技术栈

- Java 17
- Spring Boot 3.2.5
- MyBatis-Plus 3.5.5
- MySQL 8.x
- Redis
- 腾讯 COS SDK
- JWT (jjwt 0.12.5)

## 开发进度

最后更新：2026-05-30

### 里程碑状态

| 里程碑 | 状态 | 说明 |
|--------|------|------|
| M0 - 工程骨架 | ✅ 完成 | 可独立启动 |
| M1 - 后端基础与行政区划 | ✅ 完成 | 登录和行政区划可用 |
| M2 - Photo-Agent 索引与 COS | ✅ 完成 | 已与 Photo-Agent V2 联调通过 |
| M3 - 路线和照片匹配 | ❌ 待开发 | - |
| M4 - AI 写作与草稿 | ❌ 待开发 | - |
| M5 - 联调和异常处理 | ❌ 待开发 | - |
| M6 - MVP 验收 | ❌ 待开发 | - |

### M0 - 工程骨架 ✅

| 任务 | 状态 |
|------|------|
| Spring Boot 工程初始化 (3.2.5 + Java 17) | ✅ |
| Maven 依赖配置 | ✅ |
| MySQL 配置 (HikariCP 连接池) | ✅ |
| Redis 配置 | ✅ |
| MyBatis-Plus 配置 (含自动填充处理器) | ✅ |
| 统一响应结构 `ApiResponse<T>` | ✅ |
| 统一错误码 `ErrorCode` | ✅ |
| 全局异常处理 `GlobalExceptionHandler` | ✅ |

### M1 - 后端基础与行政区划 ✅

| 任务 | 状态 | 接口 |
|------|------|------|
| 访问码登录 | ✅ | `POST /api/auth/access-code/login` |
| Token 续期 | ✅ | `POST /api/auth/refresh` |
| JWT 工具类 | ✅ | `JwtUtils` |
| 用户认证过滤器 | ✅ | `JwtAuthenticationFilter` |
| 省份列表 | ✅ | `GET /api/districts/provinces` |
| 城市/地区列表 | ✅ | `GET /api/districts/provinces/{adcode}/cities` |
| 行政区划初始化 | ✅ | `POST /api/admin/districts/init` |
| 健康检查 | ✅ | `GET /api/health`, `/api/health/db`, `/api/health/redis` |

### M2 - Photo-Agent 索引与 COS 上传 ✅

| 任务 | 状态 | 接口 |
|------|------|------|
| Agent Token 鉴权 | ✅ | `AgentAuthenticationFilter` |
| Agent 心跳 | ✅ | `POST /api/agent/heartbeat` |
| 批量照片索引上传 | ✅ | `POST /api/agent/photos/batch` |
| COS 上传地址申请 | ✅ | `POST /api/agent/assets/upload-ticket` |
| COS 上传完成通知 | ✅ | `POST /api/agent/assets/upload-complete` |
| 图片短期下载 URL | ✅ | `POST /api/photos/signed-urls` |
| 同步状态查询 | ✅ | `GET /api/sync/status` |
| COS 服务封装 | ✅ | `CosService` |
| Redis Agent 在线状态 | ✅ | TTL 90 秒 |

**联调记录 (2026-05-30)**：
- 与 Photo-Agent V2 完成联调
- 修复问题：
  - 时间格式解析：支持 ISO 带时区 (`+00:00`) 和不带时区格式
  - photoId 类型：支持 localPhotoId 字符串查询

### 数据库表

| 表名 | 状态 | 说明 |
|------|------|------|
| `access_session` | ✅ | 访问会话 |
| `agent` | ✅ | Agent 状态 |
| `district` | ✅ | 行政区划 |
| `poi_cache` | ✅ | POI 缓存（表已创建，功能待实现） |
| `photo` | ✅ | 照片索引 |
| `photo_asset` | ✅ | 照片资源 |
| `route` | ✅ | 路线（表已创建，功能待实现） |
| `route_city` | ✅ | 路线城市（表已创建，功能待实现） |
| `route_place` | ✅ | 路线地点（表已创建，功能待实现） |
| `route_place_photo` | ✅ | 地点照片绑定（表已创建，功能待实现） |
| `article_draft` | ✅ | 文章草稿（表已创建，功能待实现） |
| `article_generation_log` | ✅ | AI 生成日志（表已创建，功能待实现） |

### 下一步计划

1. **M3 - 路线管理**：实现路线、城市、地点的 CRUD 接口
2. **M3 - 照片匹配**：实现 GPS 照片匹配算法
3. **M4 - AI 写作**：集成 MiMo-V2.5，实现游记生成

---

## 快速开始

### 1. 环境准备

确保已安装：
- JDK 17+
- Maven 3.8+
- MySQL 8.x
- Redis

### 2. 数据库初始化

```bash
# 创建数据库并导入表结构
mysql -u root -p < src/main/resources/db/schema.sql
```

或手动执行 SQL：

```sql
source src/main/resources/db/schema.sql;
```

### 3. 配置环境变量

复制配置模板：

```bash
cp .env.example .env.dev
```

编辑 `.env.dev` 填入真实配置：

```properties
# 数据库
DB_URL=jdbc:mysql://localhost:3306/wandernote?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai
DB_USERNAME=wandernote
DB_PASSWORD=your_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# 访问码和 Agent Token
ACCESS_CODE=your_access_code
AGENT_TOKEN=your_agent_token

# 腾讯地图
TENCENT_MAP_KEY=your_tencent_map_key

# 腾讯 COS
COS_REGION=ap-guangzhou
COS_BUCKET=baizhi-wandernote-1318597275
COS_SECRET_ID=your_secret_id
COS_SECRET_KEY=your_secret_key

# MiMo AI
MIMO_API_BASE_URL=your_mimo_api_url
MIMO_API_KEY=your_mimo_api_key
```

### 4. 启动服务

```bash
# 开发环境
mvn spring-boot:run

# 或指定配置
mvn spring-boot:run -Dspring-boot.run.profiles=dev

# 打包
mvn clean package -DskipTests

# 生产环境运行
java -Xms256m -Xmx768m -jar target/wandernote-backend-0.1.0-SNAPSHOT.jar
```

---

## 已实现接口

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/access-code/login | 访问码登录 |
| POST | /api/auth/refresh | Token 续期 |

### 行政区划接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/districts/provinces | 省份列表 |
| GET | /api/districts/provinces/{adcode}/cities | 城市/地区列表 |

### Agent 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/agent/heartbeat | Agent 心跳 |
| POST | /api/agent/photos/batch | 批量上传照片索引 |
| POST | /api/agent/assets/upload-ticket | 申请 COS 上传地址 |
| POST | /api/agent/assets/upload-complete | 通知上传完成 |

### 同步状态接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/sync/status | 获取同步状态 |

### 照片接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/photos/signed-urls | 批量获取签名下载 URL |

### 管理接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/admin/districts/init | 初始化行政区划 |

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查 |
| GET | /api/health/db | 数据库连接检查 |
| GET | /api/health/redis | Redis 连接检查 |

---

## 接口鉴权

### H5 前端

登录后获取 access token，后续请求在 header 中携带：

```
Authorization: Bearer <access_token>
```

### Photo-Agent

请求时在 header 中携带 Agent Token：

```
X-Agent-Token: <agent_token>
```

或

```
Authorization: Bearer <agent_token>
```

---

## 测试方法

### 测试登录

```bash
curl -X POST http://localhost:8080/api/auth/access-code/login \
  -H "Content-Type: application/json" \
  -d '{"accessCode":"your_access_code"}'
```

### 测试心跳

```bash
curl -X POST http://localhost:8080/api/agent/heartbeat \
  -H "Content-Type: application/json" \
  -H "X-Agent-Token: your_agent_token" \
  -d '{
    "agentId": "test-agent",
    "version": "0.1.0",
    "status": "idle",
    "photoCount": 100,
    "gpsPhotoCount": 95
  }'
```

### 测试同步状态

```bash
curl http://localhost:8080/api/sync/status \
  -H "Authorization: Bearer <access_token>"
```

### 初始化行政区划

```bash
curl -X POST http://localhost:8080/api/admin/districts/init
```

---

## 与 Photo-Agent 联调

1. 确保 Agent Token 配置正确
2. Agent 启动后调用心跳接口确认连接
3. Agent 扫描照片后调用批量上传接口
4. Agent 申请 COS 上传地址后直传 COS
5. Agent 上传完成后通知后端

---

## 性能配置

针对 2C2G 云服务器：

```bash
# JVM 内存配置
-Xms256m -Xmx768m

# MySQL 连接池（已在 application.yml 配置）
minimum-idle: 2
maximum-pool-size: 5
```

---

## 安全注意事项

- 所有密钥只能从环境变量读取
- 不在日志中输出任何密钥
- COS 使用短期签名 URL
- Agent Token 不具备外部服务调用权限
- 访问码登录后生成 JWT token

---

## 参考文档

- [后端数据模型](../docs/decisions/003-backend-data-model.md)
- [AI 写作服务](../docs/decisions/004-ai-writing-service.md)
- [API 接口协议](../docs/decisions/005-api-contract.md)
- [外部服务与密钥](../docs/decisions/006-external-services-and-secrets.md)
- [项目架构](../docs/decisions/007-project-architecture.md)
- [MVP 路线图](../docs/decisions/008-mvp-roadmap.md)
