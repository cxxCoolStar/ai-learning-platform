import logging
from typing import List, Any
from langchain_core.documents import Document
from app.db.neo4j import neo4j_driver
from app.db.milvus import get_milvus_conn
from pymilvus import Collection
from app.rag_services.vector_indexing import VectorIndexingService # Reuse embedding logic

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self):
        self.vector_service = VectorIndexingService() # To get embeddings
        self.driver = neo4j_driver

    def search(self, query: str, strategy: str = "hybrid", top_k: int = 5) -> List[Document]:
        """
        Main search entry point
        """
        vectors_docs = []
        graph_docs = []
        
        if strategy in ["hybrid", "combined"]:
            vectors_docs = self.vector_search(query, top_k)
            
        if strategy in ["graph", "combined"]:
            graph_docs = self.graph_search(query, top_k)
            
        # Deduplicate by content/ID
        seen = set()
        results = []
        for doc in graph_docs + vectors_docs:
            sig = doc.metadata.get("id") or doc.page_content[:50]
            if sig not in seen:
                seen.add(sig)
                results.append(doc)
                
        return results[:top_k]

    def vector_search(self, query: str, k: int) -> List[Document]:
        try:
            embedding = self.vector_service.embeddings.embed_query(query)
            
            col = Collection(self.vector_service.collection_name)
            col.load()
            
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            res = col.search(
                data=[embedding],
                anns_field="vector",
                param=search_params,
                limit=k,
                output_fields=["text", "resource_id", "type"]
            )
            
            docs = []
            for hits in res:
                for hit in hits:
                    docs.append(Document(
                        page_content=hit.entity.get("text"),
                        metadata={
                            "id": hit.id,
                            "resource_id": hit.entity.get("resource_id"),
                            "type": hit.entity.get("type"),
                            "score": hit.score,
                            "source": "vector"
                        }
                    ))
            return docs
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def graph_search(self, query: str, k: int) -> List[Document]:
        """
        Simple 1-hop traversal based on keyword matching for now.
        Can be enhanced with the complex 'GraphQuery' logic from examples later.
        """
        cypher = """
        CALL db.index.fulltext.queryNodes("resource_fulltext", $query + '*') YIELD node, score
        MATCH (node)-[r]-(related)
        RETURN node, collect(related) as relations, score
        ORDER BY score DESC LIMIT $k
        """
        # Note: Needs a fulltext index created first
        
        # Fallback: simple title match
        cypher_simple = """
        MATCH (r:Resource)
        WHERE toLower(r.title) CONTAINS toLower($query) OR toLower(r.summary) CONTAINS toLower($query)
        OPTIONAL MATCH (r)-[:TEACHES]->(c:Concept)
        OPTIONAL MATCH (r)-[:USES]->(t:TechStack)
        RETURN r.title as title, 
               r.summary as summary, 
               collect(c.name) as concepts, 
               collect(t.name) as stack
        LIMIT $k
        """
        
        docs = []
        try:
            with self.driver.get_session() as session:
                result = session.run(cypher_simple, {"query": query, "k": k})
                for record in result:
                    content = f"Resource: {record['title']}\nSummary: {record['summary']}\nConcepts: {record['concepts']}\nTech: {record['stack']}"
                    docs.append(Document(
                        page_content=content,
                        metadata={"source": "graph"}
                    ))
            return docs
        except Exception as e:
            logger.error(f"Graph search failed: {e}")
            return []
