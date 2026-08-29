import io
import os
import re
import base64
import logging
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from .base import BaseAgent
from ..schemas.agent_io import AgentResult
from ..models.investigation import Investigation
from ..models.agent import AgentRun, Evidence
from ..models.finding import Finding
from ..models.iocs import IOC

logger = logging.getLogger("qr_processor")

def decode_qr_image(image_input: str) -> list[str]:
    """
    Decodes QR code from either a file path, base64 string, or data URI.
    Returns list of decoded string payloads.
    """
    img = None
    try:
        # Check if base64 data URI
        if image_input.startswith("data:image"):
            base64_data = image_input.split(",")[1]
            img_bytes = base64.b64decode(base64_data)
            img = Image.open(io.BytesIO(img_bytes))
        elif os.path.exists(image_input):
            img = Image.open(image_input)
        else:
            # Try raw base64 decode
            try:
                img_bytes = base64.b64decode(image_input)
                img = Image.open(io.BytesIO(img_bytes))
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Failed to load image for QR decoding: {e}")

    results = []
    if img:
        # Try pyzbar
        try:
            from pyzbar.pyzbar import decode as pyzbar_decode
            decoded_objects = pyzbar_decode(img)
            for obj in decoded_objects:
                payload = obj.data.decode('utf-8', errors='ignore')
                if payload:
                    results.append(payload)
        except Exception as e:
            logger.warning(f"pyzbar decoding failed: {e}")

        # Fallback to OpenCV if available
        if not results:
            try:
                import cv2
                import numpy as np
                img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                detector = cv2.QRCodeDetector()
                data, bbox, _ = detector.detectAndDecode(img_cv)
                if data:
                    results.append(data)
            except Exception:
                pass

    # If input is already plain text / URL payload
    if not results and (image_input.startswith("http") or len(image_input.split()) <= 10):
        if not os.path.exists(image_input) and not image_input.startswith("data:"):
            results.append(image_input.strip())

    return results

class QRCodeProcessor(BaseAgent):
    agent_name = "qr_processor"
    agent_version = "2.0.0"
    capabilities = ["qr_decoding", "payload_classification", "quishing_detection"]

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun) -> AgentResult:
        inv = await session.get(Investigation, investigation_id)
        if not inv:
            raise ValueError("Investigation not found")

        raw_target = inv.target.strip()
        decoded_payloads = decode_qr_image(raw_target)

        findings: list[Finding] = []
        evidence_items: list[dict] = []
        primary_payload = decoded_payloads[0] if decoded_payloads else raw_target

        payload_type = "TEXT"
        if primary_payload.startswith(("http://", "https://")):
            payload_type = "URL"
        elif primary_payload.startswith("WIFI:"):
            payload_type = "WIFI_CONFIG"
        elif primary_payload.startswith("BEGIN:VCARD"):
            payload_type = "VCARD"
        elif "@" in primary_payload and "." in primary_payload:
            payload_type = "EMAIL"

        # Update investigation normalized input with extracted payload
        inv.normalized_input = primary_payload

        evidence_items.append({
            "type": "QR_PAYLOAD",
            "fact": f"Decoded QR code ({payload_type}): {primary_payload[:120]}"
        })

        # Save IOC
        session.add(IOC(
            investigation_id=investigation_id,
            ioc_type="URL" if payload_type == "URL" else "QR_PAYLOAD",
            value=primary_payload,
            source_agent=cls.agent_name,
            confidence=0.99,
            first_seen=datetime.utcnow().isoformat(),
            last_seen=datetime.utcnow().isoformat()
        ))

        # Check for Quishing risks
        if payload_type == "URL":
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="quishing",
                title="QR Code Contains Web Destination (Quishing Lure)",
                description=f"Decoded QR code routes directly to an external URL ('{primary_payload}'). Attackers use physical and digital QR codes to bypass email spam filters.",
                severity="medium",
                confidence=0.95,
                risk_contribution=25
            ))

        if findings:
            session.add_all(findings)
            for ev in evidence_items:
                session.add(Evidence(
                    investigation_id=investigation_id,
                    agent_name=cls.agent_name,
                    evidence_type=ev["type"],
                    severity="medium",
                    observed_fact=ev["fact"],
                    confidence=0.95
                ))

        return AgentResult(
            agent_name=cls.agent_name,
            agent_version=cls.agent_version,
            status="COMPLETED",
            execution_time=0.0,
            findings=[{"title": f.title, "severity": f.severity, "category": f.category} for f in findings],
            evidence=evidence_items,
            confidence=0.98,
            metadata={
                "decoded_payload": primary_payload,
                "payload_type": payload_type,
                "all_decoded": decoded_payloads
            }
        )
