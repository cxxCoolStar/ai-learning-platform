import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.sql_models import Resource
from app.rag_services.retrieval import RetrievalService
from app.rag_services.vector_indexing import VectorIndexingService

def check_db():
    db = SessionLocal()
    try:
        # Search for claude-mem in SQL
        print("Checking SQL database for 'claude-mem'...")
        resources = db.query(Resource).filter(
            (Resource.title.ilike("%claude-mem%")) | 
            (Resource.summary.ilike("%claude-mem%"))
        ).all()
        
        if resources:
            print(f"Found {len(resources)} resources in SQL:")
            for r in resources:
                print(f" - {r.title} (ID: {r.id})")
                print(f"   Summary: {r.summary}")
                print(f"   URL: {r.url}")
        else:
            print("No 'claude-mem' resources found in SQL.")
            
    finally:
        db.close()

def check_rag():
    print("\nChecking RAG retrieval for 'claude-mem'...")
    service = RetrievalService()
    query = "claude-mem"
    results = service.search(query, top_k=5)
    
    if results:
        print(f"Found {len(results)} results from RAG:")
        for doc in results:
            print(f" - {doc.metadata.get('title')} (Source: {doc.metadata.get('source')}, Score: {doc.metadata.get('score')})")
    else:
        print("No results returned by RAG.")

if __name__ == "__main__":
    check_db()
    check_rag()
