import logging
import time
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
# from langchain_openai import OpenAIEmbeddings # Commented out
from langchain_core.embeddings import FakeEmbeddings # Use Fake for now

from app.core.config import get_settings
from pymilvus import Collection, connections, utility, CollectionSchema, FieldSchema, DataType

logger = logging.getLogger(__name__)

class VectorIndexingService:
    """
    Vector Indexing Service using Milvus
    """
    
    def __init__(self, collection_name: str = "learning_resources"):
        self.settings = get_settings()
        self.collection_name = collection_name
        # Using FakeEmbeddings to bypass OpenAI Auth
        self.embeddings = FakeEmbeddings(size=1536)
        # self.embeddings = OpenAIEmbeddings(
        #     model="text-embedding-3-small",
        #     openai_api_key=self.settings.OPENAI_API_KEY,
        #     base_url=self.settings.OPENAI_BASE_URL
        # )
        
        self.ensure_collection()

    def ensure_collection(self):
        """Ensure Milvus collection exists"""
        try:
            connections.connect(host=self.settings.MILVUS_HOST, port=self.settings.MILVUS_PORT)
            
            # Check schema update
            if utility.has_collection(self.collection_name):
                # Simple check if schema matches (simplified)
                # If we need to migrate schema (add 'url' and 'title'), best way for demo is to drop and recreate
                # In prod, we'd create a new collection and migrate data.
                # Let's drop if it exists to apply new schema (WARNING: Data loss)
                # Or just use dynamic field if enabled?
                # Let's just drop and recreate for this dev session since we have seed data script.
                utility.drop_collection(self.collection_name)
                logger.info(f"Dropped existing collection {self.collection_name} to apply schema update.")

            if not utility.has_collection(self.collection_name):
                logger.info(f"Creating collection: {self.collection_name}")
                
                fields = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
                    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1536), # OpenAI embedding dim
                    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=8192),
                    FieldSchema(name="resource_id", dtype=DataType.VARCHAR, max_length=64),
                    FieldSchema(name="type", dtype=DataType.VARCHAR, max_length=32),
                    # Added fields
                    FieldSchema(name="url", dtype=DataType.VARCHAR, max_length=1024),
                    FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512)
                ]
                
                schema = CollectionSchema(fields, "AI Learning Platform Resources")
                col = Collection(self.collection_name, schema)
                
                # Create Index
                index_params = {
                    "metric_type": "COSINE",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 128}
                }
                col.create_index(field_name="vector", index_params=index_params)
                logger.info("Collection created and indexed")
            else:
                Collection(self.collection_name).load()
                
        except Exception as e:
            logger.error(f"Milvus init failed: {e}")

    def add_documents(self, documents: List[Document]):
        """Add documents to Milvus"""
        if not documents:
            return
            
        texts = [d.page_content for d in documents]
        vectors = self.embeddings.embed_documents(texts)
        
        data = [
            [d.metadata.get("id") for d in documents], # id
            vectors, # vector
            [d.page_content[:8000] for d in documents], # text (truncated)
            [d.metadata.get("resource_id", "") for d in documents], # resource_id
            [d.metadata.get("type", "unknown") for d in documents], # type
            [d.metadata.get("url", "")[:1024] for d in documents], # url
            [d.metadata.get("title", "Untitled")[:512] for d in documents], # title
        ]
        
        try:
            col = Collection(self.collection_name)
            col.insert(data)
            col.flush()
            logger.info(f"Inserted {len(documents)} vectors into Milvus")
        except Exception as e:
            logger.error(f"Vector insertion failed: {e}")
