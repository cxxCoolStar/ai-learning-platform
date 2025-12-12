import sys
import os
import logging
from sqlalchemy import func

# Add project root to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.sql_models import Resource
from app.rag_services.vector_indexing import VectorIndexingService
from pymilvus import Collection, connections, utility

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_sync():
    print("--- Checking SQL vs Vector DB Synchronization ---")
    
    # 1. SQL DB Count
    db = SessionLocal()
    try:
        sql_count = db.query(func.count(Resource.id)).scalar()
        print(f"SQL Resource Count: {sql_count}")
        
        # Get list of SQL IDs for more detailed check (limit to first 10 for display)
        sql_ids = [r.id for r in db.query(Resource.id).limit(5).all()]
        print(f"Sample SQL IDs: {sql_ids}")
    except Exception as e:
        print(f"Error querying SQL: {e}")
        sql_count = -1
    finally:
        db.close()

    # 2. Milvus Vector DB Count
    vector_service = VectorIndexingService()
    # Ensure connection is active (VectorIndexingService init does connect, but let's be sure)
    
    milvus_count = -1
    try:
        if utility.has_collection(vector_service.collection_name):
            col = Collection(vector_service.collection_name)
            # Flush to ensure newly inserted data is visible
            col.flush()
            milvus_count = col.num_entities
            print(f"Milvus Vector Count: {milvus_count}")
            
            # Note: Milvus count might be higher than SQL count because of Chunking.
            # Each SQL Resource (article/video) can be split into multiple Chunks in Milvus.
            # So exact equality is NOT expected if chunking is on.
            # Instead, we should check if unique `resource_id`s in Milvus match SQL count.
            
            # Let's query distinct resource_ids from Milvus (if possible efficiently, otherwise sample)
            # Milvus doesn't support "SELECT DISTINCT" easily in search.
            # We can try to query all resource_ids (if count is small) or just rely on the logic explanation.
            
            print("\nAnalysis:")
            if milvus_count >= sql_count and sql_count > 0:
                print("✅ Vector count >= SQL count. This is expected due to Chunking strategy.")
                print(f"   Average chunks per resource: {milvus_count / sql_count:.2f}")
            elif sql_count == 0 and milvus_count == 0:
                print("✅ Both databases are empty.")
            else:
                print("⚠️  Mismatch detected that might indicate missing vectors.")
                
        else:
            print(f"Milvus collection {vector_service.collection_name} does not exist.")
    except Exception as e:
        print(f"Error querying Milvus: {e}")

if __name__ == "__main__":
    check_sync()
