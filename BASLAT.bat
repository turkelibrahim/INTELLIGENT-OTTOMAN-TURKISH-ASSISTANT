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
timeout /t 2 /nobreak >nul

echo [2/4] Backend API (FastAPI) baslatiliyor...
start "Backend API (Uvicorn)" "%~dp0scripts\run_backend.bat"
timeout /t 2 /nobreak >nul

echo [3/4] OCR Worker (Arka Plan Isleri) baslatiliyor...
start "Backend Worker (OCR)" "%~dp0scripts\run_worker.bat"
timeout /t 2 /nobreak >nul

echo [4/4] Frontend (Next.js Arayuzu) baslatiliyor...
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
timeout /t 5 >nul
start http://localhost:3000
