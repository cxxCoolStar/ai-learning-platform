import logging
import json
from enum import Enum
from typing import Dict, Any, Tuple
from app.core.config import get_settings
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

class SearchStrategy(Enum):
    HYBRID = "hybrid"      # Simple keyword/vector search
    GRAPH = "graph"        # Deep relation traversal
    COMBINED = "combined"  # Both

class IntelligentQueryRouter:
    """
    Decides which retrieval strategy to use based on query complexity.
    Adapted for Learning Platform.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.llm = ChatOpenAI(
            model=self.settings.LLM_MODEL,
            api_key=self.settings.OPENAI_API_KEY,
            base_url=self.settings.OPENAI_BASE_URL,
            temperature=0.0
        )

    def route_query(self, query: str) -> Tuple[SearchStrategy, Dict[str, Any]]:
        """
        Analyze query to determine strategy.
        """
        prompt = f"""
        Analyze the following query for an AI Learning Platform (containing Code, Articles, Videos).
        
        Query: "{query}"
        
        Determine the search strategy:
        1. 'hybrid': Simple lookup (e.g., "Python tutorials", "What is RAG?").
        2. 'graph': Complex relationship questions (e.g., "Prerequisites for learning Transformer", "Tools compatible with LangChain", "Evolution of LLMs").
        3. 'combined': Requires both specific facts and broad relational context.
        
        Output JSON:
        {{
            "strategy": "hybrid/graph/combined",
            "reasoning": "...",
            "keywords": ["..."],
            "entities": ["..."]
        }}
        """
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            # Handle potential markdown wrapping
            if content.startswith("```json"):
                content = content[7:-3]
            
            result = json.loads(content)
            strategy_str = result.get("strategy", "hybrid").lower()
            return SearchStrategy(strategy_str), result
            
        except Exception as e:
            logger.error(f"Routing failed: {e}")
            return SearchStrategy.HYBRID, {}
