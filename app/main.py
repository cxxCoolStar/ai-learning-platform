from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.db.neo4j import neo4j_driver
from app.db.milvus import MilvusConnection
from app.db.session import engine, Base
from app.models import sql_models # Import models to register them
from app.services.scheduler import SchedulerService # Import Scheduler

scheduler_service = SchedulerService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Create tables
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Error creating SQL tables: {e}")

    try:
        neo4j_driver.connect()
    except Exception as e:
        print(f"Warning: Failed to connect to Neo4j: {e}")

    try:
        MilvusConnection.connect()
    except Exception as e:
        print(f"Warning: Failed to connect to Milvus: {e}")
        
    # Start Scheduler
    try:
        scheduler_service.start()
    except Exception as e:
        print(f"Error starting scheduler: {e}")
        
    yield
    # Shutdown
    try:
        neo4j_driver.close()
    except:
        pass
    try:
        MilvusConnection.disconnect()
    except:
        pass

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import ingest, resources, chat
app.include_router(ingest.router, prefix=f"{settings.API_V1_STR}/ingest", tags=["ingest"])
app.include_router(resources.router, prefix=f"{settings.API_V1_STR}/resources", tags=["resources"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])

@app.get("/")
def read_root():
    return {"message": "Welcome to AI Learning Platform API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
