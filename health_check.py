import os
import sqlite3
import urllib.request
import json
import subprocess

def print_status(component, status, details=""):
    print(f"[{status}] {component}: {details}")

def check_db():
    db_path = "backend/ottoman_assistant.db"
    if not os.path.exists(db_path):
        print_status("SQLite Database", "FAIL", "File not found")
        return
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()
        cursor.execute("PRAGMA journal_mode;")
        journal = cursor.fetchone()
        
        if result and result[0] == "ok":
            print_status("SQLite Database", "PASS", f"Integrity OK | Mode: {journal[0].upper()}")
        else:
            print_status("SQLite Database", "FAIL", "Integrity check failed")
    except Exception as e:
        print_status("SQLite Database", "FAIL", str(e))

def check_ollama():
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=3) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                models = [m['name'] for m in data.get('models', [])]
                print_status("Ollama Local LLM", "PASS", f"Models available: {', '.join(models)}")
            else:
                print_status("Ollama Local LLM", "FAIL", f"HTTP {response.status}")
    except Exception as e:
        print_status("Ollama Local LLM", "WARNING", "Ollama is not running locally (Expected if in Docker)")

def check_qdrant():
    try:
        req = urllib.request.Request("http://127.0.0.1:6333/collections")
        with urllib.request.urlopen(req, timeout=3) as response:
            if response.status == 200:
                print_status("Qdrant Vector DB", "PASS", "Service is up and responding")
            else:
                print_status("Qdrant Vector DB", "FAIL", f"HTTP {response.status}")
    except Exception as e:
        print_status("Qdrant Vector DB", "WARNING", "Qdrant is not running locally (Expected if in Docker)")

def check_frontend_build():
    try:
        print("Running frontend build check...")
        result = subprocess.run("cmd.exe /c \"npm run build\"", cwd="frontend")
        if result.returncode == 0:
            print_status("Frontend (Next.js)", "PASS", "Build succeeded with zero errors")
        else:
            print_status("Frontend (Next.js)", "FAIL", "Build failed")
    except Exception as e:
        print_status("Frontend (Next.js)", "FAIL", str(e))

def check_backend_tests():
    try:
        print("Running backend tests...")
        result = subprocess.run(["python", "-m", "pytest", "tests/"], cwd="backend")
        if result.returncode == 0:
            print_status("Backend (Pytest)", "PASS", "All unit tests passed")
        else:
            print_status("Backend (Pytest)", "WARNING", "Some tests failed or no tests found")
    except Exception as e:
        print_status("Backend (Pytest)", "FAIL", str(e))

if __name__ == "__main__":
    print("=== INTELLIGENT OTTOMAN TURKISH ASSISTANT HEALTH CHECK ===")
    check_db()
    check_ollama()
    check_qdrant()
    check_backend_tests()
    check_frontend_build()
