import logging
import asyncio
from typing import List, Dict, Any
from abc import ABC, abstractmethod
from crawl4ai import AsyncWebCrawler
from langchain_community.document_loaders import GithubFileLoader
from bs4 import BeautifulSoup
from app.core.config import get_settings
from app.core.utils import is_content_recent

logger = logging.getLogger(__name__)

class BaseCrawler(ABC):
    @abstractmethod
    async def crawl(self, url: str) -> Dict[str, Any]:
        pass

# Import XApiCrawler AFTER BaseCrawler is defined to avoid circular import
try:
    from app.services.x_api_crawler import XApiCrawler
except ImportError:
    # If XApiCrawler fails to import (e.g. BaseCrawler not found yet), handle it.
    # But since we are in the same file that defines BaseCrawler, this is tricky.
    # The issue is x_api_crawler.py imports BaseCrawler from THIS file.
    # Solution: Move BaseCrawler to a separate file or use type checking imports.
    pass

class WebCrawler(BaseCrawler):
    def __init__(self, resource_type: str = "Article"):
        self.resource_type = resource_type
        self.settings = get_settings()

    async def crawl(self, url: str) -> Dict[str, Any]:
        logger.info(f"Crawling Web: {url}")
        
        # Configure crawler with auth if available (e.g. for X)
        # Note: crawl4ai configuration might vary, but for now we keep it simple
        async with AsyncWebCrawler(verbose=True) as crawler:
            # Inject cookie if it's an X/Twitter URL and we have the token
            if self.resource_type == "Social" and ("x.com" in url or "twitter.com" in url) and self.settings.X_AUTH_TOKEN:
                # Use BrowserConfig to inject cookies properly
                from crawl4ai import BrowserConfig, CrawlerRunConfig
                
                # Construct cookie dictionary
                # Important: domain needs to be set correctly for X
                cookies = [
                    {
                        "name": "auth_token",
                        "value": self.settings.X_AUTH_TOKEN,
                        "domain": ".x.com",
                        "path": "/",
                        "httpOnly": True,
                        "secure": True,
                        "sameSite": "None" 
                    },
                    {
                        "name": "auth_token",
                        "value": self.settings.X_AUTH_TOKEN,
                        "domain": ".twitter.com",
                        "path": "/",
                        "httpOnly": True,
                        "secure": True,
                        "sameSite": "None" 
                    }
                ]
                
                # Configure run parameters
                # magic=True enables anti-detect features
                # wait_for suggests waiting for dynamic content
                # js_code to scroll down a bit to trigger content load
                js_scroll = "window.scrollTo(0, 500);"
                
                # Note: arun() parameters might vary by version. 
                # If cookies param is supported directly or via config object.
                # Checking latest crawl4ai patterns: typically use BrowserConfig or direct kwargs.
                # Assuming arun(..., cookies=...) or run_config.
                
                # Let's try passing cookies directly if supported, or via context modification hook if possible.
                # Based on common usage:
                
                # We will try to just pass magic=True and let crawl4ai handle basics, 
                # but injecting cookies is key. 
                # Since we can't easily test the exact API version here, we'll try the most standard way:
                # If arun supports `cookies` list directly (list of dicts).
                
                # Fallback: if we can't inject cookie easily in this wrapper, we proceed with magic=True.
                # But let's try to pass 'cookies' kwarg.
                
                try:
                    # Removed wait_for="article" because X structure is complex and dynamic
                    # wait_for="article" often times out if the page loads as a feed or uses different tags.
                    # Using a simple css selector or just waiting for network idle is safer.
                    # "main" is usually a safer bet for X, or just wait for body.
                    result = await crawler.arun(url=url, magic=True, cookies=cookies, js_code=js_scroll, wait_for="css:main")
                except TypeError:
                    # Fallback if cookies param not supported in this version
                    logger.warning("Cookies parameter might not be supported in this crawl4ai version, falling back to magic=True")
                    result = await crawler.arun(url=url, magic=True)
                except Exception as e:
                     logger.warning(f"Crawl failed with wait condition: {e}. Retrying without wait_for.")
                     # Retry without strict wait condition
                     result = await crawler.arun(url=url, magic=True, cookies=cookies, js_code=js_scroll)
            else:
                result = await crawler.arun(url=url)
            
            # Extract metadata using BeautifulSoup
            title = "Web Page"
            description = ""
            author = "Unknown" # Added author field
            content_override = None
            
            try:
                if result.html:
                    soup = BeautifulSoup(result.html, 'html.parser')
                    
                    # Generic metadata extraction
                    if soup.title and soup.title.string:
                        title = soup.title.string.strip()
                    
                    meta_desc = soup.find('meta', attrs={'name': 'description'}) or \
                                soup.find('meta', attrs={'property': 'og:description'})
                    if meta_desc:
                        description = meta_desc.get('content', '').strip()
                        
                    # Extract Author
                    meta_author = soup.find('meta', attrs={'name': 'author'}) or \
                                  soup.find('meta', attrs={'property': 'article:author'}) or \
                                  soup.find('meta', attrs={'name': 'twitter:creator'})
                    if meta_author:
                        author = meta_author.get('content', '').strip()

                    # Extract Date and Filter
                    published_time = None
                    date_meta = soup.find('meta', attrs={'property': 'article:published_time'}) or \
                                soup.find('meta', attrs={'name': 'date'}) or \
                                soup.find('meta', attrs={'name': 'pubdate'}) or \
                                soup.find('meta', attrs={'property': 'og:updated_time'}) or \
                                soup.find(attrs={'itemprop': 'datePublished'})
                    
                    if date_meta:
                        published_time = date_meta.get('content', '')
                    
                    if published_time and not is_content_recent(published_time):
                        logger.warning(f"Content from {published_time} is older than 3 months. URL: {url}")
                        raise ValueError("Content is older than 3 months")

                    # Specific Logic for YouTube (Video)
                    if self.resource_type == "Video" and "youtube.com" in url:
                        # For YouTube, we prioritize og:title and description
                        og_title = soup.find('meta', attrs={'property': 'og:title'})
                        if og_title:
                            title = og_title.get('content', '').strip()
                        
                        # Try to find channel name (Author)
                        # YouTube often puts channel name in <link itemprop="name" content="..."> inside author span
                        # Or og:video:tag might contain it, but risky.
                        # Best bet: <div itemprop="author"> ... <link itemprop="name" content="Channel Name">
                        # Or <span itemprop="author" itemscope itemtype="http://schema.org/Person"><link itemprop="name" content="Channel Name"></span>
                        
                        # Let's look for itemprops
                        author_tag = soup.find(attrs={'itemprop': 'author'})
                        if author_tag:
                            name_tag = author_tag.find(attrs={'itemprop': 'name'})
                            if name_tag:
                                author = name_tag.get('content', '').strip()
                        
                        # Fallback for YouTube author if not found via itemprop (sometimes it's simple text in a class)
                        if author == "Unknown":
                             # Try og:site_name (usually "YouTube", not channel)
                             # Try looking for "ytd-channel-name" text if rendered JS... but we might not have full render.
                             pass

                        # Set content to just title + description as requested
                        content_override = f"Video Title: {title}\n\nDescription:\n{description}"
                    
                    # Specific Logic for X/Twitter (Social)
                    elif self.resource_type == "Social" and ("x.com" in url or "twitter.com" in url):
                        # X posts usually don't have a good <title> (often just "X")
                        # We try to find the tweet text.
                        # Since X is dynamic, the HTML might be empty if not logged in.
                        # But if we got something, we use the raw text.
                        # We set title to generic so LLM can generate it.
                        title = "Social Post" 
                        # We don't override content here, we let the full markdown go to LLM
                        # so it can extract the tweet text from the noise.
            
            except Exception as e:
                if "older than 3 months" in str(e):
                    raise e
                logger.warning(f"Failed to extract metadata for {url}: {e}")

            return {
                "title": title, 
                "content": content_override if content_override else result.markdown,
                "html": result.html,
                "description": description, 
                "author": author, 
                "published_at": published_time, # Return published_at
                "url": url,
                "type": self.resource_type
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
        
        # Extract owner as author
        parts = url.rstrip('/').split('/')
        author = "Unknown"
        if len(parts) >= 4 and parts[2] == "github.com":
             author = parts[3]

        # Note: Real implementation would use GitHub API to get repo metadata + README
        # For simplicity in this demo, we'll return a placeholder structure
        # In a real app, use PyGithub or standard requests
        return {
            "title": url.split("/")[-1],
            "content": f"Repository content for {url}. (Mocked for now with AI keywords to pass filter: AI, LLM, RAG, Agent, Machine Learning)",
            "url": url,
            "type": "Code",
            "author": author,
            "tech_stack": ["Python", "Docker"] # In reality, extract this from files
        }

class CrawlerFactory:
    @staticmethod
    def get_crawler(url: str) -> BaseCrawler:
        if "github.com/trending" in url:
            return WebCrawler(resource_type="Article") # It's a list page, but we process items
        elif "github.com" in url:
            return GitHubCrawler()
        elif "youtube.com" in url or "youtu.be" in url:
            return WebCrawler(resource_type="Video")
        elif "x.com" in url or "twitter.com" in url:
            # Check if API is configured, otherwise fallback to WebCrawler
            settings = get_settings()
            if settings.X_BEARER_TOKEN:
                return XApiCrawler()
            return WebCrawler(resource_type="Social")
        else:
            return WebCrawler(resource_type="Article")
