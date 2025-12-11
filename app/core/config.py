import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Learning Platform"
    API_V1_STR: str = "/api/v1"
    
    # SQLite
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./sql_app.db"

    # Neo4j
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")

    # Milvus
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT: str = os.getenv("MILVUS_PORT", "19530")
    MILVUS_COLLECTION: str = "learning_resources"

    # OpenAI / LLM
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL: str = "moonshot-v1-8k"

    class Config:
        case_sensitive = True
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
