from typing import Optional
from app.services.parsers.base import BaseParser
from app.services.parsers.github_trending import GithubTrendingParser
from app.services.parsers.levelup_coding import LevelUpCodingParser
from app.services.parsers.langchain_blog import LangChainBlogParser
from app.services.parsers.anthropic_blog import AnthropicBlogParser
from app.services.parsers.youtube_channel import YouTubeChannelParser
from app.services.parsers.x_profile import XProfileParser

class ParserFactory:
    @staticmethod
    def get_parser(url: str) -> Optional[BaseParser]:
        if "github.com/trending" in url:
            return GithubTrendingParser()
        elif "levelup.gitconnected.com" in url:
            return LevelUpCodingParser()
        elif "blog.langchain.com" in url:
            return LangChainBlogParser()
        elif "anthropic.com/engineering" in url:
            return AnthropicBlogParser()
        elif "youtube.com" in url:
            return YouTubeChannelParser()
        elif "x.com" in url or "twitter.com" in url:
            return XProfileParser()
        else:
            return None
