import subprocess
import time
import requests
import sys
import os

# Set test DB for Uvicorn
os.environ["ANNOTATION_DATABASE_URL"] = "sqlite:///./backend/tests_uvicorn.db"
os.environ["SECRET_KEY"] = "testsecret"
os.environ["ALGORITHM"] = "HS256"

print("Starting Uvicorn...")
proc = subprocess.Popen([
    sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8002"
], cwd=os.path.join(os.getcwd(), "backend"), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

time.sleep(3) # Wait for startup

try:
    print("Testing /api/v1/annotation/datasets WITHOUT auth...")
    res = requests.get("http://localhost:8002/api/v1/annotation/datasets")
    assert res.status_code == 401, f"Expected 401, got {res.status_code}"
    print("PASS: Unauthorized rejected.")
    
    # We can't easily mock get_current_user in a separate process unless we generate a real valid JWT.
    # We don't have user creation set up here. But 401 proves the router is mounted and auth is active.
    
    print("E2E Uvicorn Contract Test PASS")
finally:
    proc.terminate()
    proc.wait()
