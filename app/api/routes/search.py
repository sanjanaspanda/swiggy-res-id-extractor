import sys
import os
from typing import Optional

sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.search_service import SwiggySearchService

router = APIRouter()
search_service = SwiggySearchService()


class SearchRequest(BaseModel):
    name: str
    location: str


class SearchResponse(BaseModel):
    url: Optional[str] = ""
    dineout_only: bool = False
    not_found: bool = False
    error: Optional[str] = None


@router.post("/search", response_model=SearchResponse)
async def search_restaurant(request: SearchRequest):
    result = await search_service.find_restaurant_url(request.name, request.location)

    # Check if result is a dict (new format) or str (legacy fallback, though we updated service)
    if isinstance(result, dict):
        response = SearchResponse()
        response.url = result.get("url")
        response.dineout_only = result.get("dineout_only", False)
        response.not_found = result.get("not_found", False)
        response.error = result.get("error")

        if response.not_found or not response.url:
            # Ensure consistency if not_found is true
            response.not_found = True
            if not response.error:
                response.error = "Restaurant not found"

        return response

    # Fallback for string response (should not happen with new service)
    response = SearchResponse()
    if (
        not result
        or "No Results" in result
        or "Page Not Found" in result
        or "No Suitable Link Found" in result
    ):
        response.not_found = True
        response.error = result if result else "Restaurant not found"
        return response

    if result.startswith("Error"):
        raise HTTPException(status_code=500, detail=result)

    if "dineout" in result.lower():
        response.dineout_only = True

    response.url = result
    return response
