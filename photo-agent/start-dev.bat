@echo off
echo WanderNote Photo Agent (开发环境)
echo ==================================================

cd /d "%~dp0"

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM 设置开发环境
set AGENT_ENV=dev

REM 启动 Agent
python -m agent.main

pause
