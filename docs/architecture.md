# System Architecture & Design Rationale

## 1. Why use a Graph Database (Neo4j)?

The decision to incorporate a Graph Database (Neo4j) alongside Vector (Milvus) and Relational storage is based on the specific nature of an **AI Learning Platform**.

### 1.1. Highly Interconnected Knowledge
Learning resources are rarely isolated. They form a "Knowledge Graph":
- **Hierarchical Concepts**: `LangChain` $\rightarrow$ `LLM Frameworks` $\rightarrow$ `Python` $\rightarrow$ `Programming`.
- **Dependencies**: A "RAG Tutorial" *requires* understanding of "Embeddings" and "Vector DBs".
- **Cross-References**: Analysis of a *Repo* (Code) often references a *Paper* (Article).

**Relational DB (SQL)** struggles with these arbitrary depth relationships (requiring complex recursive JOINs).
**Graph DB** handles them natively: `(Tutorial)-[:REQUIRES]->(Concept)`.

### 1.2. Graph RAG (Retrieval Augmented Generation)
Standard RAG retrieves documents based on *semantic similarity* (Vector Search). Graph RAG enhances this by retrieving based on *structural relationships*.

**Example Query**: *"How do I build a RAG app using Python?"*
- **Vector Search**: Finds documents containing "RAG", "Python", "Build".
- **Graph RAG**:
    1. Finds node `Concept: RAG`.
    2. Traverses `[:USED_BY]` to find `Tool: LangChain`.
    3. Traverses `[:HAS_EXAMPLE]` to find `Repo: LangChain-Demo`.
    4. Returns the *Repo* even if it doesn't explicitly mention "How to build" in its description, because it is structurally connected.

This aligns with the reference `examples/rag_modules` which implements **Multi-hop Traversal** and **Knowledge Subgraph Extraction**.

### 1.3. Intelligent Recommendations
Graphs enable powerful recommendation algorithms:
- *"Users who learnt `FastAPI` also learnt `Pydantic`"* (Collaborative Filtering on Graph).
- *"Show me videos that explain the concepts used in this code repository"* (Content-based Graph Traversal).

## 2. Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Fact Store** | **Neo4j** | Stores Entities (Resource, Author, Concept) and Relations. |
| **Vector Store** | **Milvus** | Stores Embeddings of resource content for semantic search. |
| **Backend** | **FastAPI** | Orchestrates the Logic, Crawlers, and API. |
| **Analyst** | **LLM (OpenAI/Kimi)** | "Intelligent Query Router" decides whether to use Graph or Vector search. |

## 3. Suitability Conclusion
**Yes, this project is highly suitable for a Graph Database.** 
While simpler lists can be managed with SQL, the goal of an "AI Learning Platform" with an "Intelligent Chatbot" benefits significantly from understanding the *relationships* between diverse resources (Code, Articles, Video).
