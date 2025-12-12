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
    
    # Reset Vector and Graph databases for clean slate
    print("Resetting Vector and Graph databases...")
    pipeline.vector_service.reset_collection()
    pipeline.graph_service.reset_graph()
    
    # Sources to scrape
    sources = [
        "https://github.com/trending",
        "https://levelup.gitconnected.com",
        "https://blog.langchain.com",
        "https://www.anthropic.com/engineering",
        # YouTube Channels
        "https://www.youtube.com/@LatentSpaceTV",
        "https://www.youtube.com/@AIDailyBrief",
        "https://www.youtube.com/@LennysPodcast",
        "https://www.youtube.com/@NoPriorsPodcast",
        "https://www.youtube.com/@GoogleDeepMind",
        "https://www.youtube.com/@sequoiacapital",
        "https://www.youtube.com/@RedpointAI",
        "https://www.youtube.com/@ycombinator",
        "https://www.youtube.com/@PeterYangYT",
        "https://www.youtube.com/@southparkcommons",
        "https://www.youtube.com/@AndrejKarpathy",
        "https://www.youtube.com/@AnthropicAI",
        "https://www.youtube.com/@Google",
        "https://www.youtube.com/@Every",
        "https://www.youtube.com/@MattTurck",
        "https://www.youtube.com/@ColeMedin",
        # X Profiles
        "https://x.com/zarazhang",
        "https://x.com/zarazhangrui",
        "https://x.com/karpathy",
        "https://x.com/swyx",
        "https://x.com/gregisenberg",
        "https://x.com/lennysan",
        "https://x.com/joshwoodward",
        "https://x.com/kevinweil",
        "https://x.com/petergyang",
        "https://x.com/thenanyu",
        "https://x.com/madhuguru",
        "https://x.com/mckaywrigley",
        "https://x.com/stevenberlin",
        "https://x.com/AmandaAskell",
        "https://x.com/catwu",
        "https://x.com/thariq",
        "https://x.com/googlelabs",
        "https://x.com/georgemack",
        "https://x.com/RaizaMartin",
        "https://x.com/amasad",
        "https://x.com/rauchg",
        "https://x.com/rileybrown_ai",
        "https://x.com/alexalbert__",
        "https://x.com/HamelHusain",
        "https://x.com/levie",
        "https://x.com/ryo_lu",
        "https://x.com/garrytan",
        "https://x.com/lulumeservey",
        "https://x.com/venturetwins",
        "https://x.com/mattturck",
        "https://x.com/joulee",
        "https://x.com/gabrielpeters",
        "https://x.com/pjace"
    ]
    
    all_urls = []
    for source in sources:
        links = await scrape_source(source)
        all_urls.extend(links)
    
    # Remove duplicates
    all_urls = list(set(all_urls))
    
    print(f"Starting seeding process for {len(all_urls)} unique URLs...")
    for url in all_urls[:200]: 
        print(f"Ingesting: {url}")
        await pipeline.ingest_url(url)
    print("Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed())
