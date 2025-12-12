import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

from app.services.ingestion import IngestionPipeline
from app.services.crawler import CrawlerFactory

# Configure logging to see details
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_ingestion():
    url = "https://github.com/thedotmack/claude-mem"
    print(f"--- Debugging Ingestion for {url} ---")
    
    pipeline = IngestionPipeline()
    
    # 1. Test Crawl independently to see what content we get
    print("\n1. Testing Crawler...")
    crawler = CrawlerFactory.get_crawler(url)
    raw_data = await crawler.crawl(url)
    
    print(f"Crawl Result Keys: {raw_data.keys()}")
    content = raw_data.get("content", "")
    print(f"Content Length: {len(content)}")
    print(f"Content Preview (first 500 chars):\n{content[:500]}")
    
    # 2. Test Analysis (LLM Filter)
    print("\n2. Testing LLM Analysis / Filter...")
    # We call the private method directly to see the result
    try:
        analyzed_data = await pipeline._analyze_content(raw_data)
        print(f"Analysis Result: {analyzed_data}")
        
        if analyzed_data.get("is_ai_related"):
            print("\n✅ SUCCESS: Content matches AI criteria.")
        else:
            print("\n❌ FAILED: Content was filtered out as non-AI.")
            
    except Exception as e:
        print(f"Analysis failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_ingestion())
