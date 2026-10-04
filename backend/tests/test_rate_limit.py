import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_rate_limit_exceeded():
    # Health endpoint rate limit is 100/minute. 
    # To test without making 101 requests, we can just assume slowapi is working or mock it, 
    # or make a fast loop. 
    # Let's make 105 requests to /health with a unique IP
    responses = []
    headers = {"X-Forwarded-For": "192.168.100.100"}
    for _ in range(105):
        responses.append(client.get("/health", headers=headers))
    
    # At least one should be 429
    status_codes = [r.status_code for r in responses]
    
    # Reset limiter to avoid breaking other tests
    from app.main import limiter
    limiter._storage.reset()
    
    assert 429 in status_codes
