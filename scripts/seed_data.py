import asyncio
import sys
import os
import re

# Add project root to path
sys.path.append(os.getcwd())

from app.services.ingestion import IngestionPipeline
from app.db.session import engine, Base
from app.models import sql_models # Ensure models are imported
from app.services.crawler import CrawlerFactory
from app.services.parsers.factory import ParserFactory

async def scrape_source(url: str):
    """
    Generic scraper using CrawlerFactory and ParserFactory.
    """
    print(f"Fetching source: {url}...")
    crawler = CrawlerFactory.get_crawler(url)
    try:
        data = await crawler.crawl(url)
        html_content = data.get("html", "")
        if not html_content:
            print(f"No HTML content returned for {url}")
            return []
            
        parser = ParserFactory.get_parser(url)
        if not parser:
            print(f"No parser configured for {url}")
            return []
            
        links = parser.parse(html_content)
        print(f"Found {len(links)} links from {url}")
        return links
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return []

async def seed():
    # Ensure tables exist
    print("Creating database tables...")
    Base.metadata.drop_all(bind=engine) # Drop to apply schema changes (e.g. new column)
    Base.metadata.create_all(bind=engine)

    pipeline = IngestionPipeline()
    
    # Sources to scrape
    sources = [
        "https://github.com/trending",
        "https://levelup.gitconnected.com",
        "https://blog.langchain.com",
        "https://www.anthropic.com/engineering"
    ]
    
    all_urls = []
    for source in sources:
        links = await scrape_source(source)
        all_urls.extend(links)
    
    # Remove duplicates
    all_urls = list(set(all_urls))
    
    print(f"Starting seeding process for {len(all_urls)} unique URLs...")
    # Limit to first 10 for demo speed if needed, but let's try all or a subset
    for url in all_urls[:20]: # Limit to avoid taking too long in demo
        print(f"Ingesting: {url}")
        await pipeline.ingest_url(url)
    print("Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed())
