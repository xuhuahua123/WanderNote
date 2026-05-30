# 环境变量配置指南

本文档说明如何在本地开发环境和生产服务器上配置环境变量。

## 需要配置的环境变量

### 密钥类（必须配置，不可提交到 Git）

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `DB_PASSWORD` | 数据库密码 | `your_db_password` |
| `ACCESS_CODE` | H5 访问码 | `wn2026travel` |
| `AGENT_TOKEN` | Agent 身份凭证 | `agent-sec-xyz-123` |
| `TENCENT_MAP_KEY` | 腾讯地图 Key | `PJZBZ-XXXXX` |
| `COS_SECRET_ID` | 腾讯云 SecretId | `AKIDxxxxx` |
| `COS_SECRET_KEY` | 腾讯云 SecretKey | `xxxxx` |
| `MIMO_API_KEY` | MiMo API Key | `sk-xxxxx` |
| `JWT_SECRET` | JWT 签名密钥 | `random-string-32chars` |

### 非密钥类（可写入配置文件）

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `SPRING_PROFILES_ACTIVE` | 运行环境 | `dev` / `prod` |
| `DB_URL` | 数据库连接地址 | 本地/服务器地址 |
| `DB_USERNAME` | 数据库用户名 | `wandernote` |
| `REDIS_HOST` | Redis 地址 | `localhost` |
| `REDIS_PORT` | Redis 端口 | `6379` |
| `COS_REGION` | COS 区域 | `ap-guangzhou` |
| `COS_BUCKET` | COS 存储桶 | `baizhi-wandernote-1318597275` |
| `MIMO_API_BASE_URL` | MiMo API 地址 | `https://api.xiaomimimo.com/v1/chat/completions` |
| `MIMO_MODEL` | MiMo 模型 | `mimo-v2.5` |

---

## 本地开发环境（Windows + IDEA）

### 方式一：IDEA 运行配置（推荐）

1. 打开 IDEA，点击右上角运行配置下拉框 → `Edit Configurations...`

2. 找到 `WanderNoteBackendApplication`

3. 点击 `Modify options` → 勾选 `Environment variables`

4. 在 `Environment variables` 字段填入（分号分隔）：

```
SPRING_PROFILES_ACTIVE=dev;DB_URL=jdbc:mysql://localhost:3306/wandernote_test?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai;DB_USERNAME=root;DB_PASSWORD=你的密码;REDIS_HOST=localhost;REDIS_PORT=6379;ACCESS_CODE=你的访问码;AGENT_TOKEN=你的AgentToken;TENCENT_MAP_KEY=你的地图Key;COS_REGION=ap-guangzhou;COS_BUCKET=baizhi-wandernote-1318597275;COS_SECRET_ID=你的SecretId;COS_SECRET_KEY=你的SecretKey;MIMO_API_BASE_URL=https://api.xiaomimimo.com/v1/chat/completions;MIMO_API_KEY=你的MiMoKey;MIMO_MODEL=mimo-v2.5
```

5. 点击 `Apply` → `OK`

6. 点击绿色运行按钮启动

### 方式二：使用 .env.dev 文件

1. 复制 `.env.example` 为 `.env.dev`，填入真实值

2. 在项目根目录执行：
```bash
# Git Bash 或 WSL
source .env.dev && mvn spring-boot:run

# PowerShell
Get-Content .env.dev | ForEach-Object { $parts = $_ -split '=', 2; if ($parts.Length -eq 2) { [Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), "Process") } }; mvn spring-boot:run
```

### 方式三：安装 EnvFile 插件

1. IDEA → `File` → `Settings` → `Plugins` → 搜索 `EnvFile` → 安装并重启

2. `Edit Configurations...` → `Modify options` → 勾选 `EnvFile`

3. 点击 `+` 添加 `.env.dev` 文件路径

---

## 生产环境（Linux 服务器）

### 步骤一：创建环境变量配置文件

```bash
sudo vi /etc/wandernote.env
```

内容如下（填入真实值）：

```bash
# WanderNote 环境变量配置

# 运行环境
export SPRING_PROFILES_ACTIVE="prod"

# 数据库配置
export DB_URL="jdbc:mysql://localhost:3306/wandernote?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai"
export DB_USERNAME="wandernote"
export DB_PASSWORD="你的数据库密码"

# Redis 配置
export REDIS_HOST="localhost"
export REDIS_PORT="6379"

# 访问码和 Agent Token
export ACCESS_CODE="你的访问码"
export AGENT_TOKEN="你的AgentToken"

# 腾讯地图
export TENCENT_MAP_KEY="你的腾讯地图Key"

# 腾讯云 COS
export COS_REGION="ap-guangzhou"
export COS_BUCKET="baizhi-wandernote-1318597275"
export COS_SECRET_ID="你的SecretId"
export COS_SECRET_KEY="你的SecretKey"
export COS_UPLOAD_URL_TTL_SECONDS="600"
export COS_DOWNLOAD_URL_TTL_SECONDS="900"

# MiMo AI
export MIMO_API_BASE_URL="https://api.xiaomimimo.com/v1/chat/completions"
export MIMO_API_KEY="你的MiMoKey"
export MIMO_MODEL="mimo-v2.5"

# JWT 密钥（建议生成 32 位随机字符串）
export JWT_SECRET="你的JWT密钥"
```

设置文件权限：
```bash
sudo chmod 600 /etc/wandernote.env
sudo chown root:root /etc/wandernote.env
```

### 步骤二：创建 systemd 服务

```bash
sudo vi /etc/systemd/system/wandernote.service
```

内容：

```ini
[Unit]
Description=WanderNote Backend Service
After=network.target mysql.service redis.service

[Service]
Type=simple
User=wandernote
WorkingDirectory=/opt/wandernote
EnvironmentFile=/etc/wandernote.env
ExecStart=/usr/bin/java -Xms256m -Xmx768m -jar /opt/wandernote/wandernote-backend.jar
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 步骤三：启动服务

```bash
# 重载 systemd 配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start wandernote

# 设置开机自启
sudo systemctl enable wandernote

# 查看状态
sudo systemctl status wandernote

# 查看日志
sudo journalctl -u wandernote -f
```

### 常用命令

```bash
# 重启服务
sudo systemctl restart wandernote

# 停止服务
sudo systemctl stop wandernote

# 查看最近日志
sudo journalctl -u wandernote -n 100

# 实时查看日志
sudo journalctl -u wandernote -f
```

---

## 验证环境变量是否生效

### Linux

```bash
source /etc/wandernote.env
echo $DB_URL
echo $ACCESS_CODE
```

### Windows PowerShell

```powershell
[Environment]::GetEnvironmentVariable("DB_URL", "User")
```

---

## 安全注意事项

1. **不要将 `.env.dev` 或 `.env.prod` 提交到 Git**
   - 已在 `.gitignore` 中配置忽略

2. **生产服务器的 `/etc/wandernote.env` 权限设为 600**
   - 只有 root 用户可读写

3. **定期更换密钥**
   - ACCESS_CODE、AGENT_TOKEN、JWT_SECRET 可以随时更换
   - COS 密钥更换后需同步更新配置文件并重启服务

4. **JWT_SECRET 建议**
   - 使用 32 位以上随机字符串
   - 生成方式：`openssl rand -base64 32`
