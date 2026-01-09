@echo off
REM Smart-Ops-Term 启动脚本 (Windows)

echo Starting Smart-Ops-Term...
echo.

cd /d "%~dp0"
python src\main.py

pause
