@echo off
chcp 65001 >nul
echo WanderNote Photo Agent (开发环境)
echo ==================================================

cd /d "%~dp0"

set AGENT_ENV=dev

.venv\Scripts\python.exe -m agent.main

pause
