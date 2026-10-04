import asyncio
import aiohttp
import os
import time
from PIL import Image

API_BASE = "http://127.0.0.1:8000/api/v1"
CONCURRENT_REQUESTS = 15

async def register_and_login():
    async with aiohttp.ClientSession() as session:
        # Try register
        email = f"stress_test_{int(time.time())}@example.com"
        password = "password123"
        
        async with session.post(f"{API_BASE}/auth/register", json={
            "email": email,
            "username": email.split("@")[0],
            "password": password,
            "full_name": "Stress Test"
        }) as resp:
            pass
            
        async with session.post(f"{API_BASE}/auth/login", json={
            "email": email,
            "password": password
        }) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["access_token"]
            else:
                text = await resp.text()
                print(f"Auth failed: {repr(text)}")
                return None

async def submit_job(session, token, image_path, i):
    headers = {"Authorization": f"Bearer {token}"}
    data = aiohttp.FormData()
    data.add_field('file',
                   open(image_path, 'rb'),
                   filename=f"test_image_{i}.png",
                   content_type='image/png')
    data.add_field('title', f'Stress Test Doc {i}')
    
    print(f"[{i}] Submitting document...")
    
    async with session.post(f"{API_BASE}/document/analyze", data=data, headers=headers) as resp:
        if resp.status in (200, 201, 202):
            result = await resp.json()
            job_id = result.get("job_id")
            if not job_id:
                job_id = result.get("id")
            print(f"[{i}] Job started with ID: {job_id}")
            return job_id
        else:
            print(f"[{i}] Failed to submit: {await resp.text()}")
            return None

async def poll_job(session, token, job_id, i):
    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()
    while True:
        async with session.get(f"{API_BASE}/document/jobs/{job_id}", headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                status = data.get("status")
                print(f"[{i}] Job {job_id} status: {status}")
                if status in ("COMPLETED", "FAILED", "ERROR"):
                    elapsed = time.time() - start_time
                    print(f"[{i}] Finished with status {status} in {elapsed:.2f}s")
                    return status
            else:
                print(f"[{i}] Error polling: {await resp.text()}")
                return "ERROR"
        await asyncio.sleep(2)

async def main():
    print("Preparing dummy image...")
    img_path = "test_image.png"
    img = Image.new('RGB', (100, 100), color = 'white')
    img.save(img_path)
    
    print("Authenticating...")
    token = await register_and_login()
    if not token:
        print("Could not obtain auth token. Is the backend running?")
        return
        
    print(f"Starting stress test with {CONCURRENT_REQUESTS} concurrent requests...")
    
    start_total = time.time()
    
    async with aiohttp.ClientSession() as session:
        # Submit all jobs concurrently
        submit_tasks = [submit_job(session, token, img_path, i) for i in range(CONCURRENT_REQUESTS)]
        job_ids = await asyncio.gather(*submit_tasks)
        
        valid_job_ids = [(idx, jid) for idx, jid in enumerate(job_ids) if jid]
        
        print(f"Successfully submitted {len(valid_job_ids)} jobs. Polling for completion...")
        if len(valid_job_ids) == 0:
            print("No valid jobs to poll.")
            return
            
        poll_tasks = [poll_job(session, token, jid, idx) for idx, jid in valid_job_ids]
        results = await asyncio.gather(*poll_tasks)
        
        completed = results.count("COMPLETED")
        failed = results.count("FAILED") + results.count("ERROR")
        
        total_time = time.time() - start_total
        print("="*40)
        print("STRESS TEST RESULTS")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Successful jobs: {completed}")
        print(f"Failed/Error jobs: {failed}")
        print("="*40)

if __name__ == "__main__":
    asyncio.run(main())
