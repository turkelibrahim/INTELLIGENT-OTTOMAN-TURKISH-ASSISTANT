@echo off
echo Starting Ottoman Turkish Assistant Backend (v1.0.0-RC1)
echo.

if not exist ".env" (
    echo WARNING: .env file not found. Copying .env.example to .env
    copy .env.example .env
    echo Please edit .env file and set a secure SECRET_KEY before running in production!
)

if exist "venv\Scripts\activate.bat" (
    echo Activating Virtual Environment...
    call venv\Scripts\activate.bat
)

echo Configuring Environment Variables...
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo Running Database Migrations...
alembic upgrade head

echo Starting API Server...
uvicorn app.main:app --host 127.0.0.1 --port 8000
