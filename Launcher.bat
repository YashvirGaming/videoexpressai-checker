@echo off
title VideoExpress.AI Checker Launcher - By Yashvir Gaming
cd /d "%~dp0"

REM Prioritize EXE if exists, else use main.py
if exist main.exe (
    start "" videoexpress_checker.exe
) else (
    if exist main.py (
        python videoexpress_gui.py
    ) else (
        echo videoexpress_gui.py or videoexpress_checker.exe not found in %CD%
        pause
    )
)
