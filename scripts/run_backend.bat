@echo off
chcp 65001 >nul
color 0A
title Backend API (Uvicorn)
echo ========================================================
echo INTELLIGENT OTTOMAN ASSISTANT - BACKEND API (PORT: 8000)
echo ========================================================
echo.
cd /d "%~dp0..\backend"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo Calisma dizini: %CD%
echo FastAPI sunucusu baslatiliyor...
echo.

"%~dp0..\backend\venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000

if errorlevel 1 (
    echo.
    echo ========================================================
    echo [HATA] Backend API beklenmedik sekilde durdu!
    echo ========================================================
)
pause
