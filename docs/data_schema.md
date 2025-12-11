# Data Schema Recommendations

To build a "Premium" and "Intelligent" platform, you should store much deeper metadata than just standard link info. Here is the recommended schema strategy:

## 1. Core Metadata (The Basics)
Stored in **Neo4j (Properties)** and **PostgreSQL/SQLite** (if used for admin).

| Field | Type | Description |
|-------|------|-------------|
| `title` | String | Original title of the resource. |
| `url` | String | Source link. |
| `original_url` | String | If it's a mirror or repost. |
| `platform` | Enum | GitHub, Medium, YouTube, Arxiv, Twitter/X. |
| `author_name` | String | Primary author. |
| `published_at` | DateTime | When it was created. |
| `updated_at` | DateTime | Last modification time. |
| `crawled_at` | DateTime | When our system last synced it. |

## 2. Platform-Specific Metrics (Social Proof)
Use these to sort by "Trending" or "High Quality".

| Field | Description |
|-------|-------------|
| `social_score` | A normalized 0-100 score based on platform metrics. |
| `github_stars` | For GitHub repos. |
| `github_forks` | For GitHub repos. |
| `youtube_views` | For Videos. |
| `youtube_likes` | For Videos. |
| `article_claps` | For Medium/Blog posts. |

## 3. AI-Generated Insights (The "Smart" Layer)
**Crucial for the Chatbot and Search**. We use the LLM to extract these during crawling.

| Field | Type | Description |
|-------|------|-------------|
| `summary` | String | A concise 1-paragraph summary of the content (Markdown). |
| `key_takeaways` | List[String] | Bullet points of the most important info. |
| `difficulty_level` | Enum | `Beginner`, `Intermediate`, `Advanced`, `Expert`. |
| `estimated_time` | String | "15 min read" or "10 min coding". |
| `quality_score` | Float | AI-evaluated quality (based on depth, clarity, code quality). |
| `tech_stack_detected`| List[String]| (For code) E.g., `["PyTorch", "FastAPI", "React"]`. |
| `prerequisites` | List[String] | What concepts users need to know *before* this. |

## 4. Graph Structure (Nodes & Relationships)
**This is the most valuable part for your Graph RAG.**

### Nodes
- **`Resource`**: The central item.
- **`Concept`**: Abstract ideas (e.g., "Attention Mechanism", "RLHF").
- **`Tool`**: Concrete software (e.g., "Docker", "LangChain").
- **`Author`**: Person or Organization.

### Relationships
- `(Resource)-[:TEACHES]->(Concept)`: "This video explains Transformer."
- `(Resource)-[:USES]->(Tool)`: "This repo uses LangChain."
- `(Resource)-[:REQUIRES]->(Concept)`: "This article assumes you know Python."
- `(Resource)-[:REFERENCES]->(Resource)`: "This tweet discusses that paper."
- `(Author)-[:CREATED]->(Resource)`

## 5. Vector Data (For Semantic Search)
Stored in **Milvus**.

- **`content_embedding`**: Vector representation of the full text/summary.
- **`chunk_vectors`**: Vectors for individual segments (for long articles/videos).

---

## Example JSON Representation

```json
{
  "id": "res_123",
  "title": "Building RAG with LangChain",
  "type": "Code",
  "metrics": {
    "stars": 1200,
    "quality_ai_score": 9.2
  },
  "ai_analysis": {
    "summary": "A comprehensive guide to...",
    "difficulty": "Intermediate",
    "concepts": ["RAG", "Vector DB"],
    "stack": ["Python", "LangChain"]
  },
  "graph_connections": {
    "requires": ["Python Basics"],
    "related_to": ["res_456"] // Another wrapper library
  }
}
```
