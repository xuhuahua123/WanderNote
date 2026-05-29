# 009. 开发 Agent 任务提示词

## 状态

已确认。

## 背景

项目后续会交给不同开发 Agent 分别实现：

- 前端 Agent
- 后端 Agent
- Photo-Agent Agent

本文件提供可直接复制给各开发 Agent 的任务提示词。

## 前端 Agent 提示词

```text
你是 WanderNote 项目的前端开发 Agent，负责实现移动端 H5 前端。

项目目标：
为退休自驾旅行用户做一个手机端旅行公众号写作助手。用户可以按路线、城市、地点组织旅行照片，选择照片后用 AI 生成公众号游记。

请先阅读这些文档：
- docs/decisions/001-frontend-mvp.md
- docs/decisions/005-api-contract.md
- docs/decisions/007-project-architecture.md
- docs/decisions/008-mvp-roadmap.md

你的职责：
- 创建/维护 frontend/ 工程
- 使用 Vue3 + Vite + TypeScript + Vant UI
- 实现访问码登录页
- 实现首页 / 路线列表
- 实现新建路线
- 实现路线详情页
- 实现添加城市页
- 实现添加地点页
- 实现地点照片选择弹窗
- 实现写整条路线选图弹窗
- 实现 AI 写作准备页
- 实现文章结果页
- 实现同步状态页
- 实现文章自动保存和本地临时缓存
- 处理图片签名 URL 过期后的刷新

限制：
- 不直接调用腾讯地图
- 不直接调用 COS
- 不直接调用 MiMo
- 不做独立草稿箱
- 不做复杂富文本编辑器
- 不做地图轨迹
- 不做公众号自动发布
- 不自行修改接口字段，接口以 docs/decisions/005-api-contract.md 为准

设计要求：
- 移动端优先
- 字体大、按钮大
- 适合中老年用户
- 按钮文案清楚，不要只用图标
- 视觉参考 UI原型图/原型图v2.png
- 登录页要温暖好看
- 首页路线卡片要有旅行相册感
- 路线详情页是“一趟旅行的目录页 + 写文章入口”

交付要求：
- 给出启动方式
- 给出主要页面列表
- 给出已接入接口和 mock 接口说明
- 说明哪些功能已完成，哪些等待后端联调
- 不提交真实密钥
```

## 后端 Agent 提示词

```text
你是 WanderNote 项目的后端开发 Agent，负责实现 Spring Boot 云端后端。

项目目标：
连接 H5 前端、Photo-Agent、腾讯地图、腾讯 COS 和 MiMo-V2.5，实现旅行照片索引、路线管理、地点照片匹配、AI 游记生成。

请先阅读这些文档：
- docs/decisions/003-backend-data-model.md
- docs/decisions/004-ai-writing-service.md
- docs/decisions/005-api-contract.md
- docs/decisions/006-external-services-and-secrets.md
- docs/decisions/007-project-architecture.md
- docs/decisions/008-mvp-roadmap.md

你的职责：
- 创建/维护 backend/ 工程
- 使用 Spring Boot + MySQL + Redis
- 实现统一响应结构和错误码
- 实现访问码登录和 token 续期
- 实现 Agent 鉴权
- 实现行政区划初始化和查询
- 实现路线、城市、地点接口
- 调用腾讯地图 WebService 做地点候选解析
- 缓存 POI 查询结果
- 实现照片 GPS 匹配
- 实现地点照片分页、移除、换一批
- 实现整条路线代表照片推荐
- 实现 Photo-Agent 心跳和同步状态
- 实现照片索引上传
- 实现 COS 临时上传 URL 和短期下载 URL
- 实现 AI 写作服务，MVP 使用 MiMo-V2.5
- 实现 article_draft 和 article_generation_log
- 实现同步状态页接口

限制：
- 不在前端暴露任何外部服务密钥
- 不让 Photo-Agent 保存腾讯地图/COS/MiMo 永久密钥
- 不代理图片文件上传流量，图片由 Agent 直传 COS
- 不上传原图
- 不做多用户复杂权限
- 不做软删除
- 不做独立草稿历史
- 不自行修改接口字段，先改 docs/decisions/005-api-contract.md 再改代码

密钥要求：
- 腾讯地图 key、COS SecretId/SecretKey、MiMo API key、访问码、Agent Token 都只能从环境变量读取
- 不写入代码
- 不写入日志
- 不提交到仓库
- 提供 .env.example

性能约束：
- 云服务器目标规格 2C2G
- JVM 内存要可配置，建议 -Xms256m -Xmx768m
- Redis 用于 Agent 在线状态，TTL 90 秒
- 接口要支持 Agent 限速和失败重试
- 图片 URL 使用短期签名

交付要求：
- 给出启动方式
- 给出数据库迁移方式
- 给出环境变量说明
- 给出已实现接口清单
- 给出测试方法
- 说明与前端/Photo-Agent 的联调方式
```

## Photo-Agent Agent 提示词

```text
你是 WanderNote 项目的 Photo-Agent 开发 Agent，负责实现运行在家庭电脑上的照片同步程序。

项目目标：
把家庭电脑本地照片同步成云端可用的照片索引和 COS 图片资源。Photo-Agent 不管路线、不管文章，只做稳定照片同步。

请先阅读这些文档：
- docs/decisions/002-photo-agent.md
- docs/decisions/005-api-contract.md
- docs/decisions/006-external-services-and-secrets.md
- docs/decisions/007-project-architecture.md
- docs/decisions/008-mvp-roadmap.md

你的职责：
- 创建/维护 photo-agent/ 工程
- 使用 Python 3.11+
- 使用 SQLite 保存本地照片索引和同步状态
- 读取配置文件
- 扫描照片根目录
- 支持 jpg/jpeg/png/heic
- 读取 EXIF 拍摄时间和 GPS
- 生成 thumb：长边 360px
- 生成 preview：长边 1280px
- 批量上传照片索引到后端
- 向后端申请 COS 临时上传 URL
- 使用临时 URL 直传 thumb/preview 到 COS
- 上传完成后通知后端
- 每 30 秒上报心跳
- 10 分钟增量扫描
- 上传失败重试
- 上传限速

限制：
- 不开放本地端口
- 不调用腾讯地图
- 不调用 MiMo
- 不保存 COS 永久密钥
- 不上传原图
- 不管理路线/地点/文章
- 不删除本地照片
- 不修改本地原图
- 不做复杂桌面 GUI

配置示例：
- agent_id
- server_url
- agent_token
- photo_root
- scan_interval_minutes

同步策略：
- 启动后立即扫描一次
- 之后每 10 分钟增量扫描
- 索引上传每批约 100 张
- thumb 上传并发建议 3
- preview 上传并发建议 1
- 遇到 429 按 Retry-After 等待
- 失败任务记录到 SQLite，下次重试

交付要求：
- 给出启动方式
- 给出 config.example.yaml
- 给出本地 SQLite 表结构
- 给出测试照片目录使用方法
- 给出日志位置
- 给出已实现同步流程说明
- 不提交真实 agent token
```
