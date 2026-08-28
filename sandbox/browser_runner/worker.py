from celery import Celery
import os

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery("sandbox_worker", broker=redis_url, backend=redis_url)

@app.task
def analyze_url_in_sandbox(url: str, investigation_id: str):
    import asyncio
    return asyncio.run(_run_playwright(url, investigation_id))

async def _run_playwright(url: str, investigation_id: str):
    from playwright.async_api import async_playwright
    
    events = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            ignore_https_errors=True,
            userAgent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Monitor requests
        page.on("request", lambda request: events.append({
            "type": "network_request",
            "url": request.url,
            "method": request.method
        }))
        
        try:
            await page.goto(url, timeout=30000, wait_until="networkidle")
            
            # Extract basic facts
            title = await page.title()
            forms = await page.locator("form").count()
            password_inputs = await page.locator("input[type='password']").count()
            
            # Screenshot (we just mock the path for the hackathon)
            screenshot_path = f"/app/artifacts/{investigation_id}_screenshot.png"
            await page.screenshot(path=screenshot_path)
            
            events.append({
                "type": "dom_analysis",
                "title": title,
                "forms_count": forms,
                "password_inputs": password_inputs
            })
            
            return {
                "status": "completed",
                "events": events,
                "screenshot": screenshot_path
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
        finally:
            await browser.close()
