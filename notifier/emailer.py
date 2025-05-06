import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any

class EmailNotifier:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def notify(self, items: List[Dict[str, Any]]) -> None:
        """
        Send email notifications for processed items
        """
        if not items:
            self.logger.info("No items to notify about")
            return
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.sender_email
            msg['To'] = ', '.join(self.config.recipient_emails)
            msg['Subject'] = f"New Feed Items ({len(items)})"
            
            # Create email body
            body = "New items have been processed:\n\n"
            for item in items:
                body += f"Title: {item['title']}\n"
                body += f"Link: {item['link']}\n"
                body += f"Summary: {item['ai_summary']}\n"
                body += f"Source: {item['source']}\n"
                body += "-" * 80 + "\n\n"
                
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.sender_email, self.config.smtp_password)
                server.send_message(msg)
                
            self.logger.info(f"Sent notification email for {len(items)} items")
            
        except Exception as e:
            self.logger.error(f"Error sending notification email: {str(e)}")
            raise 