import pandas as pd
import asyncio
import io
import uuid
from typing import Dict
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    WebSocket,
    BackgroundTasks,
    HTTPException,
)
from fastapi.websockets import WebSocketDisconnect
from app.services.search_service import SwiggySearchService
from app.services.extract_service import SwiggyExtractService

router = APIRouter()

# In-memory store for active jobs (in production, use Redis/DB)
# Structure: job_id -> { "status": str, "total": int, "processed": int, "results": DataFrame, "queue": asyncio.Queue }
jobs: Dict[str, dict] = {}

search_service = SwiggySearchService()
extract_service = SwiggyExtractService()


async def process_row(row, job_id: str):
    """
    Process a single row: Search -> Extract -> Update Result
    """
    name = row.get("Restaurant Name", "")
    location = row.get("Location", "")

    # Initialize result with original data
    result = row.copy()
    result["status"] = "Processing"
    result["dineout_only"] = False
    result["not_found"] = False
    result["swiggy_url"] = ""
    result["promo_codes"] = ""
    result["99_store_items"] = ""
    result["offer_items"] = ""
    result["rating"] = ""
    result["total_ratings"] = ""

    # Notify start
    job = jobs.get(job_id)
    if not job:
        return result

    try:
        # 1. Search
        await job["queue"].put(
            {
                "type": "update",
                "data": {"id": str(row.name), "status": "Searching", "name": name},
            }
        )

        search_result = await search_service.find_restaurant_url(name, location)

        # Handle dict response (new format) or legacy string
        search_result_obj = search_result
        url = ""
        is_dineout = False
        not_found = False
        error_msg = None

        if isinstance(search_result_obj, dict):
            url = str(search_result_obj.get("url", ""))
            is_dineout = bool(search_result_obj.get("dineout_only", False))
            not_found = bool(search_result_obj.get("not_found", False))
            error_msg = search_result_obj.get("error")
        else:
            # Fallback for string response
            url = str(search_result_obj)
            is_dineout = "dineout" in url.lower()
            not_found = (
                not url
                or "No Results" in url
                or "Page Not Found" in url
                or "Error" in url
                or "No Suitable Link Found" in url
            )
            error_msg = url if not_found else None

        if not_found or not url:
            result["swiggy_url"] = ""
            result["status"] = "Not Found"
            result["not_found"] = True
            result["error"] = error_msg or "Restaurant not found"
            await job["queue"].put(
                {
                    "type": "update",
                    "data": {
                        "id": str(row.name),
                        "status": "Failed",
                        "error": result["error"],
                    },
                }
            )
            return result

        result["swiggy_url"] = url
        result["dineout_only"] = is_dineout

        # Skip extraction if dineout only
        if is_dineout:
            result["status"] = "Completed"
            await job["queue"].put(
                {
                    "type": "update",
                    "data": {
                        "id": str(row.name),
                        "status": "Completed",
                        "dineout_only": True,
                        "swiggy_url": url,
                        "name": name,
                    },
                }
            )
            return result

        # 2. Extract
        await job["queue"].put(
            {
                "type": "update",
                "data": {"id": str(row.name), "status": "Extracting", "url": url},
            }
        )

        data = await extract_service.extract_data(url)

        # Retry logic for empty data (same as frontend)
        if (
            not data.get("rating")
            and not data.get("promo_codes")
            and not data.get("99_store_items")
        ):
            await asyncio.sleep(2)
            data = await extract_service.extract_data(url)

        if "error" in data:
            result["status"] = "Partial Error"
            result["error"] = data["error"]
        else:
            result["status"] = "Completed"
            result["promo_codes"] = ", ".join(data.get("promo_codes", []))
            result["99_store_items"] = ", ".join(data.get("99_store_items", []))

            # Flatten offer items for CSV columns
            offer_items_data = data.get("offer_items", {})
            result["offer_items"] = (
                ""  # Keep this for UI summary if needed, or build it
            )

            offer_str_parts = []
            for cat, items in offer_items_data.items():
                items_str = ", ".join(items)
                offer_str_parts.append(f"{cat}: {items_str}")

                # Add dynamic column for CSV
                # Santize key
                safe_key = f"offer_{cat.replace(' ', '_').replace('%', 'pct')}"
                result[safe_key] = items_str

            result["offer_items"] = " | ".join(offer_str_parts)

            result["rating"] = data.get("rating", "")
            result["total_ratings"] = data.get("total_ratings", "")

        # Prepare update data for frontend (keep it simple for UI)
        # We send the full result dict to the UI, so the dynamic keys will be there too if we want
        # But strictly for UI "items" state, we might just need the standard fields + offer_items dict

        # update_data needs to be serializable and useful for the table
        update_data = {
            "id": str(row.name),
            "status": "Completed",
            "rating": result["rating"],
            "total_ratings": result["total_ratings"],
            "promo_codes": result["promo_codes"],
            "items_99": result["99_store_items"],
            "offer_items": result["offer_items"],  # This is the summary string
            "offer_items_raw": data.get(
                "offer_items", {}
            ),  # Pass raw obj for UI to render
            "dineout_only": result["dineout_only"],
            "not_found": result["not_found"],
            "swiggy_url": result["swiggy_url"],
        }

        await job["queue"].put(
            {
                "type": "update",
                "data": update_data,
            }
        )

    except Exception as e:
        result["status"] = "Error"
        result["error"] = str(e)
        await job["queue"].put(
            {
                "type": "update",
                "data": {"id": str(row.name), "status": "Error", "error": str(e)},
            }
        )

    return result


