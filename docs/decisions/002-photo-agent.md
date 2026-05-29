# 002. Photo-Agent 功能决策记录

## 状态

已确认。

## 背景

项目中的照片存放在家庭电脑本地。手机端不能直接访问家庭电脑，也不能要求家庭电脑开放公网端口。

因此需要一个运行在家庭电脑上的 Photo-Agent，负责把本地照片变成云端可用的照片素材库。

Photo-Agent 的定位是：

```text
本地照片同步器
```

它不是路线管理器，也不是写作助手。

## 核心职责

Photo-Agent 只负责：

- 扫描本地照片目录
- 读取照片基础信息
- 读取 EXIF 拍摄时间
- 读取 EXIF GPS 经纬度
- 生成缩略图
- 生成预览图
- 上传照片索引
- 上传缩略图和预览图
- 上报心跳和同步状态
- 失败任务重试

Photo-Agent 不负责：

- 路线管理
- 城市/地点管理
- 地点解析
- 照片归类到路线
- AI 写作
- 公众号草稿
- 原图上传
- 本地公网访问

## 照片扫描

Agent 启动时读取配置中的照片根目录。

示例：

```text
/Users/xxx/Pictures/旅行照片
D:\旅行照片
```

MVP 支持图片格式：

- jpg
- jpeg
- png
- heic

扫描字段：

- 相对路径
- 文件名
- 文件大小
- 文件修改时间
- 图片宽度
- 图片高度
- 拍摄时间
- GPS 纬度
- GPS 经度
- 文件 hash

没有 GPS 的照片也记录，但 MVP 不参与自动地点匹配。

## 本地索引

Photo-Agent 使用本地 SQLite 维护照片索引，避免每次全量重扫。

建议本地表：

```text
photos
- id
- relative_path
- file_size
- mtime
- content_hash
- taken_at
- lat
- lng
- width
- height
- thumb_path
- preview_path
- index_sync_status
- thumb_sync_status
- preview_sync_status
- last_error
- updated_at
```

本地索引用于判断：

- 哪些照片是新增的
- 哪些照片被修改了
- 哪些照片已经生成缩略图
- 哪些照片已经上传
- 哪些照片同步失败，需要重试

## 缩略图和预览图

Agent 生成两类图片：

```text
缩略图 thumb：长边 360px
预览图 preview：长边 1280px
```

用途：

- thumb 用于照片网格列表。
- preview 用于大图预览和公众号草稿预览。

MVP 不上传原图。

thumb 和 preview 都上传到腾讯 COS。

Photo-Agent 不保存 COS 密钥，只使用后端下发的临时上传 URL。

## 上传策略

Agent 主动连接云端，不开放本地端口。

上传内容：

- 照片索引
- 缩略图
- 预览图
- 同步状态

上传分工：

- Photo-Agent 上传照片索引到云服务器后端。
- 后端为 thumb 和 preview 生成 COS 存储路径。
- 后端生成短期有效的 COS 临时上传 URL。
- Photo-Agent 使用临时上传 URL 直传 COS。
- Photo-Agent 上传完成后通知后端。
- 后端写入 `photo_asset` 记录。

云端保存照片索引和图片资源地址后，前端通过后端返回的 COS 地址访问缩略图和预览图。

不允许：

- 家庭电脑开放公网端口
- 内网穿透
- 手机直接访问家庭电脑
- Photo-Agent 保存 COS 永久密钥

上传流程：

```text
Photo-Agent 生成 thumb / preview
  -> 上传照片索引到后端
  -> 向后端申请上传地址
  -> 后端返回 storage_key 和临时上传 URL
  -> Photo-Agent 直传 COS
  -> Photo-Agent 通知后端上传完成
  -> 后端写入 photo_asset
```

## 同步策略

MVP 同步策略：

- Agent 启动后立即扫描一次。
- 每隔 10 分钟做一次增量扫描。
- 发现新增或修改照片后，生成缩略图和预览图。
- 上传照片索引和图片。
- 同步失败的任务记录错误，下次自动重试。

MVP 不做实时文件监听。

原因：

- macOS / Windows 文件监听细节较多。
- 第一版优先稳定可靠。
- 10 分钟增量扫描已经能满足家庭旅行照片同步场景。

## 心跳机制

Photo-Agent 定时向云端上报心跳。

建议：

```text
心跳间隔：30 秒
Redis TTL：90 秒
```

心跳接口示例：

```text
POST /api/agent/heartbeat
```

心跳内容示例：

```json
{
  "agentId": "home-mac-001",
  "version": "0.1.0",
  "status": "idle",
  "lastScanAt": "2026-05-28T18:18:02",
  "lastSyncAt": "2026-05-28T18:20:00",
  "photoCount": 428,
  "gpsPhotoCount": 421,
  "thumbSyncedCount": 428,
  "previewSyncedCount": 428,
  "failedCount": 0
}
```

后端收到心跳后：

1. 更新数据库中的 Agent 状态。
2. 写入 Redis 在线 key。
3. 设置 Redis 过期时间。

Redis key 示例：

```text
agent:online:home-mac-001 = 1
TTL = 90 秒
```

如果 Agent 正常在线，每 30 秒刷新一次 TTL。

如果 Agent 离线、电脑关机或网络断开，Redis key 会在 90 秒后自动过期。

## 在线状态判断

前端同步状态页调用：

```text
GET /api/sync/status
```

后端判断：

```text
Redis 中存在 agent:online:{agentId} -> 在线
Redis 中不存在 agent:online:{agentId} -> 离线
```

Redis 只负责当前在线状态。

数据库保存长期状态：

- Agent ID
- Agent 版本
- 最近心跳时间
- 最近扫描时间
- 最近同步时间
- 照片总数
- GPS 照片数量
- 缩略图同步数量
- 预览图同步数量
- 失败数量

这样即使 Agent 离线，前端也能显示最近一次同步结果。

## 配置形态

MVP 可以使用简单配置文件。

示例：

```yaml
agent_id: home-mac-001
server_url: https://api.example.com
photo_root: /Users/xxx/Pictures/旅行照片
scan_interval_minutes: 10
```

第一版可以做成：

```text
Python 后台程序 + SQLite + 配置文件
```

后续再考虑桌面托盘图标或图形界面。

## MVP 暂不做

- AI 图片识别
- 自动路线识别
- 自动地点归类
- 视频处理
- 原图上传
- 本地 Web 服务
- 复杂桌面 GUI
- 实时文件监听
- 多电脑 Agent
- 双向删除照片
- 手机直接访问家庭电脑

## 产品原则

Photo-Agent 越简单越可靠。

智能逻辑放在云端，Agent 只做稳定的数据同步。

核心原则：

```text
本地照片不出原图。
家庭电脑不开放端口。
Agent 主动连接云端。
云端负责路线、地点和写作。
```
