@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --quiet -r requirements.txt
python scripts\collect.py
endlocal