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
    result["status_text"] = "Processing"
    result["swiggy_id"] = "NA"
    result["promos"] = ""
    result["promo_codes"] = ""  # Kept for UI
    result["promos"] = ""
    result["promo_codes"] = ""  # Kept for UI
    result["offer_items_formatted"] = ""
    result["rating"] = ""
    result["total_ratings"] = ""
    result["99_store_items"] = ""
    result["offer_items"] = {}

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
            # Try to extract ID from URL even if not found (e.g. from generic error page URL)
            # The search service might return a URL that is technically "Not Found" but has ID

            # Check search_result_obj for a potential URL if 'url' var is empty
            potential_url = url
            if not potential_url and isinstance(search_result_obj, dict):
                potential_url = search_result_obj.get("url", "")
            if not potential_url:
                # Check error msg if it looks like a url
                if error_msg and "http" in str(error_msg):
                    potential_url = str(error_msg)

            swiggy_id = "NA"
            if potential_url:
                import re

                match = re.search(r"(\d+)$", potential_url)
                if match:
                    swiggy_id = match.group(1)

            result["swiggy_id"] = swiggy_id
            result["swiggy_url"] = potential_url or ""

            result["status"] = "Not Found"
            result["not_found"] = True
            result["error"] = error_msg or "Restaurant not found"
            result["status_text"] = "Not on Swiggy"
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
                        "status_text": "Only Dineout",
                        "swiggy_id": "NA",
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

        # Retry logic: Try up to 3 times if data is missing
        max_retries = 3
        data = {}

        for attempt in range(max_retries):
            # Update status if retrying
            if attempt > 0:
                await job["queue"].put(
                    {
                        "type": "update",
                        "data": {
                            "id": str(row.name),
                            "status": f"Extracting (try {attempt + 1}/{max_retries})",
                            "url": url,
                        },
                    }
                )
                await asyncio.sleep(2)  # Backoff

            data = await extract_service.extract_data(url)

            # Check if we have useful data
            has_data = (
                data.get("rating")
                or data.get("promo_codes")
                or data.get("99_store_items")
            )

            # Also failing if explicit error (unless it's not found, which is terminal)
            if "error" in data:
                if "not found" in data["error"].lower():
                    break  # Don't retry if really not found
                # Otherwise might be network error, retry might help?
                pass

            if has_data:
                break

        # If loop finishes without data, we use whatever we got (likely empty or error)

        if "error" in data:
            result["status"] = "Partial Error"
            result["error"] = data["error"]
            if "not found" in data["error"].lower():
                result["status"] = "Not Found"
                result["not_found"] = True
                result["status_text"] = "Not on Swiggy"
        else:
            # Extract ID from URL
            # Expected format: ...-rest12345 or ...-12345
            import re

            swiggy_id = "NA"
            match = re.search(r"(\d+)$", url)
            if match:
                swiggy_id = match.group(1)

            result["swiggy_id"] = swiggy_id
            result["status_text"] = "On Swiggy"

            result["status"] = "Completed"
            # Join with newlines for Excel
            result["promo_codes"] = ", ".join(
                data.get("promo_codes", [])
            )  # Kept for UI
            result["promos"] = "\n".join(data.get("promo_codes", []))

            # Formatted offer string for Excel
            offer_str_parts = []
            offer_items_data = data.get("offer_items", {})
            for cat, items in offer_items_data.items():
                items_str = ", ".join(items)
                offer_str_parts.append(f"{cat}: {items_str}")

            result["offer_items_formatted"] = "\n".join(offer_str_parts)
            result["offer_items"] = " | ".join(offer_str_parts)

            result["rating"] = data.get("rating", "")
            result["total_ratings"] = data.get("total_ratings", "")
            result["99_store_items"] = "\n".join(data.get("99_store_items", []))

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
            "offer_items_display": result["offer_items"],  # This is the summary string
            "offer_items": data.get("offer_items", {}),
            "status_text": result.get("status_text", "Processing"),
            "swiggy_id": result.get("swiggy_id", "NA"),
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
    semaphore = asyncio.Semaphore(5)  # Concurrency limit

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

    # Prepare final DataFrame for Excel export
    final_df = job["results"].copy()

    # Handle missing columns if job failed early
    for col in ["status_text", "swiggy_id", "promos", "offer_items_formatted"]:
        if col not in final_df.columns:
            final_df[col] = ""

    # Map status_text for Not Found items if not already set correctly in process_row error flow
    # (In process_row we only set it for success/dineout, need to ensure error cases have it)
    def get_status(row):
        if row.get("status_text"):
            return row.get("status_text")
        if row.get("not_found"):
            return "Not on Swiggy"
        return "Not on Swiggy"  # Default fallback for errors

    # Just ensure the column exists and populate if empty
    final_df["status_text"] = final_df.apply(
        lambda x: x["status_text"]
        if x.get("status_text")
        else ("Not on Swiggy" if x.get("not_found") else "Error"),
        axis=1,
    )

    # Rename columns to match requirements
    final_df = final_df.rename(
        columns={
            "Restaurant Name": "Restaurant Name",
            "Location": "Location",
            "swiggy_id": "Swiggy Restaurant ID",
            "status_text": "Status",
            "promos": "Promos",
            "offer_items_formatted": "Offer Items",
            "rating": "Rating",
            "total_ratings": "Total Ratings",
            "99_store_items": "99 Store Items",
            "dineout_only": "Dineout Only",
        }
    )
    print(final_df.columns)

    # Select only required columns
    cols_to_keep = [
        "Restaurant Name",
        "Location",
        "Swiggy Restaurant ID",
        "Status",
        "Promos",
        "Offer Items",
        "Rating",
        "Total Ratings",
        "99 Store Items",
    ]
    # Filter only existing columns to be safe
    cols_to_keep = [c for c in cols_to_keep if c in final_df.columns]

    final_df = final_df[cols_to_keep]

    stream = io.BytesIO()
    # Use xlsxwriter or default (openpyxl)
    final_df.to_excel(stream, index=False, engine="openpyxl")

    from fastapi.responses import StreamingResponse

    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response.headers["Content-Disposition"] = "attachment; filename=swiggy_results.xlsx"
    return response
