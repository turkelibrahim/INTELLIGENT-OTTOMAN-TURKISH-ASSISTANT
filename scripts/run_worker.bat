@echo off
chcp 65001 >nul
color 0B
title Backend Worker (OCR & AI)
echo ========================================================
echo INTELLIGENT OTTOMAN ASSISTANT - WORKER (OCR & AI)
echo ========================================================
echo.
cd /d "%~dp0..\backend"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo Calisma dizini: %CD%
echo Arka plan OCR isleri ve yapay zeka kuyrugu baslatiliyor...
echo.

"%~dp0..\backend\venv\Scripts\python.exe" worker.py

if errorlevel 1 (
    echo.
    echo ========================================================
    echo [HATA] Worker beklenmedik sekilde durdu!
    echo ========================================================
)
pause
