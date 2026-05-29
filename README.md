# WanderNote

退休旅行公众号写作助手。

本项目面向退休自驾旅行用户，帮助用户在手机端按旅行路线整理照片，并生成适合公众号发布的游记文章。

## 项目结构

```text
WanderNote/
  docs/           产品和技术决策文档
  UI原型图/       移动端 UI 原型图
  frontend/       H5 前端
  backend/        Spring Boot 后端
  photo-agent/    家庭电脑照片同步 Agent
  deploy/         部署配置模板
  scripts/        开发和维护脚本
```

## 当前阶段

当前处于 MVP 工程初始化阶段。

请先阅读：

```text
docs/decisions/001-frontend-mvp.md
docs/decisions/002-photo-agent.md
docs/decisions/003-backend-data-model.md
docs/decisions/004-ai-writing-service.md
docs/decisions/005-api-contract.md
docs/decisions/006-external-services-and-secrets.md
docs/decisions/007-project-architecture.md
docs/decisions/008-mvp-roadmap.md
docs/decisions/009-agent-prompts.md
```

## 安全规则

- 不提交真实密钥。
- 不提交 `.env`、`config.yaml`、本地数据库或生成图片。
- 前端不保存腾讯地图、COS、MiMo 密钥。
- Photo-Agent 不保存腾讯地图、COS、MiMo 永久密钥。
- 外部服务密钥只放云端后端环境变量。

## 开发分工

- 前端 Agent 只在 `frontend/` 工作。
- 后端 Agent 只在 `backend/` 工作。
- Photo-Agent Agent 只在 `photo-agent/` 工作。
- 部署配置放在 `deploy/`。
- 公共脚本放在 `scripts/`。

