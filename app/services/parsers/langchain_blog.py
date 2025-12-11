from bs4 import BeautifulSoup
from typing import List
import logging
from app.services.parsers.base import BaseParser

logger = logging.getLogger(__name__)

class LangChainBlogParser(BaseParser):
    def parse(self, html_content: str) -> List[str]:
        """
        Parse LangChain Blog page HTML to extract article URLs.
        """
        urls = []
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # LangChain blog usually lists articles with <a> tags
            # We look for links that look like blog posts
            
            links = soup.find_all('a')
            seen_urls = set()
            
            for link in links:
                href = link.get('href')
                if not href:
                    continue
                
                # Normalize URL
                if href.startswith('/'):
                    full_url = f"https://blog.langchain.com{href}"
                elif href.startswith('https://blog.langchain.com'):
                    full_url = href
                else:
                    continue
                
                # Filter out likely non-article pages
                if any(x in full_url for x in ['/tag/', '/author/', '/page/', '/rss', '/search']):
                    continue
                
                # Heuristic: Blog posts usually have >3 segments in path or specific date structure
                # But for now, simple exclusion is safer
                
                if full_url not in seen_urls and full_url != "https://blog.langchain.com/" and full_url != "https://blog.langchain.com":
                    seen_urls.add(full_url)
                    urls.append(full_url)
                        
            logger.info(f"Parsed {len(urls)} articles from LangChain Blog")
            return urls
            
        except Exception as e:
            logger.error(f"Error parsing LangChain Blog: {e}")
            return []
