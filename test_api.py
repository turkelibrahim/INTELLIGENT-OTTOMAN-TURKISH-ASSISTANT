import requests
import json

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AQ.Ab8RN6LxAPDYjtnC2UGoMysranGo_fy9tMpkN19qMNSLzl3BHg"

payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": "hi"
                }
            ]
        }
    ]
}

response = requests.post(url, json=payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
