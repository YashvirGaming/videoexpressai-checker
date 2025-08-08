@echo off
title Installing requirements.txt for VideoExpress.AI Checker
cd /d "%~dp0"

echo.
echo [!] Installing requirements. Please wait...
echo.

REM Optionally try to upgrade pip first
python -m pip install --upgrade pip

REM Install requirements.txt
python -m pip install -r requirements.txt

echo.
echo [!] All requirements installed.
pause
