
import sys
import os
import asyncio
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_youtube_date():
    logger.info("Initializing YouTubeCrawler...")
    try:
        from app.services.crawler import YouTubeCrawler
        crawler = YouTubeCrawler()
    except ImportError as e:
        logger.error(f"Failed to import YouTubeCrawler: {e}")
        return

    # Test URL: A stable video (e.g. OpenAI GPT-4 demo) - OLDER than 3 months
    # GPT-4 Developer Livestream (March 14, 2023) -> Should FAIL if logic works
    test_url_old = "https://www.youtube.com/watch?v=outcGtbnMuQ" 
    
    logger.info(f"Testing OLD Video (Should fail): {test_url_old}")
    try:
        result = await crawler.crawl(test_url_old)
        print("\n--- Crawl Result (Old) ---")
        print(f"Title: {result.get('title')}")
        print(f"Published At: {result.get('published_at')}")
        
    except ValueError as e:
         print(f"\n--- SUCCESS: Old video correctly rejected: {e}")
    except Exception as e:
        logger.error(f"Crawl execution failed: {e}")

    # Test URL: A Recent Video (Need something < 3 months)
    # This might fail if the video becomes old, but for now we can try a very recent channel
    # or just skip this if we confirmed the old one failed correctly.
    # Let's try to just check the metadata extraction on the old one, assuming we can catch the error if we want to inspect.
    
    # Actually, let's Temporarily mock is_content_recent to True to see if date is extracted?
    # No, better to see rejection.

if __name__ == "__main__":
    asyncio.run(test_youtube_date())
