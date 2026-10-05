@echo off
title Local Python AI Agent
cd /d "%~dp0"
echo Activating virtual environment...
call .\venv\Scripts\activate.bat
echo Starting Agent...
python agent.py
pause
