# WanderNote Photo Agent 开发环境安装脚本

Write-Host "安装 Photo Agent 开发环境" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 切换到脚本目录
Set-Location $PSScriptRoot

# 激活虚拟环境
& .\.venv\Scripts\Activate.ps1

# 安装开发依赖
Write-Host "安装开发依赖..." -ForegroundColor Yellow
pip install -e ".[dev]"

Write-Host ""
Write-Host "开发环境安装完成！" -ForegroundColor Green
Write-Host ""
Write-Host "可用命令：" -ForegroundColor Cyan
Write-Host "  pytest           - 运行测试" -ForegroundColor White
Write-Host "  pytest -v        - 运行测试（详细输出）" -ForegroundColor White
Write-Host "  pytest --cov     - 运行测试并生成覆盖率报告" -ForegroundColor White
