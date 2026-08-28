from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List

from ..engine.threat_intel_provider import registry
from ..schemas.threat_intel import ThreatIntelResult, ThreatIntelProviderHealth

router = APIRouter(tags=["threat-intel"])

class LookupRequest(BaseModel):
    indicator: str
    indicator_type: str

@router.get("/providers", response_model=List[ThreatIntelProviderHealth])
async def get_providers():
    return await registry.get_health()

@router.post("/lookup", response_model=List[ThreatIntelResult])
async def manual_lookup(req: LookupRequest):
    results = await registry.lookup(req.indicator, req.indicator_type.upper())
    if not results:
        raise HTTPException(status_code=404, detail="No intelligence found for this indicator")
    return results
