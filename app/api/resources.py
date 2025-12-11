from typing import List, Optional, Dict
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from datetime import datetime
import uuid
from app.models.schemas import ResourceResponse, FeedbackCreate
from app.db.session import get_db
from app.models.sql_models import Resource, Feedback

router = APIRouter()

@router.post("/{resource_id}/feedback")
async def create_feedback(
    resource_id: str,
    feedback: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """
    Submit feedback (like/dislike) for a resource
    """
    # Verify resource exists
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
        
    db_feedback = Feedback(
        id=str(uuid.uuid4()),
        resource_id=resource_id,
        vote_type=feedback.vote_type,
        reason=feedback.reason,
        created_at=datetime.now()
    )
    
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    return {"status": "success", "message": "Feedback submitted"}

@router.get("/stats")
async def get_resource_stats(db: Session = Depends(get_db)) -> Dict[str, int]:
    """
    Get counts for each resource type
    """
    # Count all
    total_count = db.query(func.count(Resource.id)).scalar()
    
    # Count by type
    # Group by type and count
    type_counts = db.query(Resource.type, func.count(Resource.id)).group_by(Resource.type).all()
    
    stats = {
        "all": total_count,
        "code": 0,
        "article": 0,
        "video": 0,
        "forum": 0
    }
    
    for r_type, count in type_counts:
        if r_type:
            key = r_type.lower()
            if key in stats:
                stats[key] = count
            else:
                # Handle unexpected types if necessary, or just ignore
                pass
                
    return stats

@router.get("/", response_model=List[ResourceResponse])
async def list_resources(
    skip: int = 0,
    limit: int = 20,
    type: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of resources from SQLite (replacing Neo4j for simplicity/demo)
    """
    query = db.query(Resource)

    if type and type.lower() != 'all':
        query = query.filter(Resource.type == type)

    if search:
        search_lower = f"%{search.lower()}%"
        query = query.filter(
            or_(
                Resource.title.ilike(search_lower),
                Resource.summary.ilike(search_lower)
            )
        )

    if tag:
        # Simple tag filtering using string contains (since tags are stored as JSON string)
        # Note: This is not efficient for large datasets but works for demo/sqlite
        tag_like = f'%"{tag}"%'
        query = query.filter(
            or_(
                Resource.concepts_json.ilike(tag_like),
                Resource.tech_stack_json.ilike(tag_like)
            )
        )
    
    query = query.order_by(Resource.published_at.desc())
    resources = query.offset(skip).limit(limit).all()

    return resources
