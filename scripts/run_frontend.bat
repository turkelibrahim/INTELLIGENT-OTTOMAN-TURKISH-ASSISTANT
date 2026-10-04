@echo off
chcp 65001 >nul
color 0D
title Frontend (Next.js)
echo ========================================================
echo INTELLIGENT OTTOMAN ASSISTANT - FRONTEND (PORT: 3000)
echo ========================================================
echo.
cd /d "%~dp0..\frontend"

echo Port 3000 temizleniyor...
taskkill /F /IM node.exe >nul 2>&1

echo Calisma dizini: %CD%
echo Next.js gelistirme sunucusu baslatiliyor...
echo.

call npm run dev

if errorlevel 1 (
    echo.
    echo ========================================================
    echo [HATA] Frontend beklenmedik sekilde durdu!
    echo ========================================================
)
pause
