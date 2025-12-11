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
from app.services.parsers.github_trending import GithubTrendingParser

async def get_github_trending_repos():
    """
    Scrape GitHub Trending page to get top repo URLs using GithubTrendingParser.
    """
    print("Fetching GitHub Trending...")
    url = "https://github.com/trending"
    crawler = CrawlerFactory.get_crawler(url)
    try:
        data = await crawler.crawl(url)
        html_content = data.get("html", "")
        if not html_content:
            print("No HTML content returned from crawler.")
            return []
            
        parser = GithubTrendingParser()
        trending_repos = parser.parse(html_content)
        
        print(f"Found {len(trending_repos)} trending repos.")
        return trending_repos
    except Exception as e:
        print(f"Failed to fetch trending: {e}")
        return []

async def seed():
    # Ensure tables exist
    print("Creating database tables...")
    Base.metadata.drop_all(bind=engine) # Drop to apply schema changes (e.g. new column)
    Base.metadata.create_all(bind=engine)

    pipeline = IngestionPipeline()
    
    # 1. Standard URLs
    urls = [
        "https://blog.langchain.com/rag-production",
        "https://www.anthropic.com/engineering/prompt-engineering",
    ]
    
    # 2. GitHub Trending
    trending_urls = await get_github_trending_repos()
    urls.extend(trending_urls)
    
    print(f"Starting seeding process for {len(urls)} URLs...")
    for url in urls:
        print(f"Ingesting: {url}")
        await pipeline.ingest_url(url)
    print("Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed())
