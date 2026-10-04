import os
import requests

model_dir = "backend/models/translation/opus-mt-tr-en"
os.makedirs(model_dir, exist_ok=True)

files = [
    "config.json",
    "source.spm",
    "target.spm",
    "vocab.json",
    "tokenizer_config.json",
    "pytorch_model.bin",
    "generation_config.json"
]

base_url = "https://huggingface.co/Helsinki-NLP/opus-mt-tr-en/resolve/main/"

for file in files:
    url = base_url + file
    out_path = os.path.join(model_dir, file)
    if os.path.exists(out_path):
        print(f"Skipping {file}, already exists.")
        continue
    
    print(f"Downloading {file} from {url}...")
    response = requests.get(url, stream=True)
    if response.status_code == 404:
        print(f"File {file} not found, skipping.")
        continue
        
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    with open(out_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024*1024):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    print(f"Downloaded {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB for {file}", end='\r')
    print(f"\nCompleted {file}")

print("Download complete.")
