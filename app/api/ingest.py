from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from app.services.ingestion import IngestionPipeline

router = APIRouter()

class IngestRequest(BaseModel):
    url: str

@router.post("/ingest")
async def ingest_resource(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Trigger async ingestion for a URL.
    """
    pipeline = IngestionPipeline()
    
    # Run in background to avoid blocking
    background_tasks.add_task(pipeline.ingest_url, request.url)
    
    return {"message": f"Ingestion started for {request.url}", "status": "processing"}
