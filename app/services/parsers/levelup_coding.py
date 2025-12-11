from bs4 import BeautifulSoup
from typing import List
import logging
from app.services.parsers.base import BaseParser

logger = logging.getLogger(__name__)

class LevelUpCodingParser(BaseParser):
    def parse(self, html_content: str) -> List[str]:
        """
        Parse Level Up Coding (Medium) page HTML to extract article URLs.
        """
        urls = []
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Medium articles usually are <a> tags with specific attributes or structure
            # A generic way for Medium publications is to look for links that:
            # 1. Have an href
            # 2. Belong to the domain (or are relative)
            # 3. Contain a date or look like an article slug (often end with a hash id like -1234abc)
            
            # Find all 'a' tags
            links = soup.find_all('a')
            
            seen_urls = set()
            
            for link in links:
                href = link.get('href')
                if not href:
                    continue
                
                # Normalize URL
                if href.startswith('/'):
                    full_url = f"https://levelup.gitconnected.com{href}"
                elif href.startswith('https://levelup.gitconnected.com'):
                    full_url = href
                else:
                    continue
                
                # Filter out non-article links (tags, authors, etc.)
                # Heuristic: Articles usually don't contain '/tag/', '/@', '/page/'
                # Medium article URLs often have a unique ID at the end
                if any(x in full_url for x in ['/tag/', '/@', '/page/', '/search', '/about', '/signin', '/membership']):
                    continue
                
                # Often Medium URLs have ?source=... remove it
                full_url = full_url.split('?')[0]
                
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    urls.append(full_url)
                        
            logger.info(f"Parsed {len(urls)} articles from Level Up Coding")
            return urls
            
        except Exception as e:
            logger.error(f"Error parsing Level Up Coding: {e}")
            return []
