
import sys
import os
import asyncio
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_web_crawler_x():
    logger.info("Initializing WebCrawler (Social)...")
    try:
        from app.services.crawler import WebCrawler
        # Force resource_type="Social" to trigger X-specific logic in WebCrawler
        crawler = WebCrawler(resource_type="Social")
    except ImportError as e:
        logger.error(f"Failed to import WebCrawler: {e}")
        return
    except Exception as e:
        logger.error(f"Failed to initialize WebCrawler: {e}")
        return

    # Test URL (Jack Dorsey's first tweet)
    test_url = "https://x.com/jack/status/20" 
    
    logger.info(f"Testing WebCrawler for URL: {test_url}")
    try:
        result = await crawler.crawl(test_url)
        print("\n--- Crawl Result ---")
        print(f"Title: {result.get('title')}")
        print(f"Type: {result.get('type')}")
        print(f"Content Length: {len(result.get('content', ''))}")
        print(f"Content Snippet: {result.get('content', '')[:500]}...")
        if result.get('error'):
            print(f"Error: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Crawl execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_web_crawler_x())
