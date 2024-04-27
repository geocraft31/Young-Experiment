@echo off
set "scriptPath=%~dp0"
cd /d "%scriptPath%"
call venv\Scripts\activate
start /min "" cmd /c "py main.py"
deactivate
