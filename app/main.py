import sys
import os

# Add the project root directory to the Python path
# This handles both running as module (python -m app.main) and running script directly (python app/main.py)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import search, extract, bulk

app = FastAPI(title="Swiggy Scraper API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(extract.router, prefix="/api/v1", tags=["Extract"])
app.include_router(bulk.router, prefix="/api/v1/bulk", tags=["Bulk"])

# Websocket route directly on app to avoid router prefix issues
app.add_api_websocket_route("/api/v1/bulk/ws/{job_id}", bulk.websocket_endpoint)


@app.get("/")
async def root():
    return {"message": "Swiggy Scraper API is running. Visit /docs for documentation."}


def main():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
