import logging
import asyncio
from typing import List, Dict, Any
from abc import ABC, abstractmethod
from crawl4ai import AsyncWebCrawler
from langchain_community.document_loaders import GithubFileLoader
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class BaseCrawler(ABC):
    @abstractmethod
    async def crawl(self, url: str) -> Dict[str, Any]:
        pass

class WebCrawler(BaseCrawler):
    async def crawl(self, url: str) -> Dict[str, Any]:
        logger.info(f"Crawling Web: {url}")
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(url=url)
            
            # Extract metadata using BeautifulSoup
            title = "Web Page"
            description = ""
            try:
                if result.html:
                    soup = BeautifulSoup(result.html, 'html.parser')
                    if soup.title and soup.title.string:
                        title = soup.title.string.strip()
                    
                    # Try to find description meta tag
                    meta_desc = soup.find('meta', attrs={'name': 'description'}) or \
                                soup.find('meta', attrs={'property': 'og:description'})
                    if meta_desc:
                        description = meta_desc.get('content', '').strip()
            except Exception as e:
                logger.warning(f"Failed to extract metadata for {url}: {e}")

            return {
                "title": title, 
                "content": result.markdown,
                "html": result.html,
                "description": description, # Added description field
                "url": url,
                "type": "Article"
            }

class GitHubCrawler(BaseCrawler):
    """
    Simple GitHub crawler using LangChain loader or direct API if needed.
    For deep analysis, we might want to clone and parse, but for now specific file loading.
    """
    def __init__(self, github_token: str = None):
        self.github_token = github_token

    async def crawl(self, url: str) -> Dict[str, Any]:
        # URL format: https://github.com/user/repo
        logger.info(f"Crawling GitHub: {url}")
        # Note: Real implementation would use GitHub API to get repo metadata + README
        # For simplicity in this demo, we'll return a placeholder structure
        # In a real app, use PyGithub or standard requests
        return {
            "title": url.split("/")[-1],
            "content": f"Repository content for {url}. (Mocked for now)",
            "url": url,
            "type": "Code",
            "tech_stack": ["Python", "Docker"] # In reality, extract this from files
        }

class CrawlerFactory:
    @staticmethod
    def get_crawler(url: str) -> BaseCrawler:
        if "github.com/trending" in url:
            return WebCrawler()
        elif "github.com" in url:
            return GitHubCrawler()
        elif "youtube.com" in url or "youtu.be" in url:
            # Placeholder for VideoCrawler
            return WebCrawler() 
        else:
            return WebCrawler()
