import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import desc
from app.services.ingestion import IngestionPipeline
from app.services.email_service import EmailService
from app.db.session import SessionLocal
from app.models.sql_models import Resource
from app.core.config import get_settings
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.ingestion_pipeline = None
        self.email_service = None
        self.notification_email = "1848505943@qq.com" # Could be configurable per user later
        self.settings = get_settings()
        
        try:
            self.llm = ChatOpenAI(
                model=self.settings.LLM_MODEL,
                api_key=self.settings.OPENAI_API_KEY,
                base_url=self.settings.OPENAI_BASE_URL
            )
        except Exception:
            self.llm = None

    def get_ingestion_pipeline(self):
        if not self.ingestion_pipeline:
            self.ingestion_pipeline = IngestionPipeline()
        return self.ingestion_pipeline

    def get_email_service(self):
        if not self.email_service:
            self.email_service = EmailService()
        return self.email_service

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
        sources = [
            "https://github.com/trending",
            "https://blog.langchain.com",
            "https://www.anthropic.com/engineering"
        ]
        
        logger.info("Crawling sources for daily update...")
        for url in sources:
            await self.get_ingestion_pipeline().ingest_url(url)
            
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

            # 3. Generate Digest Summary with LLM
            digest_intro = "以下是为您精选的今日 AI 技术动态，涵盖了最新的工具、文章和研究成果。"
            if self.llm:
                try:
                    resource_list_text = "\n".join([f"- {r.title}: {r.summary}" for r in new_resources])
                    prompt = f"""
                    你是 AI Learning Platform 的智能助手。请根据以下今日更新的 AI 资源列表，写一段简短、吸引人且专业的每日摘要（Daily Digest Intro）。
                    
                    受众：AI 工程师和研究员。
                    语言：中文。
                    风格：专业、简洁、富有洞察力。
                    字数：100字左右。
                    
                    资源列表：
                    {resource_list_text}
                    """
                    response = await self.llm.ainvoke(prompt)
                    digest_intro = response.content
                except Exception as e:
                    logger.error(f"Failed to generate digest summary: {e}")

            # 4. Format Email Content (HTML & Plain)
            subject = f"AI Learning Daily Digest - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Plain Text
            plain_content = f"{digest_intro}\n\n"
            for res in new_resources:
                plain_content += f"[{res.type}] {res.title}\nURL: {res.url}\nSummary: {res.summary}\n"
                if res.recommended_reason:
                    plain_content += f"Why: {res.recommended_reason}\n"
                plain_content += "-" * 30 + "\n"
            plain_content += "\nHappy Learning!\nAI Learning Platform"
            
            # HTML Content
            items_html = ""
            for res in new_resources:
                type_color = "#4f46e5" if res.type == "Code" else "#ea580c" if res.type == "Video" else "#0ea5e9"
                items_html += f"""
                <div style="margin-bottom: 24px; padding: 16px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff;">
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <span style="background-color: {type_color}1a; color: {type_color}; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; margin-right: 8px;">
                            {res.type}
                        </span>
                        <a href="{res.url}" style="color: #1e293b; text-decoration: none; font-size: 18px; font-weight: 700;">
                            {res.title}
                        </a>
                    </div>
                    <p style="color: #475569; font-size: 14px; line-height: 1.6; margin-top: 0; margin-bottom: 12px;">
                        {res.summary}
                    </p>
                    {f'<div style="background-color: #f8fafc; padding: 12px; border-radius: 8px; font-size: 13px; color: #64748b; border-left: 3px solid #cbd5e1;"><strong>💡 推荐理由:</strong> {res.recommended_reason}</div>' if res.recommended_reason else ''}
                    <div style="margin-top: 12px; font-size: 12px; color: #94a3b8;">
                        Author: {res.author or 'Unknown'} • Published: {res.published_at.strftime('%Y-%m-%d') if res.published_at else 'Recent'}
                    </div>
                </div>
                """

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #334155; background-color: #f1f5f9; margin: 0; padding: 0;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 40px; border-radius: 16px; margin-top: 40px; margin-bottom: 40px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                    <div style="text-align: center; margin-bottom: 32px;">
                        <h1 style="color: #4f46e5; margin-bottom: 8px;">🤖 AI Learning Digest</h1>
                        <p style="color: #64748b; font-size: 14px;">{datetime.now().strftime('%B %d, %Y')}</p>
                    </div>
                    
                    <div style="background-color: #e0e7ff; padding: 20px; border-radius: 12px; margin-bottom: 32px; color: #3730a3; font-size: 15px;">
                        {digest_intro}
                    </div>
                    
                    {items_html}
                    
                    <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #94a3b8; font-size: 12px;">
                        <p>Keep learning, keep growing.</p>
                        <p>© {datetime.now().year} AI Learning Platform</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 5. Send Email
            self.get_email_service().send_notification(self.notification_email, subject, plain_content, html_content)
            logger.info("Daily digest email sent (HTML).")
            
        except Exception as e:
            logger.error(f"Failed to generate daily digest: {e}")
        finally:
            db.close()
