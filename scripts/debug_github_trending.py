import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

from app.services.crawler import CrawlerFactory
from app.services.parsers.factory import ParserFactory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_github_trending():
    url = "https://github.com/trending"
    print(f"Fetching source: {url}...")
    
    crawler = CrawlerFactory.get_crawler(url)
    try:
        data = await crawler.crawl(url)
        html_content = data.get("html", "")
        
        if not html_content:
            print("Error: No HTML content returned.")
            return

        parser = ParserFactory.get_parser(url)
        links = parser.parse(html_content)
        
        print(f"\nFound {len(links)} links:")
        found = False
        for link in links:
            print(f"- {link}")
            if "claude-mem" in link:
                found = True
        
        if found:
            print("\nSUCCESS: 'claude-mem' was found in the list.")
        else:
            print("\nFAILURE: 'claude-mem' was NOT found in the list.")
            # Print HTML snippet to debug if layout changed
            print("\n--- HTML Snippet (First 500 chars) ---")
            print(html_content[:500])
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(debug_github_trending())
