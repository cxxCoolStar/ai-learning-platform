import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.settings = get_settings()
        self.smtp_server = self.settings.MAIL_HOST
        self.smtp_port = self.settings.MAIL_PORT
        self.user = self.settings.MAIL_USERNAME
        self.password = self.settings.MAIL_PASSWORD
        
    def send_notification(self, to_email: str, subject: str, content: str):
        """
        Send email notification using QQ Mail (SMTP_SSL)
        """
        sender = self.user
        password = self.password
        
        try:
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(content, 'plain'))
            
            # Connect to QQ Mail
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                
            server.login(sender, password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

# Function to simulate/mock for now if no creds
def send_update_notification(resource_title: str):
    logger.info(f"MOCK: Sending email notification for new resource: {resource_title}")
    # Real implementation would call EmailService().send_notification(...)
