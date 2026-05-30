@echo off
chcp 65001 >nul
echo WanderNote Photo Agent (生产环境)
echo ==================================================

cd /d "%~dp0"

set AGENT_ENV=prod

.venv\Scripts\python.exe -m agent.main

pause
