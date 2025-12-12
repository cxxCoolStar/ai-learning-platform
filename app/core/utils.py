from datetime import datetime, timedelta, timezone
from dateutil import parser
import logging

logger = logging.getLogger(__name__)

def is_content_recent(date_str: str, days: int = 90) -> bool:
    """
    Checks if the provided date string is within the last `days`.
    Returns True if recent, False if older.
    """
    if not date_str:
        # If no date provided, we can't filter, so we assume it's okay (or could be strict)
        # For now, let's assume okay but log
        return True

    try:
        dt = parser.parse(date_str)
        # Ensure timezone awareness
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days)
        
        if dt < cutoff:
            logger.info(f"Content date {dt} is older than {days} days cutoff {cutoff}")
            return False
        return True
    except Exception as e:
        logger.warning(f"Date parsing failed for {date_str}: {e}")
        # If we can't parse, we default to accepting it (fail open)
        return True
