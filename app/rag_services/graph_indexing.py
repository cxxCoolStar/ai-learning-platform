import logging
import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_core.documents import Document
from app.db.neo4j import neo4j_driver
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class GraphIndexingService:
    """
    Graph Indexing Service for Learning Resources
    
    Nodes:
    - Resource (Code, Article, Video, Forum)
    - Concept (e.g., "RAG", "Attention")
    - TechStack (e.g., "Python", "React")
    - Author
    
    Relationships:
    - (Resource)-[:TEACHES]->(Concept)
    - (Resource)-[:USES]->(TechStack)
    - (Resource)-[:AUTHORED_BY]->(Author)
    """
    
    def __init__(self, llm_client=None):
        self.driver = neo4j_driver
        self.llm_client = llm_client # For future extraction logic
        
        # Initialize constraints
        self._create_constraints()

    def _create_constraints(self):
        """Create Neo4j constraints to ensure data integrity"""
        queries = [
            "CREATE CONSTRAINT resource_id IF NOT EXISTS FOR (r:Resource) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT tech_name IF NOT EXISTS FOR (t:TechStack) REQUIRE t.name IS UNIQUE",
            "CREATE CONSTRAINT author_name IF NOT EXISTS FOR (a:Author) REQUIRE a.name IS UNIQUE"
        ]
        
        try:
            with self.driver.get_session() as session:
                for q in queries:
                    session.run(q)
            logger.info("Graph constraints initialized")
        except Exception as e:
            logger.error(f"Failed to create constraints: {e}")

    def index_resource(self, resource_data: Dict[str, Any]):
        """
        Index a single resource into the Graph
        
        Expected resource_data:
        {
            "id": "...",
            "title": "...",
            "url": "...",
            "type": "Code/Article/Video",
            "summary": "...",
            "author": "...",
            "concepts": ["RAG", "LLM"],
            "tech_stack": ["Python", "FastAPI"],
            "published_at": "..."
        }
        """
        query = """
        MERGE (r:Resource {id: $id})
        SET r.title = $title,
            r.url = $url,
            r.type = $type,
            r.summary = $summary,
            r.published_at = $published_at,
            r.updated_at = datetime()
            
        // Process Author
        MERGE (a:Author {name: $author})
        MERGE (r)-[:AUTHORED_BY]->(a)
        
        // Process Concepts
        FOREACH (c_name IN $concepts | 
            MERGE (c:Concept {name: c_name})
            MERGE (r)-[:TEACHES]->(c)
        )
        
        // Process Tech Stack
        FOREACH (t_name IN $tech_stack | 
            MERGE (t:TechStack {name: t_name})
            MERGE (r)-[:USES]->(t)
        )
        """
        
        params = {
            "id": resource_data.get("id", str(uuid.uuid4())),
            "title": resource_data.get("title", "Untitled"),
            "url": resource_data.get("url", ""),
            "type": resource_data.get("type", "Article"),
            "summary": resource_data.get("summary", ""),
            "published_at": resource_data.get("published_at", datetime.now().isoformat()),
            "author": resource_data.get("author", "Unknown"),
            "concepts": resource_data.get("concepts", []),
            "tech_stack": resource_data.get("tech_stack", [])
        }
        
        try:
            with self.driver.get_session() as session:
                session.run(query, params)
            logger.info(f"Indexed resource: {params['title']}")
            return True
        except Exception as e:
            logger.error(f"Failed to index resource {params['id']}: {e}")
            return False

    def close(self):
        pass # Driver is managed globally
