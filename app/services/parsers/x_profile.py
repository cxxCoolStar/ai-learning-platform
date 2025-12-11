from bs4 import BeautifulSoup
from typing import List
import logging
import re
from app.services.parsers.base import BaseParser

logger = logging.getLogger(__name__)

class XProfileParser(BaseParser):
    def parse(self, html_content: str) -> List[str]:
        """
        Parse X (Twitter) Profile page HTML to extract tweet URLs.
        """
        urls = []
        try:
            tweet_ids = set()
            
            # Method 1: BS4 for hrefs
            soup = BeautifulSoup(html_content, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                # Standard tweet path: /username/status/123456789
                if '/status/' in href:
                    # Validate it ends with digits
                    match = re.search(r'/status/(\d+)', href)
                    if match:
                        tweet_ids.add(match.group(1))

            # Method 2: Regex on full content (for JSON data)
            # e.g. "rest_id":"123456" inside Tweet results, or url structure
            # Looking for status/123456789 pattern in text
            regex_matches = re.findall(r'/status/(\d+)', html_content)
            for tid in regex_matches:
                tweet_ids.add(tid)
            
            # Reconstruct full URLs. 
            # Note: We might not know the exact username for each ID if we used regex globally,
            # but usually constructing https://x.com/i/web/status/ID or similar works.
            # Or better: https://x.com/user/status/ID.
            # Since we don't always have the user from just the ID in regex, 
            # we can try to rely on the fact that these came from a specific profile page 
            # OR just use a generic format if X supports it. 
            # Actually, https://x.com/anyuser/status/ID often redirects correctly, but best to use 'i' or just store what we found.
            # However, for the ingestion pipeline, we want a valid URL.
            
            # Let's rely on what we found in hrefs first which have the username.
            # For regex matches, we might miss the username.
            
            # If we parse `href="/user/status/id"`, we have the full path.
            # Let's prioritize hrefs.
            
            final_paths = set()
            
            # Re-scan for full paths
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/status/' in href and re.search(r'/status/(\d+)$', href):
                    final_paths.add(href)
            
            # If regex found IDs that hrefs didn't (unlikely in rendered HTML but possible in JSON),
            # we can't easily reconstruct the URL without the handle.
            # So we'll stick to extracted paths.
            
            for path in final_paths:
                if path.startswith('http'):
                    urls.append(path)
                else:
                    urls.append(f"https://x.com{path}")
                        
            logger.info(f"Parsed {len(urls)} tweets from X Profile")
            return urls
            
        except Exception as e:
            logger.error(f"Error parsing X Profile: {e}")
            return []
