import os
import requests
from dotenv import load_dotenv

load_dotenv("backend/.env")

api_key = os.getenv("NVIDIA_API_KEY")
if not api_key:
    print("No NVIDIA API key found")
    exit(1)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "application/json"
}

response = requests.get("https://integrate.api.nvidia.com/v1/models", headers=headers)
if response.status_code == 200:
    models = response.json().get("data", [])
    vision_models = []
    for model in models:
        # Check if the model ID implies vision, multimodal, etc.
        name = model.get("id", "").lower()
        if "vision" in name or "multimodal" in name or "vlm" in name or "llama-3.2-90b-vision" in name or "pixtral" in name or "nemotron" in name:
            vision_models.append(model["id"])
    
    print("Found potential Vision models:")
    for vm in vision_models:
        print(f" - {vm}")
    
    # Actually just print a sample of all models to not miss anything
    print("\nAll models sample:")
    for model in models[:10]:
        print(f" - {model['id']}")
else:
    print(f"Error fetching models: {response.status_code} - {response.text}")
