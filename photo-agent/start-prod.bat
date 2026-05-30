@echo off
echo WanderNote Photo Agent (生产环境)
echo ==================================================

cd /d "%~dp0"

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM 设置生产环境
set AGENT_ENV=prod

REM 启动 Agent
python -m agent.main

pause
