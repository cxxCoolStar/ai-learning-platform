import asyncio
from app.services.crawler import YouTubeCrawler

async def test_duration_extraction():
    # A known YouTube Short (less than 60s)
    # n8n AI Agent related or generic
    # Using the ID found in search: Pd_Y5_5n9_8
    url = "https://www.youtube.com/watch?v=Pd_Y5_5n9_8" 
    
    crawler = YouTubeCrawler()
    result = await crawler.crawl(url)
    
    print(f"Title: {result.get('title')}")
    print(f"Duration extracted: {result.get('duration')}") # Should be None currently
    
    # We want to see if we CAN find it in the HTML manually during this test
    # (The crawler won't return it yet, so we inspect the logic)
    # Actually, let's just assert the current behavior (None) before fixing.
    
    if result.get('duration'):
        print(f"SUCCESS: Duration found! {result.get('duration')}")
    else:
        print("FAILURE: Duration NOT found (Expected).")

if __name__ == "__main__":
    asyncio.run(test_duration_extraction())
