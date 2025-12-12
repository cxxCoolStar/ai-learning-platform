from typing import List
from app.services.parsers.base import BaseParser
import re

class XProfileParser(BaseParser):
    def parse(self, html_content: str) -> List[str]:
        # Simple regex to find status links
        urls = []
        patterns = [
            r'https?://(?:www\.)?x\.com/[^/]+/status/\d+',
            r'https?://(?:www\.)?twitter\.com/[^/]+/status/\d+'
        ]
        
        if not html_content:
            return []

        for pattern in patterns:
            found = re.findall(pattern, html_content)
            urls.extend(found)
            
        return list(set(urls))
