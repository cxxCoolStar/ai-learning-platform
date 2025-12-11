from bs4 import BeautifulSoup
from typing import List
import logging
from app.services.parsers.base import BaseParser

logger = logging.getLogger(__name__)

class AnthropicBlogParser(BaseParser):
    def parse(self, html_content: str) -> List[str]:
        """
        Parse Anthropic Engineering Blog page HTML to extract article URLs.
        """
        urls = []
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Anthropic Engineering blog links likely start with /engineering/ or /news/
            
            links = soup.find_all('a')
            seen_urls = set()
            
            for link in links:
                href = link.get('href')
                if not href:
                    continue
                
                # Normalize URL
                if href.startswith('/'):
                    full_url = f"https://www.anthropic.com{href}"
                elif href.startswith('https://www.anthropic.com'):
                    full_url = href
                else:
                    continue
                
                # Filter criteria
                # We are looking for engineering articles, so they should likely contain /engineering/ or /research/ or /news/
                # But strictly speaking, if we are parsing the /engineering page, the relevant links are likely there.
                
                valid_paths = ['/engineering/', '/news/', '/research/']
                if not any(path in full_url for path in valid_paths):
                    continue

                if full_url in ["https://www.anthropic.com/engineering", "https://www.anthropic.com/news", "https://www.anthropic.com/research"]:
                    continue

                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    urls.append(full_url)
                        
            logger.info(f"Parsed {len(urls)} articles from Anthropic Engineering")
            return urls
            
        except Exception as e:
            logger.error(f"Error parsing Anthropic Engineering: {e}")
            return []
