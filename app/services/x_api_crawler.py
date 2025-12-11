import logging
import tweepy
import datetime
from typing import Dict, Any, Optional
from app.services.crawler import BaseCrawler
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class XApiCrawler(BaseCrawler):
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        
        # Filtering thresholds
        self.MIN_LIKES = 10
        self.MIN_RETWEETS = 5
        self.MIN_REPLIES = 2
        self.DAYS_LIMIT = 30 # Only crawl tweets from last 30 days
        
        if self.settings.X_BEARER_TOKEN:
            try:
                self.client = tweepy.Client(bearer_token=self.settings.X_BEARER_TOKEN)
            except Exception as e:
                logger.error(f"Failed to initialize X API Client: {e}")

    async def crawl(self, url: str) -> Dict[str, Any]:
        """
        Fetch tweet content using X API V2 with filtering.
        URL expected: https://x.com/user/status/TWEET_ID
        """
        logger.info(f"Crawling X via API: {url}")
        
        if not self.client:
            logger.error("X API Client not initialized. Missing Bearer Token.")
            return self._error_response(url, "X API not configured.")

        try:
            # Extract Tweet ID
            import re
            match = re.search(r'/status/(\d+)', url)
            if not match:
                logger.error(f"Could not extract tweet ID from {url}")
                return self._error_response(url, "Invalid URL")
            
            tweet_id = match.group(1)
            
            # Fetch Tweet with metrics
            response = self.client.get_tweet(
                tweet_id, 
                tweet_fields=['created_at', 'text', 'note_tweet', 'public_metrics', 'author_id']
            )
            
            if not response.data:
                logger.warning(f"No data returned for tweet {tweet_id}")
                return self._error_response(url, "Tweet Not Found")
            
            tweet = response.data
            
            # 1. Filter by Date (Recent content only)
            if tweet.created_at:
                now = datetime.datetime.now(datetime.timezone.utc)
                age = now - tweet.created_at
                if age.days > self.DAYS_LIMIT:
                    logger.info(f"Skipping tweet {tweet_id}: Too old ({age.days} days)")
                    return self._skip_response(url)

            # 2. Filter by Metrics (Popularity)
            metrics = tweet.public_metrics
            if metrics:
                likes = metrics.get('like_count', 0)
                retweets = metrics.get('retweet_count', 0)
                replies = metrics.get('reply_count', 0)
                
                if (likes < self.MIN_LIKES and 
                    retweets < self.MIN_RETWEETS and 
                    replies < self.MIN_REPLIES):
                    logger.info(f"Skipping tweet {tweet_id}: Metrics too low (Likes: {likes}, RT: {retweets})")
                    return self._skip_response(url)
            
            # Use full text if available
            text = tweet.text
            if tweet.note_tweet and 'text' in tweet.note_tweet:
                text = tweet.note_tweet['text']

            # Construct content with metrics for LLM context
            content = f"Tweet Content:\n{text}\n\nMetrics:\nLikes: {metrics.get('like_count', 0)}\nRetweets: {metrics.get('retweet_count', 0)}"

            return {
                "title": "Social Post", 
                "content": content,
                "html": "", 
                "description": text[:200],
                "url": url,
                "type": "Social",
                "published_at": tweet.created_at.isoformat() if tweet.created_at else None,
                "is_ai_related": True # Let LLM verify this later, but pass crawler check
            }

        except Exception as e:
            logger.error(f"X API Request failed: {e}")
            return self._error_response(url, f"Failed to fetch tweet: {e}")

    def _error_response(self, url: str, msg: str) -> Dict[str, Any]:
        return {
            "title": "Social Post (Error)",
            "content": msg,
            "url": url,
            "type": "Social",
            "is_ai_related": False
        }

    def _skip_response(self, url: str) -> Dict[str, Any]:
        return {
            "title": "Filtered Post",
            "content": "Skipped due to low metrics or age.",
            "url": url,
            "type": "Social",
            "is_ai_related": False # Flag to tell pipeline to skip
        }
