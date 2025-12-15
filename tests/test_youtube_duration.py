import asyncio
from app.services.crawler import YouTubeCrawler

async def test_duration_extraction():
    # The video reported by user where timestamps are missing
    # URL: https://www.youtube.com/watch?v=xriHA6WwZtw
    url = "https://www.youtube.com/watch?v=xriHA6WwZtw" 
    
    crawler = YouTubeCrawler()
    result = await crawler.crawl(url)
    
    print(f"Title: {result.get('title')}")
    print(f"Duration extracted: {result.get('duration')}")
    
    # Print Description to see if it has timestamps
    description = result.get('description', '')
    print("Description Preview:")
    print(description[:500])
    
    # Print content to check for Transcript
    content = result.get('content', '')
    print("Full Content Preview:")
    print(content) # Print all to see if Transcript section exists
    
    if result.get('duration'):
        print(f"SUCCESS: Duration found! {result.get('duration')}")
    else:
        print("FAILURE: Duration NOT found (Expected).")

if __name__ == "__main__":
    asyncio.run(test_duration_extraction())
