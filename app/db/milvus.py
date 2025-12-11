from pymilvus import connections, utility
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

class MilvusConnection:
    _connected = False

    @classmethod
    def connect(cls):
        if cls._connected:
            return

        settings = get_settings()
        try:
            connections.connect(
                alias="default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT
            )
            cls._connected = True
            logger.info(f"Connected to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise

    @classmethod
    def disconnect(cls):
        if cls._connected:
            connections.disconnect("default")
            cls._connected = False
            logger.info("Disconnected from Milvus")

def get_milvus_conn():
    MilvusConnection.connect()
    return connections
