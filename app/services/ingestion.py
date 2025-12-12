from dateutil import parser
import logging
import uuid
import json
from typing import List
from datetime import datetime

from app.services.crawler import CrawlerFactory
from app.rag_services.graph_indexing import GraphIndexingService
from app.rag_services.vector_indexing import VectorIndexingService
from app.db.session import SessionLocal
from app.models.sql_models import Resource, Feedback
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from sqlalchemy import desc
from app.core.config import get_settings
import html2text

logger = logging.getLogger(__name__)

class IngestionPipeline:
    def __init__(self):
        self.graph_service = GraphIndexingService()
        self.vector_service = VectorIndexingService()
        self.settings = get_settings()
        # Mocking LLM if no key provided, handled in logic
        try:
            self.llm = ChatOpenAI(
                model=self.settings.LLM_MODEL,
                api_key=self.settings.OPENAI_API_KEY,
                base_url=self.settings.OPENAI_BASE_URL
            )
        except Exception:
            self.llm = None

    def _resolve_date(self, date_str: str) -> str:
        if not date_str:
            return datetime.now().isoformat()
        try:
            return parser.parse(str(date_str)).isoformat()
        except Exception:
            return datetime.now().isoformat()

    async def ingest_url(self, url: str):
        logger.info(f"Starting ingestion for: {url}")

        # Check if resource already exists
        db = SessionLocal()
        try:
            existing = db.query(Resource).filter(Resource.url == url).first()
            if existing:
                logger.info(f"Resource already exists, skipping crawl: {url}")
                return True
        finally:
            db.close()
        
        # 1. Crawl
        crawler = CrawlerFactory.get_crawler(url)
        try:
            raw_data = await crawler.crawl(url)
        except Exception as e:
            logger.error(f"Crawl failed for {url}: {e}")
            return False

        # 2. Analyze (Extract Metadata, Tech Stack, Summary)
        analyzed_data = await self._analyze_content(raw_data)
        
        # 3. Index to SQL (Primary Metadata Storage)
        self._save_to_sql(analyzed_data)

        # 4. Index to Graph (Neo4j) - Best effort
        self.graph_service.index_resource(analyzed_data)
        
        # 5. Index to Vector (Milvus)
        # Create document chunks for the content
        # Combine summary and content for full context
        summary_text = analyzed_data.get("summary", "")
        raw_content = raw_data.get("content", "")
        
        # Determine content format and convert to Markdown if necessary
        is_markdown = False
        content_to_split = raw_content
        
        # Check if it's already markdown (e.g. from GitHub API) or needs conversion
        if analyzed_data.get("type") == "Code" or "readme" in url.lower() or raw_content.strip().startswith("#"):
            is_markdown = True
        else:
            # For HTML articles, convert to Markdown to use structural splitting
            # If raw_content is HTML (crawler usually returns text, but let's be safe if we change crawler later)
            # Actually, our Crawler currently returns text content via readability or similar.
            # If it's plain text, we can't do much structure. 
            # BUT, if we have HTML available in raw_data (we do!), let's use it.
            html_source = raw_data.get("html", "")
            if html_source and len(html_source) > 100:
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = True
                try:
                    content_to_split = h.handle(html_source)
                    is_markdown = True
                    logger.info(f"Converted HTML to Markdown for structural splitting: {url}")
                except Exception as e:
                    logger.warning(f"HTML to Markdown conversion failed: {e}")
            
        
        # Strategy: Structural Chunking (Markdown) -> Fallback to Recursive
        # 1. First, split by Markdown headers to preserve semantic structure
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        
        final_chunks = []
        
        # Always add summary as the first chunk (high value)
        if summary_text:
            final_chunks.append(Document(page_content=f"Summary: {summary_text}", metadata={"section": "Summary"}))

        if is_markdown:
            markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
            # Split main content
            md_docs = markdown_splitter.split_text(content_to_split)
            
            # 2. Then, recursively split large chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            
            for doc in md_docs:
                # If a section is too large, split it further
                if len(doc.page_content) > 1000:
                    sub_chunks = text_splitter.split_documents([doc])
                    final_chunks.extend(sub_chunks)
                else:
                    final_chunks.append(doc)
        else:
             # Fallback for plain text (Recursive only)
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            plain_chunks = text_splitter.create_documents([content_to_split])
            final_chunks.extend(plain_chunks)
        
        docs = []
        resource_id = analyzed_data.get("id", str(uuid.uuid4()))
        
        for i, chunk in enumerate(final_chunks):
            # Merge header metadata into content for context
            header_context = ""
            if "Header 1" in chunk.metadata:
                header_context += f"{chunk.metadata['Header 1']} > "
            if "Header 2" in chunk.metadata:
                header_context += f"{chunk.metadata['Header 2']} > "
            if "Header 3" in chunk.metadata:
                header_context += f"{chunk.metadata['Header 3']}"
            
            # Construct fully context-aware content
            # 1. Global Context (Title + Summary)
            doc_context = f"Document Title: {analyzed_data.get('title', 'Untitled')}\n"
            if summary_text:
                # Use first 200 chars of summary to avoid token bloat
                doc_context += f"Document Summary: {summary_text[:200]}...\n"
            
            # 2. Structural Context (Headers)
            if header_context:
                doc_context += f"Section Path: {header_context}\n"
            
            # 3. Combine with original chunk content
            content_with_context = f"{doc_context}\nContent:\n{chunk.page_content}"

            doc = Document(
                page_content=content_with_context,
                metadata={
                    "id": str(uuid.uuid4()), # Unique ID for each vector chunk
                    "resource_id": resource_id,
                    "chunk_index": i,
                    "type": analyzed_data.get("type", "Article"),
                    "title": analyzed_data.get("title", "Untitled"),
                    "url": analyzed_data.get("url", ""),
                    # Preserve markdown header metadata
                    **chunk.metadata 
                }
            )
            docs.append(doc)

        if docs:
            self.vector_service.add_documents(docs)
            logger.info(f"Indexed {len(docs)} chunks to Milvus for {url}")
        else:
            logger.warning(f"No content to index for {url}")
        
        logger.info(f"Ingestion complete for {url}")
        return True

    def _save_to_sql(self, data: dict):
        if not data.get("is_ai_related", False):
            logger.info(f"Skipping non-AI content: {data.get('url', 'unknown')}")
            return

        db = SessionLocal()
        try:
            # Check if exists
            existing = db.query(Resource).filter(Resource.url == data["url"]).first()
            if existing:
                logger.info(f"Resource already exists in SQL: {data['url']}")
                return

            resource = Resource(
                id=data["id"],
                title=data["title"],
                url=data["url"],
                type=data["type"],
                summary=data["summary"],
                author=data["author"],
                published_at=datetime.fromisoformat(data["published_at"]) if isinstance(data["published_at"], str) else data["published_at"],
                recommended_reason=data.get("recommended_reason") # Save recommended reason
            )
            resource.concepts = data["concepts"]
            resource.tech_stack = data["tech_stack"]
            
            db.add(resource)
            db.commit()
            logger.info(f"Saved to SQL: {data['title']}")
        except Exception as e:
            logger.error(f"Failed to save to SQL: {e}")
            db.rollback()
        finally:
            db.close()

    def _get_few_shot_examples(self) -> str:
        db = SessionLocal()
        try:
            # Get recent likes
            likes = db.query(Feedback, Resource).join(Resource, Feedback.resource_id == Resource.id)\
                .filter(Feedback.vote_type == "like", Feedback.reason != None)\
                .order_by(desc(Feedback.created_at)).limit(3).all()
            
            # Get recent dislikes
            dislikes = db.query(Feedback, Resource).join(Resource, Feedback.resource_id == Resource.id)\
                .filter(Feedback.vote_type == "dislike", Feedback.reason != None)\
                .order_by(desc(Feedback.created_at)).limit(3).all()
            
            if not likes and not dislikes:
                return ""

            examples_text = "\n\nUser Preferences (Few-Shot Examples):\n"
            examples_text += "Use these examples to better understand what content is valuable to the user.\n"
            
            if likes:
                examples_text += "\n[Positive Examples (Keep/Recommended)]\n"
                for feedback, resource in likes:
                    examples_text += f"- Title: {resource.title}\n  User Reason: {feedback.reason}\n"
            
            if dislikes:
                examples_text += "\n[Negative Examples (Discard/Avoid)]\n"
                for feedback, resource in dislikes:
                    examples_text += f"- Title: {resource.title}\n  User Reason: {feedback.reason}\n"
            
            return examples_text
        except Exception as e:
            logger.error(f"Failed to fetch few-shot examples: {e}")
            return ""
        finally:
            db.close()

    async def _analyze_content(self, raw_data: dict) -> dict:
        """
        Use LLM to extract structured metadata from raw text.
        Also filters non-AI content and generates recommended reason.
        """
        # Prepare input content with metadata hint to help LLM
        input_text = f"Title: {raw_data.get('title', 'Unknown')}\n"
        if raw_data.get('author') and raw_data.get('author') != 'Unknown':
            input_text += f"Extracted Author: {raw_data['author']}\n"
        input_text += f"URL: {raw_data.get('url', '')}\n\n"
        input_text += raw_data.get("content", "")[:3000] # Limit tokens
        
        few_shot_context = self._get_few_shot_examples()

        system_prompt = f"""
        Analyze the following technical content.
        
        **Filtering Criteria:**
        You are an advanced AI content filter. The user is specifically interested in **AI Application Development** (e.g., AI Agents, RAG, LLM Engineering, LangChain, LlamaIndex, OpenAI API integration, Multi-Agent Systems).
        
        **EXCLUDE** content that is primarily about:
        - Pure Machine Learning theory (e.g., backpropagation details, math-heavy papers).
        - Deep Learning model architecture research without application context.
        - General Data Science, Statistics, or Data Analysis.
        - Low-level CUDA/GPU optimization (unless directly relevant to inference serving).
        - General Web Development not related to AI integration.
        
        {few_shot_context}

        **Instructions:**
        1. Determine if this content matches the user's specific interest in AI Application Development.
        
        If it does NOT match (e.g., it's general web dev, pure ML theory, or unrelated):
        Return valid JSON with {{"is_ai_related": false}}.
        
        If it DOES match (e.g., building Agents, RAG pipelines, using LLMs):
        Extract the following and return valid JSON:
        1. "is_ai_related": true
        2. "summary": A concise summary (in Chinese).
        3. "recommended_reason": A short reason why this project/article is recommended for an AI App Developer (in Chinese).
        4. "concepts": List of main technical concepts (e.g., 'RAG', 'Embeddings', 'Agents').
        5. "tech_stack": List of tech stack involved (e.g., 'Python', 'LangChain', 'Next.js').
        6. "author": Main Author (if apparent, else 'Unknown').
        
        **Special Instruction for Social Media (Twitter/X) Posts:**
        - Since these posts often lack a formal title, please generate a **Concise and Descriptive Title** (in English) based on the content. 
        - Example: Instead of "Tweet by @user", use "Summary of OpenAI's new o1 model release".
        - Ensure the title captures the main topic.
        
        Input Content:
        """
        
        try:
            if self.llm:
                try:
                    response = await self.llm.ainvoke([
                        SystemMessage(content=system_prompt), 
                        HumanMessage(content=input_text)
                    ])
                    # Clean up response content if it contains markdown code blocks
                    content = response.content
                    if "```json" in content:
                        content = content.replace("```json", "").replace("```", "")
                    elif "```" in content:
                        content = content.replace("```", "")
                    
                    parsed = json.loads(content)
                    
                    if not parsed.get("is_ai_related", False):
                        return {"is_ai_related": False}
                    
                    # Use LLM generated title if raw title is generic for Social posts
                    final_title = raw_data.get("title", "Untitled")
                    if raw_data.get("type") == "Social" and parsed.get("title"): 
                         # Use LLM title for social posts
                         pass 
                    
                    # Resolve Author: Prefer LLM parsed, fallback to crawler extracted
                    final_author = parsed.get("author")
                    if not final_author or final_author == "Unknown":
                        final_author = raw_data.get("author", "Unknown")

                    return {
                        "is_ai_related": True,
                        "id": str(uuid.uuid4()),
                        "title": parsed.get("title", raw_data.get("title", "Untitled")), 
                        "url": raw_data["url"],
                        "type": raw_data["type"],
                        "summary": parsed.get("summary", f"AI 摘要: {raw_data.get('title')}"),
                        "recommended_reason": parsed.get("recommended_reason", f"推荐理由: 这是一个关于 {raw_data.get('title')} 的优质资源，适合深入学习 AI 技术。"),
                        "author": final_author,
                        "concepts": parsed.get("concepts", ["AI"]), 
                        "tech_stack": parsed.get("tech_stack", raw_data.get("tech_stack", ["General"])),
                        "published_at": self._resolve_date(raw_data.get("published_at"))
                    }
                except Exception as e:
                    logger.error(f"LLM analysis failed: {e}")
                    # Fallback to heuristic if LLM fails but we want to be lenient or debug
                    pass
            
            # Fallback / Mock logic if LLM not available or failed
            # Simple keyword-based heuristic for the "LLM" part in this demo without burning tokens
            is_ai = any(kw in raw_data.get("content", "").lower() or kw in raw_data.get("title", "").lower() for kw in ["ai", "gpt", "llm", "rag", "transformer", "learning", "model", "prompt"])
            
            if not is_ai and "github.com/trending" not in raw_data["url"]: 
                # Strict filtering for non-trending pages. 
                return {"is_ai_related": False}

            return {
                "is_ai_related": True,
                "id": str(uuid.uuid4()),
                "title": raw_data.get("title", "Untitled"),
                "url": raw_data["url"],
                "type": raw_data["type"],
                "summary": raw_data.get("description") or f"AI 摘要: {raw_data.get('title')}",
                "recommended_reason": f"推荐理由: 这是一个关于 {raw_data.get('title')} 的优质资源，适合深入学习 AI 技术。",
                "author": raw_data.get("author", "Unknown"),
                "concepts": ["AI", "LLM"], 
                "tech_stack": raw_data.get("tech_stack", ["General"]),
                "published_at": self._resolve_date(raw_data.get("published_at"))
            }
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {"is_ai_related": False} # Fail safe
