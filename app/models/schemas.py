from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# --- Resource Schemas ---
class ResourceBase(BaseModel):
    title: str
    url: str
    type: str # Code, Article, Video
    summary: Optional[str] = None
    author: Optional[str] = "Unknown"
    published_at: Optional[datetime] = None
    recommended_reason: Optional[str] = None # Added field

class ResourceCreate(ResourceBase):
    concepts: List[str] = []
    tech_stack: List[str] = []

class ResourceResponse(ResourceBase):
    id: str
    concepts: List[str] = []
    tech_stack: List[str] = []
    
    class Config:
        from_attributes = True

class FeedbackCreate(BaseModel):
    vote_type: str # 'like' or 'dislike'
    reason: Optional[str] = None

# --- Chat Schemas ---
class ChatRequest(BaseModel):
    message: str
    history: List[dict] = [] # [{"role": "user", "content": "..."}]

class ChatResponse(BaseModel):
    answer: str
    sources: List[ResourceResponse] = []
    strategy_used: str
    suggested_questions: List[str] = [] # Added suggested questions

# --- Settings Schemas ---
class NotificationSettings(BaseModel):
    email: str
    notify_on_new_code: bool = True
    notify_on_new_article: bool = True
    notify_on_new_video: bool = True
    frequency: str = "daily" # realtime, daily, weekly
