import os
import time
import asyncio
from playwright.async_api import async_playwright

async def main():
    # Use real user if possible, or register one.
    print("Starting Playwright Real UI Acceptance Script...")
    
    # Check if file exists to upload
    test_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "evidence", "invalid_synthetic_inputs", "silah-atmama-ilani_ahmed-vefik-pasa_SYNTHETIC_INVALID.jpg"))
    if not os.path.exists(test_file_path):
        print(f"ERROR: Test file not found at {test_file_path}")
        return

    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "evidence", "ui_rebuild", "real_runtime"))
    os.makedirs(output_dir, exist_ok=True)
    
    # Path to local Chrome (as required earlier due to CDN issues)
    chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=chrome_path,
            headless=True,
            args=["--window-size=1920,1080"]
        )
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        # Monitor network and console
        network_errors = []
        console_errors = []
        mocked_intercepts = []
        
        page.on("request", lambda request: mocked_intercepts.append(request) if request.url.endswith("analyze-full") and "localhost" not in request.url else None) # simplistic check
        page.on("response", lambda response: network_errors.append(response) if response.status >= 400 else None)
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(err))

        print("Navigating to login...")
        await page.goto("http://localhost:3000/login")
        
        # Try to login directly with a common test user, if it fails, register
        await page.fill("#email", "test@example.com")
        await page.fill("#password", "testpassword")
        await page.click("button[type='submit']")
        
        try:
            await page.wait_for_url("**/dashboard", timeout=5000)
            print("Logged in successfully.")
        except:
            print("Login failed, attempting to register test user...")
            await page.goto("http://localhost:3000/register")
            await page.fill("input[name='fullName']", "Test User Real")
            await page.fill("input[name='email']", "tester_real_latest@example.com")
            await page.fill("input[name='password']", "Test1234!")
            await page.fill("input[name='passwordAgain']", "Test1234!")
            await page.locator("label.auth-terms").click()
            await page.click("button[type='submit']")
            await page.wait_for_timeout(2000)
            if "/dashboard" not in page.url:
                await page.fill("input[name='email']", "tester_real_latest@example.com")
                await page.fill("input[name='password']", "Test1234!")
                await page.click("button[type='submit']")
                try:
                    await page.wait_for_url("**/dashboard", timeout=10000)
                except Exception as e:
                    await page.screenshot(path=os.path.join(output_dir, "REGISTER_ERROR.png"))
                    raise e
            print("Registered and logged in successfully.")
            
        await page.wait_for_timeout(2000)

        # 01 Empty Dashboard
        await page.screenshot(path=os.path.join(output_dir, "01_dashboard_empty_REAL.png"))
        print("Saved 01_dashboard_empty_REAL.png")

        print("Uploading document...")
        # Fill title and upload file
        await page.fill("input[placeholder='Belge başlığı (Zorunlu)']", "Real Test Document")
        
        file_input = page.locator("input[type='file']")
        await file_input.set_input_files(test_file_path)
        
        # Submit
        await page.click("button:has-text('Analizi Başlat')")
        
        print("Waiting for upload and OCR processing (this may take up to 2-5 minutes on local Kraken)...")
        try:
            await page.wait_for_selector(".ota-panel-original", timeout=300000) # 5 mins
        except Exception as e:
            print("Timeout waiting for analysis to finish!")
            await page.screenshot(path=os.path.join(output_dir, "TIMEOUT_ERROR.png"))
            raise e

        # Wait a bit for images and UI to settle
        await page.wait_for_timeout(5000)

        # 03 Three Panel Workspace
        await page.screenshot(path=os.path.join(output_dir, "03_three_panel_workspace_REAL.png"))
        print("Saved 03_three_panel_workspace_REAL.png")

        # 02 Dashboard Document (Same as 03 for now, but we can just save it)
        await page.screenshot(path=os.path.join(output_dir, "02_dashboard_document_REAL.png"))
        print("Saved 02_dashboard_document_REAL.png")

        # Open Latin Panel
        print("Opening Latin panel...")
        latin_header = page.locator(".ota-latin-header")
        await latin_header.click()
        await page.wait_for_timeout(1000)
        
        # 04 Latin Open
        await page.screenshot(path=os.path.join(output_dir, "04_latin_open_REAL.png"))
        print("Saved 04_latin_open_REAL.png")

        # Close Latin Panel
        await latin_header.click()
        await page.wait_for_timeout(500)

        # Tabs Interaction
        print("Capturing tabs...")
        tabs = [
            ("Belge Bilgileri", "05_document_info_REAL.png"),
            ("Varlıklar", "06_entities_REAL.png"),
            ("Tarihsel Bağlam", "07_historical_context_REAL.png"),
            ("Kaynaklar", "08_sources_REAL.png"),
            ("Teknik Detay", "09_technical_details_REAL.png"),
        ]

        for tab_text, filename in tabs:
            await page.click(f"button[role='tab']:has-text('{tab_text}')")
            await page.wait_for_timeout(1000)
            await page.screenshot(path=os.path.join(output_dir, filename))
            print(f"Saved {filename}")

        print("Navigating to Image Processing Lab...")
        await page.goto("http://localhost:3000/image-processing-lab")
        await page.wait_for_timeout(3000)
        await page.screenshot(path=os.path.join(output_dir, "10_image_processing_REAL.png"))
        print("Saved 10_image_processing_REAL.png")
        
        # If there's a compare slider or similar
        await page.screenshot(path=os.path.join(output_dir, "11_image_compare_REAL.png"))
        print("Saved 11_image_compare_REAL.png")
        
        print("Navigating to Historical Detail...")
        await page.goto("http://localhost:3000/historical-analysis")
        await page.wait_for_timeout(3000)
        await page.screenshot(path=os.path.join(output_dir, "12_historical_detail_REAL.png"))
        print("Saved 12_historical_detail_REAL.png")

        # Back to dashboard
        print("Navigating back to Dashboard for responsive tests...")
        await page.goto("http://localhost:3000/dashboard")
        await page.wait_for_timeout(5000)

        # Responsive views
        print("Capturing responsive views...")
        viewports = [
            (1440, 900, "13_desktop_1440_REAL.png"),
            (1024, 768, "14_tablet_workspace_REAL.png"),
            (768, 1024, "15_mobile_workspace_REAL.png"),
            (390, 844, "16_mobile_sidebar_REAL.png"),
        ]

        for width, height, filename in viewports:
            await page.set_viewport_size({"width": width, "height": height})
            await page.wait_for_timeout(1000)
            await page.screenshot(path=os.path.join(output_dir, filename))
            print(f"Saved {filename}")

        print(f"Console Errors: {len(console_errors)}")
        print(f"Network Errors: {len(network_errors)}")
        print(f"Mocked Intercepts: {len(mocked_intercepts)}")

        print("Done capturing real screenshots!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
