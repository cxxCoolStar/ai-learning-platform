
import sys
import os
import asyncio
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_x_crawler():
    logger.info("Initializing XApiCrawler...")
    try:
        from app.services.x_api_crawler import XApiCrawler
        crawler = XApiCrawler()
    except ImportError as e:
        logger.error(f"Failed to import XApiCrawler: {e}")
        return
    except Exception as e:
        logger.error(f"Failed to initialize XApiCrawler: {e}")
        return

    # Test URL (Jack Dorsey's first tweet)
    test_url = "https://x.com/jack/status/20" 
    # Or purely random to test 404 vs 401
    
    logger.info(f"Testing crawl for URL: {test_url}")
    try:
        result = await crawler.crawl(test_url)
        print("\n--- Crawl Result ---")
        print(f"Title: {result.get('title')}")
        print(f"Type: {result.get('type')}")
        print(f"Error: {result.get('error')}")
        print(f"Content Length: {len(result.get('content', ''))}")
        if result.get('error'):
            print(f"Raw Result: {result}")
        else:
            print(f"Content Snippet: {result.get('content', '')[:200]}...")
            
    except Exception as e:
        logger.error(f"Crawl execution failed: {e}")

if __name__ == "__main__":
    from app.core.config import get_settings
    settings = get_settings()
    if not settings.X_BEARER_TOKEN:
        logger.warning("X_BEARER_TOKEN is not set in environment or .env file.")
        logger.warning("Test is expected to fail with Authentication issues.")
    else:
        logger.info("X_BEARER_TOKEN found.")
        
    asyncio.run(test_x_crawler())
