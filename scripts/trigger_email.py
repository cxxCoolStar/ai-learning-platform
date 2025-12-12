import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.getcwd())

from app.services.scheduler import SchedulerService
from app.db.session import SessionLocal
from app.models.sql_models import Resource

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def trigger_email():
    print("--- Manual Trigger: Daily Digest Email ---")
    
    # Check if we have recent data to ensure email sends
    db = SessionLocal()
    yesterday = datetime.now() - timedelta(days=1)
    recent_count = db.query(Resource).filter(Resource.published_at >= yesterday).count()
    db.close()
    
    print(f"Resources from last 24h: {recent_count}")
    
    service = SchedulerService()
    
    # We want to see the email format, so we execute the job.
    # The job includes crawling, which might take a moment.
    # If no recent data, crawling is necessary. 
    # If we have data, we could technically skip crawling for speed, but let's run full flow to be safe.
    
    await service.daily_digest_job()
    print("--- Job Execution Complete ---")

if __name__ == "__main__":
    asyncio.run(trigger_email())