async def run_bulk_job(job_id: str, df: pd.DataFrame):
    job = jobs[job_id]
    semaphore = asyncio.Semaphore(8)  # Concurrency limit

    async def sem_task(row):
        async with semaphore:
            return await process_row(row, job_id)

    tasks = []
    # Convert rows to dicts but keep index for ID
    for idx, row in df.iterrows():
        row_with_id = row.to_dict()
        row_with_id["name"] = idx  # Use index as ID
        # Pass the Series object to allow .name access or construct a dict
        # Better: construct a dict with index attached
        row_series = row.copy()
        row_series.name = idx
        tasks.append(sem_task(row_series))

    results = await asyncio.gather(*tasks)

    # Save results
    job["results"] = pd.DataFrame(results)
    job["status"] = "completed"
    await job["queue"].put({"type": "complete"})


@router.post("/upload")
async def upload_csv(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file type")

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid CSV format: {str(e)}. Please ensure fields with commas are enclosed in quotes.",
        )

    # Normalize headers
    required = ["Restaurant Name", "Location"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

    job_id = str(uuid.uuid4())

    # Initialize job
    jobs[job_id] = {
        "status": "processing",
        "total": len(df),
        "results": None,
        "queue": asyncio.Queue(),
    }

    # Start background task
    background_tasks.add_task(run_bulk_job, job_id, df)

    # Return initial list of items for UI to populate
    items = []
    for idx, row in df.iterrows():
        items.append(
            {
                "id": str(idx),
                "name": row.get("Restaurant Name", "Unknown"),
                "location": row.get("Location", ""),
                "status": "Pending",
            }
        )

    return {"job_id": job_id, "items": items}


async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()

    job = jobs.get(job_id)
    if not job:
        await websocket.close(code=4004, reason="Job not found")
        return

    try:
        while True:
            # Wait for message from queue
            msg = await job["queue"].get()
            await websocket.send_json(msg)

            if msg["type"] == "complete":
                break
    except WebSocketDisconnect:
        pass


@router.get("/download/{job_id}")
async def download_results(job_id: str):
    job = jobs.get(job_id)
    if not job or job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not ready or found")

    df = job["results"]
    stream = io.StringIO()
    df.to_csv(stream, index=False)

    from fastapi.responses import StreamingResponse

    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=swiggy_results.csv"
    return response
