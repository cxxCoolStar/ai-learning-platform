from sqlalchemy import Column, String, DateTime, Text
from app.db.session import Base
import json

class Resource(Base):
    __tablename__ = "resources"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    url = Column(String)
    type = Column(String, index=True)
    summary = Column(Text)
    author = Column(String)
    published_at = Column(DateTime)
    recommended_reason = Column(Text, nullable=True) # Added field
    
    # Storing lists as JSON strings for simplicity in SQLite
    concepts_json = Column(Text, default="[]")
    tech_stack_json = Column(Text, default="[]")

    @property
    def concepts(self):
        return json.loads(self.concepts_json)

    @concepts.setter
    def concepts(self, value):
        self.concepts_json = json.dumps(value)

    @property
    def tech_stack(self):
        return json.loads(self.tech_stack_json)

    @tech_stack.setter
    def tech_stack(self, value):
        self.tech_stack_json = json.dumps(value)

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(String, primary_key=True, index=True)
    resource_id = Column(String, index=True)
    vote_type = Column(String) # 'like' or 'dislike'
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime)
