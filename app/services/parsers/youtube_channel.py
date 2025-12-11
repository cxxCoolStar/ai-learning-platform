from bs4 import BeautifulSoup
from typing import List
import logging
import re
from app.services.parsers.base import BaseParser

logger = logging.getLogger(__name__)

class YouTubeChannelParser(BaseParser):
    def parse(self, html_content: str) -> List[str]:
        """
        Parse YouTube Channel page HTML to extract video URLs.
        """
        urls = []
        try:
            # Simple regex approach often works better for raw HTML from dynamic sites
            # if the crawler returns rendered HTML, BS4 is good.
            # If crawler returns raw initial HTML, regex might find JSON data.
            
            # Pattern for video links: /watch?v=...
            # We want unique video IDs
            
            video_ids = set()
            
            # Method 1: BS4 for hrefs
            soup = BeautifulSoup(html_content, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/watch?v=' in href:
                    # Extract video ID
                    match = re.search(r'v=([a-zA-Z0-9_-]+)', href)
                    if match:
                        video_ids.add(match.group(1))
            
            # Method 2: Regex on full content (in case of JSON blobs)
            # "videoId":"..."
            regex_matches = re.findall(r'"videoId":"([a-zA-Z0-9_-]+)"', html_content)
            for vid in regex_matches:
                video_ids.add(vid)
                
            for vid in video_ids:
                urls.append(f"https://www.youtube.com/watch?v={vid}")
                        
            logger.info(f"Parsed {len(urls)} videos from YouTube Channel")
            return urls
            
        except Exception as e:
            logger.error(f"Error parsing YouTube Channel: {e}")
            return []
