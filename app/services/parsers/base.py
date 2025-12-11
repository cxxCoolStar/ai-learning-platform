from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseParser(ABC):
    @abstractmethod
    def parse(self, html_content: str) -> List[str]:
        """
        Parse HTML content and return a list of discovered URLs.
        """
        pass
