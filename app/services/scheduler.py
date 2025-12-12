import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import desc
from app.services.ingestion import IngestionPipeline
from app.services.email_service import EmailService
from app.db.session import SessionLocal
from app.models.sql_models import Resource
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.ingestion_pipeline = IngestionPipeline()
        self.email_service = EmailService()
        self.notification_email = "1848505943@qq.com" # Could be configurable per user later

    def start(self):
        """Start the scheduler"""
        # Schedule daily digest at 9:00 AM
        self.scheduler.add_job(
            self.daily_digest_job,
            CronTrigger(hour=9, minute=0),
            id="daily_digest",
            replace_existing=True
        )
        self.scheduler.start()
        logger.info("Scheduler started. Daily digest scheduled for 9:00 AM.")

    async def daily_digest_job(self):
        """
        1. Crawl new data
        2. Generate digest of new resources from last 24h
        3. Send email
        """
        logger.info("Starting daily digest job...")
        
        # 1. Trigger Crawl (using seed data sources for now as a demo of "fresh" crawl)
        # In a real app, this might crawl a dynamic list of sources or subscriptions
        from scripts.seed_data import seed
        # Note: calling seed() might be heavy if it re-crawls everything. 
        # Ideally we should have an incremental crawl method.
        # For now, let's assume we want to crawl specific "news" sources.
        
        # Let's manually trigger ingestion for a few key sources to ensure freshness
        sources = [
            "https://github.com/trending",
            "https://blog.langchain.com",
            "https://www.anthropic.com/engineering"
            # Add X/YouTube channels here if needed
        ]
        
        logger.info("Crawling sources for daily update...")
        for url in sources:
            await self.ingestion_pipeline.ingest_url(url)
            
        # 2. Query new resources (last 24h)
        yesterday = datetime.now() - timedelta(days=1)
        db = SessionLocal()
        try:
            # Get latest 5 resources
            new_resources = db.query(Resource).filter(
                Resource.published_at >= yesterday
            ).order_by(desc(Resource.published_at)).limit(5).all()
            
            if not new_resources:
                logger.info("No new resources found for digest.")
                return

            # 3. Format Email Content
            subject = f"AI Learning Daily Digest - {datetime.now().strftime('%Y-%m-%d')}"
            content = "Here are the latest AI resources for you:\n\n"
            
            for res in new_resources:
                content += f"[{res.type}] {res.title}\n"
                content += f"URL: {res.url}\n"
                content += f"Summary: {res.summary}\n"
                if res.recommended_reason:
                    content += f"Why: {res.recommended_reason}\n"
                content += "-" * 30 + "\n"
            
            content += "\nHappy Learning!\nAI Learning Platform"
            
            # 4. Send Email
            self.email_service.send_notification(self.notification_email, subject, content)
            logger.info("Daily digest email sent.")
            
        except Exception as e:
            logger.error(f"Failed to generate daily digest: {e}")
        finally:
            db.close()
