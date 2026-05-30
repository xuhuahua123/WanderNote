# WanderNote Photo Agent 生产环境启动脚本

Write-Host "WanderNote Photo Agent (生产环境)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 切换到脚本目录
Set-Location $PSScriptRoot

# 设置生产环境
$env:AGENT_ENV = "prod"

# 激活虚拟环境
& .\.venv\Scripts\Activate.ps1

# 检查配置文件
if (-not (Test-Path "config.yaml") -and -not (Test-Path ".env.prod")) {
    Write-Host "错误: 配置文件不存在" -ForegroundColor Red
    Write-Host "请创建 config.yaml 或 .env.prod 并填写配置" -ForegroundColor Yellow
    Read-Host "按 Enter 键退出"
    exit 1
}

Write-Host "环境: prod" -ForegroundColor Green
Write-Host ""

# 启动 Agent
python -m agent.main
