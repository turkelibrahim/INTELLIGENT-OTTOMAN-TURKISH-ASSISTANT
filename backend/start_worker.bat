@echo off
color 0B
echo ========================================================
echo INTELLIGENT OTTOMAN TURKISH ASSISTANT - WORKER PROCESS
echo ========================================================
echo.

if exist "venv\Scripts\activate.bat" (
    echo Activating Virtual Environment...
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found. Worker may fail!
)

echo Configuring Environment Variables...
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo.
echo Starting Background Worker...
echo Leave this window open to process background tasks (OCR, LoRA).
echo.

python worker.py

echo.
echo Worker process stopped!
pause
