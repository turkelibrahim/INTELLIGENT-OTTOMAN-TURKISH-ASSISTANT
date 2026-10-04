import asyncio
import json
from playwright.async_api import async_playwright

MOCK_RESULT = {
  "document": {
    "document_id": 1,
    "filename": "ornek_ferman.pdf",
    "document_type": "Ferman"
  },
  "ocr": {
    "confidence": 92.5,
    "ottoman_text": "Ø¨Ø³Ù… Ø§Ù„Ù„Ù‡ Ø§Ù„Ø±Ø­Ù…Ù† Ø§Ù„Ø±Ø­ÙŠÙ…\n...",
    "lines": [
      {
        "line_id": "L1",
        "line_no": 1,
        "text": "بسم الله الرحمن الرحيم",
        "ocr_text": "بسم الله الرحمن الرحيم",
        "confidence": 99.1
      }
    ]
  },
  "transliteration": {
    "text": "Bismillahirrahmanirrahim",
    "lines": [
      {
        "line_id": "L1",
        "line_no": 1,
        "text": "Bismillahirrahmanirrahim",
        "confidence": 95.0
      }
    ]
  },
  "modern_turkish": {
    "text": "Rahman ve Rahim olan Allah'ın adıyla",
    "lines": [
      {
        "line_id": "L1",
        "line_no": 1,
        "text": "Rahman ve Rahim olan Allah'ın adıyla",
        "modern_text": "Rahman ve Rahim olan Allah'ın adıyla",
        "confidence": 90.0
      }
    ]
  },
  "confidence": {
    "overall": 93.0,
    "ocr": 92.5,
    "transliteration": 95.0,
    "modern_turkish": 90.0
  },
  "entities": [
    {
      "entity_id": "e1",
      "entity_type": "PERSON",
      "text": "Sultan Süleyman",
      "confidence": 98.0
    }
  ],
  "metadata": {
    "date_normalized": "1520",
    "summary": "Örnek bir ferman özeti."
  }
}

MOCK_CONTEXT = {
  "documentId": 1,
  "filename": "ornek_ferman.pdf",
  "analysisResult": MOCK_RESULT,
  "savedAt": "2026-08-20T00:00:00.000Z",
  "source": "document-analyze-full"
}

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe", headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # We must go to the site first to set sessionStorage
        await page.goto("http://localhost:3000/")
        await page.wait_for_timeout(1000)
        
        payload = json.dumps(MOCK_CONTEXT).replace("'", "\\'")
        # Ensure it is set
        await page.evaluate(f"sessionStorage.setItem('active-document-context:v1', '{payload}')")
        val = await page.evaluate("sessionStorage.getItem('active-document-context:v1')")
        print("Value set in sessionStorage:", "YES" if val else "NO")
        
        await page.goto("http://localhost:3000/dashboard")
        await page.wait_for_timeout(3000)
        
        await page.screenshot(path="evidence/ui_rebuild/02_dashboard_document.png", full_page=True)
        print("02_dashboard_document.png taken!")
        
        await browser.close()

asyncio.run(main())
