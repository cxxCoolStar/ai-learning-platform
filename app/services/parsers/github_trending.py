from bs4 import BeautifulSoup
from typing import List
import logging
from app.services.parsers.base import BaseParser

logger = logging.getLogger(__name__)

class GithubTrendingParser(BaseParser):
    def parse(self, html_content: str) -> List[str]:
        """
        Parse GitHub Trending page HTML to extract repository URLs.
        """
        urls = []
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # GitHub Trending repos are usually in <article class="Box-row">
            articles = soup.find_all('article', class_='Box-row')
            
            for article in articles:
                # Find the h2 tag which contains the link
                h2 = article.find('h2')
                if h2:
                    a_tag = h2.find('a')
                    if a_tag and a_tag.get('href'):
                        # href is usually relative like /owner/repo
                        relative_url = a_tag.get('href')
                        full_url = f"https://github.com{relative_url}"
                        urls.append(full_url)
                        
            logger.info(f"Parsed {len(urls)} repositories from GitHub Trending")
            return urls
            
        except Exception as e:
            logger.error(f"Error parsing GitHub Trending: {e}")
            return []
