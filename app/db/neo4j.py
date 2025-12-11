from neo4j import GraphDatabase
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

class Neo4jDriver:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jDriver, cls).__new__(cls)
            cls._instance.driver = None
        return cls._instance

    def connect(self):
        settings = get_settings()
        if self.driver is None:
            try:
                self.driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
                )
                logger.info("Connected to Neo4j")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                raise

    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Closed Neo4j connection")

    def get_session(self):
        if not self.driver:
            self.connect()
        return self.driver.session()

neo4j_driver = Neo4jDriver()

def get_neo4j_session():
    session = neo4j_driver.get_session()
    try:
        yield session
    finally:
        session.close()
