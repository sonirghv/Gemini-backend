"""
Email Service - SMTP email sending functionality
Handles OTP emails, notifications, and email verification
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple
from utils.env_utils import get_env_str, get_env_int, get_env_bool
from utils.logging_config import get_logger

logger = get_logger(__name__)

class EmailService:
    """Service for sending emails via SMTP"""
    
    def __init__(self):
        # Environment variables
        self.smtp_server = get_env_str("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = get_env_int("SMTP_PORT", 587)
        self.smtp_username = get_env_str("SMTP_USERNAME", "")
        self.smtp_password = get_env_str("SMTP_PASSWORD", "")
        self.from_email = get_env_str("FROM_EMAIL", self.smtp_username)
        self.from_name = get_env_str("FROM_NAME", "Gemini Clone")
        self.use_tls = get_env_bool("SMTP_USE_TLS", True)
        self.enabled = get_env_bool("EMAIL_ENABLED", True)
        
        # Validate configuration
        if self.enabled and not all([self.smtp_server, self.smtp_username, self.smtp_password]):
            logger.warning("Email service not properly configured - emails will be disabled")
            self.enabled = False
    
    def _create_smtp_connection(self) -> Optional[smtplib.SMTP]:
        """Create and authenticate SMTP connection"""
        try:
            # Create SMTP connection
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.use_tls:
                # Create secure context and start TLS
                context = ssl.create_default_context()
                server.starttls(context=context)
            
            # Login to server
            server.login(self.smtp_username, self.smtp_password)
            
            return server
            
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            return None
    
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Send email with HTML and optional text content"""
        
        if not self.enabled:
            logger.info(f"Email service disabled - would send to {to_email}: {subject}")
            return True, "Email service disabled"
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Create SMTP connection and send
            server = self._create_smtp_connection()
            if not server:
                return False, "Failed to connect to SMTP server"
            
            try:
                server.send_message(message)
                logger.info(f"Email sent successfully to {to_email}")
                return True, "Email sent successfully"
            finally:
                server.quit()
                
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False, f"Failed to send email: {str(e)}"
    
    def send_otp_email(self, to_email: str, otp_code: str, purpose: str = "verification") -> Tuple[bool, str]:
        """Send OTP verification email"""
        
        app_name = get_env_str("APP_NAME", "Leagal AI")
        
        subject = f"Your Leagal AI Verification Code"
        
        # HTML email template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verification Code</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .otp-code {{
                    background: #fff;
                    border: 2px solid #667eea;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    margin: 20px 0;
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    color: #667eea;
                }}
                .warning {{
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 20px 0;
                    color: #856404;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    color: #666;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{app_name}</h1>
                <p>Email Verification</p>
            </div>
            <div class="content">
                <h2>Hello!</h2>
                <p>You requested a verification code for your Leagal AI account. Please use the code below to complete your {purpose}:</p>
                
                <div class="otp-code">
                    {otp_code}
                </div>
                
                <div class="warning">
                    <strong>Important:</strong>
                    <ul>
                        <li>This code will expire in 10 minutes</li>
                        <li>Do not share this code with anyone</li>
                        <li>If you didn't request this code, please ignore this email</li>
                    </ul>
                </div>
                
                <p>If you have any questions or need assistance, please contact our support team.</p>
                
                <p>Best regards,<br>The Leagal AI Team</p>
            </div>
            <div class="footer">
                <p>This is an automated message, please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Leagal AI - Email Verification
        
        Hello!
        
        You requested a verification code for your Leagal AI account.
        
        Your verification code is: {otp_code}
        
        This code will expire in 10 minutes.
        Do not share this code with anyone.
        
        If you didn't request this code, please ignore this email.
        
        Best regards,
        The Leagal AI Team
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_welcome_email(self, to_email: str, username: str) -> Tuple[bool, str]:
        """Send welcome email to new users"""
        
        app_name = get_env_str("APP_NAME", "Gemini Clone")
        
        subject = f"Welcome to {app_name}!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    color: #666;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Welcome to Leagal AI!</h1>
            </div>
            <div class="content">
                <h2>Hello {username}!</h2>
                <p>Welcome to Leagal AI! We're excited to have you on board.</p>
                
                <p>You can now start chatting with our AI assistant and explore all the features we have to offer.</p>
                
                <p>If you have any questions or need help getting started, don't hesitate to reach out to our support team.</p>
                
                <p>Happy chatting!</p>
                
                <p>Best regards,<br>The Leagal AI Team</p>
            </div>
            <div class="footer">
                <p>This is an automated message, please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Leagal AI!
        
        Hello {username}!
        
        Welcome to Leagal AI! We're excited to have you on board.
        
        You can now start chatting with our AI assistant and explore all the features we have to offer.
        
        If you have any questions or need help getting started, don't hesitate to reach out to our support team.
        
        Happy chatting!
        
        Best regards,
        The Leagal AI Team
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test SMTP connection"""
        if not self.enabled:
            return False, "Email service is disabled"
        
        try:
            server = self._create_smtp_connection()
            if server:
                server.quit()
                return True, "SMTP connection successful"
            else:
                return False, "Failed to establish SMTP connection"
        except Exception as e:
            return False, f"SMTP connection test failed: {str(e)}"

# Global service instance
email_service = EmailService() 