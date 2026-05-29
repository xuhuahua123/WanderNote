@echo off
echo WanderNote Photo Agent
echo ==================================================

cd /d "%~dp0"

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM 检查配置文件
if not exist config.yaml (
    echo 错误: 配置文件不存在
    echo 请复制 config.example.yaml 为 config.yaml 并填写配置
    pause
    exit /b 1
)

REM 启动 Agent
python -m agent.main

pause
