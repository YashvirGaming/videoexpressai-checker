@echo off
title VideoExpress.AI Checker Launcher - By Yashvir Gaming
cd /d "%~dp0"

REM Prioritize EXE if exists, else use main.py
if exist main.exe (
    start "" main.exe
) else (
    if exist main.py (
        python main.py
    ) else (
        echo main.py or main.exe not found in %CD%
        pause
    )
)
