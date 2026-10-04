@echo off
chcp 65001 >nul
color 0E
title Local LLM (Ollama)
echo ========================================================
echo INTELLIGENT OTTOMAN ASSISTANT - LOCAL LLM (OLLAMA)
echo ========================================================
echo.

echo Ollama servisi kontrol ediliyor...
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1

if %errorlevel% equ 0 (
    echo [BILGI] Ollama servisi zaten sisteminizde aktif ve calisiyor.
    echo Modeller hazir: Qwen 3.5
    echo.
    echo Bu pencereyi kapatabilirsiniz veya acik birakabilirsiniz.
    timeout /t 5 >nul
    exit
) else (
    echo Ollama arka planda calismiyor, simdi baslatiliyor...
    echo.
    ollama serve
)
