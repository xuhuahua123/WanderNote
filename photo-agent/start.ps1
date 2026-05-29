# WanderNote Photo Agent 启动脚本

Write-Host "WanderNote Photo Agent" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 切换到脚本目录
Set-Location $PSScriptRoot

# 激活虚拟环境
& .\.venv\Scripts\Activate.ps1

# 检查配置文件
if (-not (Test-Path "config.yaml")) {
    Write-Host "错误: 配置文件不存在" -ForegroundColor Red
    Write-Host "请复制 config.example.yaml 为 config.yaml 并填写配置" -ForegroundColor Yellow
    Read-Host "按 Enter 键退出"
    exit 1
}

# 启动 Agent
python -m agent.main
