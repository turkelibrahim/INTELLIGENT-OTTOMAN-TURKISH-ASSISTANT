import os
import sys
import time
import base64
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv("backend/.env")

api_key = os.getenv("NVIDIA_API_KEY")
if not api_key:
    print("No NVIDIA API key found")
    exit(1)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

image_path = Path(__file__).parent.parent / "backend" / "uploads" / "originals" / "175" / "175_230f03eb.jpg"
if not image_path.exists():
    print(f"Image not found at {image_path}")
    exit(1)

base64_image = encode_image(image_path)
model_name = "meta/llama-3.2-11b-vision-instruct"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

prompt = (
    "Sen bir Osmanlı paleografyası uzmanısın. Lütfen bu görüntüdeki Osmanlıca metni tam ve doğru bir şekilde, "
    "Milli Eğitim Bakanlığı veya TDK transkripsiyon kurallarına göre Türkçe Latin alfabesine aktar. "
    "Sadece okunmuş metni ver, açıklama yapma."
)

payload = {
    "model": model_name,
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        }
    ],
    "max_tokens": 1024,
    "temperature": 0.0
}

print(f"Testing {model_name} on NVIDIA API...", flush=True)
start_time = time.perf_counter()
try:
    response = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload, timeout=60)
    duration = time.perf_counter() - start_time
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success! Time: {duration:.2f}s")
        print("\n--- Output ---")
        print(result["choices"][0]["message"]["content"])
        print("-------------")
    else:
        print(f"Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"Exception occurred: {e}")
