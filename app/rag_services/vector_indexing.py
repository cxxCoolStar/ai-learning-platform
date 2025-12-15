import logging
import time
from typing import List, Dict, Any, Optional
from functools import lru_cache

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_openai import OpenAIEmbeddings # Replaced with HuggingFace
from langchain_core.embeddings import FakeEmbeddings 

from app.core.config import get_settings
from pymilvus import Collection, connections, utility, CollectionSchema, FieldSchema, DataType

logger = logging.getLogger(__name__)

@lru_cache()
def get_embeddings_model():
    logger.info("Initializing HuggingFace Embeddings (BAAI/bge-small-zh-v1.5)...")
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-zh-v1.5",
            model_kwargs={'device': 'cpu'}, # Use 'cuda' if GPU available
            encode_kwargs={'normalize_embeddings': True}
        )
        # Test embedding
        embeddings.embed_query("test")
        logger.info("HuggingFace Embeddings initialized successfully.")
        return embeddings
    except Exception as e:
        logger.error(f"Embeddings connection failed: {e}")
        raise e

class VectorIndexingService:
    """
    Vector Indexing Service using Milvus
    """
    
    def __init__(self, collection_name: str = "learning_resources"):
        self.settings = get_settings()
        self.collection_name = collection_name
        
        # Use Cached Embeddings
        self.embeddings = get_embeddings_model()
        
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
                    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=512), # BGE-small-zh dimension
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
