import logging
import json
from typing import List, Any, Tuple
from langchain_core.documents import Document
from app.db.neo4j import neo4j_driver
from app.db.milvus import get_milvus_conn
from pymilvus import Collection
from app.rag_services.vector_indexing import VectorIndexingService # Reuse embedding logic

from app.models.sql_models import Resource
from app.db.session import SessionLocal
from app.core.config import get_settings
from langchain_openai import ChatOpenAI
from langchain_community.retrievers import BM25Retriever

logger = logging.getLogger(__name__)

import re

class RetrievalService:
    def __init__(self):
        self.vector_service = VectorIndexingService() # To get embeddings
        self.settings = get_settings()
        self.driver = None
        try:
            self.driver = neo4j_driver
        except Exception:
            logger.warning("Neo4j driver not available. Graph search will be disabled.")
            
        # Initialize LLM for query expansion
        try:
            self.llm = ChatOpenAI(
                model=self.settings.LLM_MODEL,
                api_key=self.settings.OPENAI_API_KEY,
                base_url=self.settings.OPENAI_BASE_URL
            )
        except Exception:
            self.llm = None
            logger.warning("LLM not available for RetrievalService. Keyword extraction will use fallback.")

    def extract_query_keywords(self, query: str) -> Tuple[List[str], List[str]]:
        """
        Extract entity-level and topic-level keywords using LLM, similar to hybrid_retrieval.py example.
        """
        if not self.llm:
            # Fallback: simple split
            parts = query.split()
            return parts, parts

        prompt = f"""
        Analyze the following query and extract keywords for retrieval.
        Query: {query}
        
        Return JSON with:
        - "entity_keywords": specific entities, tools, libraries, authors (e.g. LangChain, Kimi, Anthropic)
        - "topic_keywords": general concepts, themes (e.g. Agents, RAG, Long-running)
        
        JSON format only.
        """
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            return data.get("entity_keywords", []), data.get("topic_keywords", [])
        except Exception as e:
            logger.warning(f"Keyword extraction failed: {e}")
            return [query], [query]

    def bm25_search(self, query: str, k: int) -> List[Document]:
        """
        Perform BM25 sparse vector search on all SQL resources.
        This compensates for poor Dense Vector performance (FakeEmbeddings).
        """
        db = SessionLocal()
        try:
            # Fetch all resources (title + summary)
            # Note: In production, this index should be persistent, not built on every request.
            # For this demo scale (<1000 items), building on fly is fine (~ms).
            resources = db.query(Resource).all()
            if not resources:
                return []
            
            # Prepare docs for BM25
            bm25_docs = []
            res_map = {}
            for r in resources:
                content = f"{r.title}\n{r.summary}"
                doc = Document(page_content=content, metadata={"id": r.id})
                bm25_docs.append(doc)
                res_map[r.id] = r
                
            # Initialize Retriever
            retriever = BM25Retriever.from_documents(bm25_docs)
            retriever.k = k
            
            # Search
            results = retriever.invoke(query)
            
            # Enrich results
            final_docs = []
            for doc in results:
                r = res_map.get(doc.metadata["id"])
                if r:
                    final_docs.append(Document(
                        page_content=doc.page_content,
                        metadata={
                            "id": r.id,
                            "resource_id": r.id,
                            "type": r.type,
                            "title": r.title,
                            "url": r.url,
                            "source": "bm25",
                            "score": 1.0 # BM25 doesn't return normalized score easily in this wrapper
                        }
                    ))
            return final_docs
            
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []
        finally:
            db.close()

    def search(self, query: str, strategy: str = "hybrid", top_k: int = 5) -> List[Document]:
        """
        Main search entry point with Hybrid Strategy (BM25 + Vector + Graph)
        """
        logger.info(f"Starting Hybrid Search for: {query}")
        
        # 1. Extract Keywords (Query Expansion)
        entity_keywords, topic_keywords = self.extract_query_keywords(query)
        expanded_query = f"{query} {' '.join(entity_keywords)} {' '.join(topic_keywords)}"
        logger.info(f"Expanded Query: {expanded_query}")

        vectors_docs = []
        graph_docs = []
        bm25_docs = []
        
        # If Neo4j is down, force hybrid
        if strategy != "hybrid" and not self._is_graph_available():
            strategy = "hybrid"
        
        # 2. Vector Search (Dense)
        if strategy in ["hybrid", "combined"]:
            vectors_docs = self.vector_search(query, top_k) # Use original query for embedding
            
        # 3. Graph Search (Structured)
        if strategy in ["graph", "combined"]:
            # Use extracted keywords for better graph matching
            graph_docs = self.graph_search(" ".join(entity_keywords + topic_keywords), top_k)
            
        # 4. BM25 Search (Sparse) - The "Fix" for FakeEmbeddings
        # Use extracted keywords + original query
        bm25_docs = self.bm25_search(expanded_query, top_k)
            
        # 5. Fallback SQL Search (Exact Match)
        sql_docs = self.sql_search(query, top_k)
            
        # 6. Merge & Deduplicate (Round-Robin / RRF-like)
        # Priority: BM25 (High precision text) > Graph (Relations) > Vector (Semantic) > SQL
        
        all_lists = [bm25_docs, graph_docs, vectors_docs, sql_docs]
        
        # Define all_docs for hydration usage
        all_docs = bm25_docs + graph_docs + vectors_docs + sql_docs
        
        merged_results = []
        seen = set()
        
        max_len = max(len(l) for l in all_lists) if all_lists else 0
        
        for i in range(max_len):
            for doc_list in all_lists:
                if i < len(doc_list):
                    doc = doc_list[i]
                    sig = doc.metadata.get("resource_id") or doc.metadata.get("id")
                    if sig and sig not in seen:
                        seen.add(sig)
                        merged_results.append(doc)
        
        results = merged_results[:top_k]
        
        # Hydration: Collect missing URLs
        resource_ids_to_fetch = []
        
        for doc in all_docs:
            sig = doc.metadata.get("resource_id") or doc.metadata.get("id") or doc.page_content[:50]
            if sig not in seen:
                seen.add(sig)
                results.append(doc)
                
                # Check if URL is missing and we have a resource_id
                if not doc.metadata.get("url") and doc.metadata.get("resource_id"):
                    resource_ids_to_fetch.append(doc.metadata.get("resource_id"))

        # Bulk fetch missing URLs from SQL
        if resource_ids_to_fetch:
            db = SessionLocal()
            try:
                resources = db.query(Resource).filter(Resource.id.in_(resource_ids_to_fetch)).all()
                id_to_url = {res.id: res.url for res in resources}
                
                # Update docs
                for doc in results:
                    rid = doc.metadata.get("resource_id")
                    if rid and rid in id_to_url and not doc.metadata.get("url"):
                        doc.metadata["url"] = id_to_url[rid]
                        # Also append URL to page_content for context visibility? 
                        # Better to keep it in metadata and let ChatService format it.
            except Exception as e:
                logger.error(f"Failed to hydrate URLs: {e}")
            finally:
                db.close()
        
        # Fallback: SQL Search if no results found (e.g. Milvus is down or empty)
        if not results:
            logger.info("No results from Vector/Graph/SQL-Primary. Falling back to broader SQL search.")
            # Note: We already did SQL search, but maybe with stricter terms?
            # For now, if we have no results, we just return empty.
            pass
        
        # Log retrieved results
        logger.info(f"Retrieved {len(results)} docs for query: '{query}'")
        for i, doc in enumerate(results):
            logger.info(f"Doc {i+1}: {doc.metadata.get('title')} (Source: {doc.metadata.get('source')}, URL: {doc.metadata.get('url')})")
                
        return results[:top_k]

    def _is_graph_available(self) -> bool:
        if not self.driver: return False
        try:
            self.driver.verify_connectivity()
            return True
        except:
            return False

    def sql_search(self, query: str, k: int) -> List[Document]:
        """
        Keyword search in SQLite.
        Tries exact match first, then extracted English keywords if query contains Chinese.
        """
        db = SessionLocal()
        try:
            results = []
            
            # 1. Direct match (exact phrase)
            search_term = f"%{query}%"
            direct_results = db.query(Resource).filter(
                (Resource.title.ilike(search_term)) | 
                (Resource.summary.ilike(search_term))
            ).limit(k).all()
            results.extend(direct_results)
            
            # 2. If query has non-ASCII (likely Chinese) and we want to find English terms
            # Extract English words sequence
            english_phrases = re.findall(r'[a-zA-Z0-9\-\s]{4,}', query)
            for phrase in english_phrases:
                phrase = phrase.strip()
                if len(phrase) > 3: # Ignore short noise
                    term = f"%{phrase}%"
                    phrase_results = db.query(Resource).filter(
                        (Resource.title.ilike(term)) | 
                        (Resource.summary.ilike(term))
                    ).limit(k).all()
                    
                    # Dedup
                    for r in phrase_results:
                        if r.id not in [existing.id for existing in results]:
                            results.append(r)

            docs = []
            for res in results[:k]: # Limit total
                content = f"Title: {res.title}\nType: {res.type}\nSummary: {res.summary}\n"
                if res.recommended_reason:
                    content += f"Recommendation: {res.recommended_reason}"
                
                docs.append(Document(
                    page_content=content,
                    metadata={
                        "id": res.id,
                        "resource_id": res.id,
                        "type": res.type,
                        "title": res.title,
                        "url": res.url,
                        "source": "sql"
                    }
                ))
            return docs
        except Exception as e:
            logger.error(f"SQL search failed: {e}")
            return []
        finally:
            db.close()

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
                output_fields=["text", "resource_id", "type", "url", "title"] # Added url, title
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
                            "title": hit.entity.get("title", "Unknown"),
                            "url": hit.entity.get("url"), # Added URL
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
