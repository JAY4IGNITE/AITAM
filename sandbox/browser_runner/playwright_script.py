import asyncio
from playwright.async_api import async_playwright
import base64
import time

async def run_sandbox_analysis(url: str):
    """
    Safely opens a URL in a headless Chromium browser,
    detects login forms, and takes a screenshot.
    """
    signals = []
    has_login_form = False
    has_password_field = False
    redirect_chain = []
    screenshot_b64 = None
    
    start_time = time.time()

    async with async_playwright() as p:
        # Launch isolated chromium instance
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
        
        # Create an isolated context (no cookies shared)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            ignore_https_errors=True # Attackers often use bad certs
        )
        
        page = await context.new_page()
        
        # Track redirects
        page.on("request", lambda request: redirect_chain.append(request.url) if request.is_navigation_request() else None)
        
        try:
            # Navigate with a strict timeout (15 seconds)
            response = await page.goto(url, timeout=15000, wait_until="networkidle")
            
            # Analyze DOM for forms
            forms = await page.locator("form").count()
            if forms > 0:
                has_login_form = True
                signals.append({"type": "form_detected", "severity": "medium", "evidence": f"Found {forms} form(s) on page"})
                
            # Analyze for password fields specifically (credential harvesting)
            password_inputs = await page.locator('input[type="password"]').count()
            if password_inputs > 0:
                has_password_field = True
                signals.append({"type": "password_field_detected", "severity": "high", "evidence": "Credential harvesting risk: Password field detected"})
                
            # Take screenshot of what the victim sees
            screenshot_bytes = await page.screenshot(type="jpeg", quality=60)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
        except Exception as e:
            signals.append({"type": "sandbox_timeout_or_error", "severity": "low", "evidence": str(e)})
            
        finally:
            await browser.close()
            
    duration = time.time() - start_time
    
    return {
        "signals": signals,
        "redirect_chain": redirect_chain,
        "screenshot_base64": screenshot_b64,
        "has_login_form": has_login_form,
        "has_password_field": has_password_field,
        "duration_seconds": round(duration, 2)
    }
