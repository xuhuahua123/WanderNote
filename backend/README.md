# backend

云端 Spring Boot 后端。

## 技术栈

计划使用：

```text
Java 17/21
Spring Boot
MySQL
Redis
Tencent COS Java SDK
HTTP Client
```

## 主要职责

- 访问码登录和 token 续期
- Agent 鉴权和心跳
- 行政区划初始化
- 路线、城市、地点接口
- 腾讯地图地点解析
- 照片 GPS 匹配
- COS 临时上传/下载 URL
- AI 写作服务
- 草稿保存
- 同步状态接口

## 参考文档

```text
../docs/decisions/003-backend-data-model.md
../docs/decisions/004-ai-writing-service.md
../docs/decisions/005-api-contract.md
../docs/decisions/006-external-services-and-secrets.md
../docs/decisions/007-project-architecture.md
../docs/decisions/008-mvp-roadmap.md
../docs/decisions/009-agent-prompts.md
```

## 配置

复制 `.env.example` 为本地环境配置。真实密钥不得提交。

