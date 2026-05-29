# photo-agent

家庭电脑照片同步 Agent。

## 技术栈

计划使用：

```text
Python 3.11+
SQLite
Pillow
httpx 或 requests
EXIF 解析库
```

## 主要职责

- 扫描本地照片目录
- 读取 EXIF 时间和 GPS
- 生成 thumb / preview
- 批量上传照片索引
- 申请 COS 临时上传 URL
- 直传 COS
- 通知后端上传完成
- 上报心跳
- 失败重试和限速

## 参考文档

```text
../docs/decisions/002-photo-agent.md
../docs/decisions/005-api-contract.md
../docs/decisions/006-external-services-and-secrets.md
../docs/decisions/007-project-architecture.md
../docs/decisions/008-mvp-roadmap.md
../docs/decisions/009-agent-prompts.md
```

## 配置

复制 `config.example.yaml` 为 `config.yaml`。

真实 `agent_token` 不得提交。

