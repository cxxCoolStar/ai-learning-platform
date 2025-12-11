import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.settings = get_settings()
        self.smtp_server = "smtp.qq.com"
        self.smtp_port = 465
        # These should be in settings, but for now we default or expect env vars
        self.user = self.settings.MYSQL_USER # Reusing user var or define new? 
        # Better to define generic EMAIL vars in settings, I will update config logic later
        # For now I'll assume they are passed or fetched from Env
        
    def send_notification(self, to_email: str, subject: str, content: str):
        """
        Send email notification using QQ Mail (SMTP_SSL)
        """
        sender = "your_qq_email@qq.com" # Needs config
        password = "your_auth_code"     # Needs config
        
        try:
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(content, 'plain'))
            
            # Connect to QQ Mail
            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
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
