import logging
import time
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
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
        # Use real OpenAI Embeddings for proper semantic search
        try:
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=self.settings.OPENAI_API_KEY,
                base_url=self.settings.OPENAI_BASE_URL
            )
            # Test embedding to check if API is accessible
            self.embeddings.embed_query("test")
        except Exception as e:
            logger.warning(f"OpenAI Embeddings failed (likely 403/Quota): {e}. Falling back to FakeEmbeddings.")
            self.embeddings = FakeEmbeddings(size=1536)
        
        self.ensure_collection()

    def ensure_collection(self):
        """Ensure Milvus collection exists"""
        try:
            connections.connect(host=self.settings.MILVUS_HOST, port=self.settings.MILVUS_PORT)
            
            # Check schema update
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

    def reset_collection(self):
        """Drop and recreate collection (for seeding)"""
        try:
            connections.connect(host=self.settings.MILVUS_HOST, port=self.settings.MILVUS_PORT)
            if utility.has_collection(self.collection_name):
                utility.drop_collection(self.collection_name)
                logger.info(f"Dropped collection {self.collection_name}")
            self.ensure_collection()
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")

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
