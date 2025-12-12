import logging
import httpx
from typing import Dict, Any
from app.services.crawler import BaseCrawler
from app.core.config import get_settings
from app.core.utils import is_content_recent

logger = logging.getLogger(__name__)

class XApiCrawler(BaseCrawler):
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://api.twitter.com/2/tweets"

    async def crawl(self, url: str) -> Dict[str, Any]:
        logger.info(f"Crawling X via API: {url}")
        
        tweet_id = self._extract_tweet_id(url)
        if not tweet_id:
            logger.error(f"Could not extract tweet ID from {url}")
            return {
                "title": "Invalid X URL",
                "content": "",
                "url": url,
                "type": "Social",
                "error": "Invalid X URL"
            }

        headers = {
            "Authorization": f"Bearer {self.settings.X_BEARER_TOKEN}",
            "User-Agent": "v2TweetLookupPython"
        }

        params = {
            "ids": tweet_id,
            "tweet.fields": "created_at,author_id,text,lang",
            "expansions": "author_id",
            "user.fields": "name,username"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.base_url, headers=headers, params=params)
                
                if response.status_code != 200:
                    logger.error(f"X API Error: {response.status_code} - {response.text}")
                    # Return fallback structure so pipeline doesn't crash completely, 
                    # or re-raise if strictness is required.
                    # Given the user wants to see logs, we'll try to be helpful.
                    return {
                        "title": f"Error fetching tweet {tweet_id}",
                        "content": f"Failed to fetch content. Status: {response.status_code}",
                        "url": url,
                        "type": "Social",
                        "error": str(response.status_code)
                    }

                data = response.json()
                
                if "data" not in data or not data["data"]:
                    logger.warning(f"No data found for tweet {tweet_id}")
                    return {
                        "title": "Tweet Not Found",
                        "content": "Tweet content not available.",
                        "url": url,
                        "type": "Social"
                    }

                tweet_data = data["data"][0]
                
                # Check date
                created_at = tweet_data.get("created_at")
                if created_at and not is_content_recent(created_at):
                    logger.warning(f"Tweet {tweet_id} is older than 3 months ({created_at}). Skipping.")
                    raise ValueError("Content is older than 3 months")

                includes = data.get("includes", {})
                users = {u["id"]: u for u in includes.get("users", [])}
                author_id = tweet_data.get("author_id")
                author_name = users.get(author_id, {}).get("name", "Unknown")
                author_username = users.get(author_id, {}).get("username", "unknown")

                return {
                    "title": f"Tweet by {author_name} (@{author_username})",
                    "content": tweet_data.get("text", ""),
                    "url": url,
                    "type": "Social",
                    "author": author_name,
                    "published_at": tweet_data.get("created_at"),
                    "metadata": {
                        "created_at": tweet_data.get("created_at"),
                        "lang": tweet_data.get("lang"),
                        "tweet_id": tweet_id
                    }
                }

            except Exception as e:
                # Re-raise date validation errors
                if "older than 3 months" in str(e):
                    raise e

                logger.error(f"X API crawl failed: {e}")
                # Return partial result to allow process to continue if possible
                return {
                    "title": "Error processing tweet",
                    "content": f"Error: {str(e)}",
                    "url": url,
                    "type": "Social",
                    "error": str(e)
                }

    def _extract_tweet_id(self, url: str) -> str:
        # Expected format: https://x.com/username/status/1234567890...
        try:
            parts = url.split("/status/")
            if len(parts) > 1:
                return parts[1].split("?")[0].split("/")[0]
        except Exception:
            pass
        return ""
