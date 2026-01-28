import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from app.services.extract_service import SwiggyExtractService

router = APIRouter()
extract_service = SwiggyExtractService()


class ExtractRequest(BaseModel):
    url: str


class ExtractResponse(BaseModel):
    promo_codes: List[str]
    items_99: List[str]
    offer_items: Dict[str, List[str]] = {}
    rating: Optional[str] = ""
    total_ratings: Optional[str] = ""


@router.post("/extract", response_model=ExtractResponse)
async def extract_data(request: ExtractRequest):
    result = await extract_service.extract_data(request.url)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return ExtractResponse(
        promo_codes=result.get("promo_codes", []),
        items_99=result.get("99_store_items", []),
        offer_items=result.get("offer_items", {}),
        rating=result.get("rating", ""),
        total_ratings=result.get("total_ratings", ""),
    )
