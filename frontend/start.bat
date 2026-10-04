@echo off
echo Starting Ottoman Turkish Assistant Frontend...
echo.

if not exist "node_modules\" (
    echo node_modules not found. Installing dependencies...
    npm install
)

echo Starting Next.js development server...
set NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
npm run dev -- -H 127.0.0.1 -p 3000
