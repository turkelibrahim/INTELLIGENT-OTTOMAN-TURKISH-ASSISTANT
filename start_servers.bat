@echo off
chcp 65001 >nul
color 0E
title INTELLIGENT OTTOMAN ASSISTANT - MASTER LAUNCHER
echo ========================================================
echo INTELLIGENT OTTOMAN TURKISH ASSISTANT
echo ========================================================
echo.
echo Eski oturumlar ve portlar temizleniyor...
taskkill /F /IM node.exe >nul 2>&1

echo.
echo Proje bilesenleri ayri pencerelerde baslatiliyor...
echo.

echo [1/4] Yerel LLM (Ollama) kontrol ediliyor...
start "Local LLM (Ollama)" "%~dp0scripts\run_ollama.bat"
ping 127.0.0.1 -n 3 >nul

echo [2/5] Backend API (FastAPI) baslatiliyor...
start "Backend API (Uvicorn)" "%~dp0scripts\run_backend.bat"
ping 127.0.0.1 -n 3 >nul

echo [3/5] Persistent OCR Servisi (Kraken) baslatiliyor...
start "Persistent OCR (Kraken)" powershell -ExecutionPolicy Bypass -File "%~dp0scripts\start_kraken_service.ps1"
ping 127.0.0.1 -n 6 >nul

echo [4/5] OCR Worker (Arka Plan Isleri) baslatiliyor...
start "Backend Worker (OCR)" "%~dp0scripts\run_worker.bat"
ping 127.0.0.1 -n 3 >nul

echo [5/5] Frontend (Next.js Arayuzu) baslatiliyor...
start "Frontend (Next.js)" "%~dp0scripts\run_frontend.bat"

echo.
echo ========================================================
echo TUM SERVISLER BASARIYLA BASLATILDI!
echo ========================================================
echo.
echo - Lutfen acilan pencereleri isiniz bitene kadar KAPATMAYINIZ.
echo - Arayuz 5 saniye icinde tarayicinizda otomatik olarak acilacaktir...
echo   (Adres: http://localhost:3000)
echo.
ping 127.0.0.1 -n 6 >nul
start http://localhost:3000
