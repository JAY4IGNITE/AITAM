import os
import asyncio
from celery import Celery
from urllib.parse import urlparse
import logging
from .playwright_script import run_sandbox_analysis
from policies.url_safety import is_safe_url

# Configure Celery
redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery(
    "threatlens_sandbox",
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=2, # Limit concurrent browsers to save memory
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

logger = logging.getLogger("sandbox_worker")

@celery_app.task(name="analyze_url", bind=True, max_retries=1)
def analyze_url_task(self, investigation_id: str, url: str):
    logger.info(f"Received sandbox task for investigation {investigation_id} -> {url}")
    
    # 1. SSRF Safety Check BEFORE spinning up browser
    if not is_safe_url(url):
        logger.warning(f"SSRF Policy Violation for {url}")
        return {
            "investigation_id": investigation_id,
            "status": "failed",
            "error": "URL violates safety policy (SSRF prevention)",
            "events": []
        }
    
    # 2. Run Playwright (Synchronous wrapper around Async Playwright)
    try:
        # Run the async playwright script in a synchronous Celery task
        results = asyncio.run(run_sandbox_analysis(url))
        results["investigation_id"] = investigation_id
        results["status"] = "completed"
        return results
    except Exception as e:
        logger.error(f"Sandbox failed for {url}: {e}")
        return {
            "investigation_id": investigation_id,
            "status": "failed",
            "error": str(e),
            "events": []
        }
