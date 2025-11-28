"""
Email utility functions for sending notifications to users
"""
from django.core.mail import send_mail, send_mass_mail
from django.conf import settings
from .models import CustomUser
from .mongodb import mongodb
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_chatbot_response_email(chat_message, response_text, title=None, author=None, description=None):
    """
    Send email to all users when chatbot sends a response
    
    Args:
        chat_message: The chat message/query
        response_text: The chatbot's response text
        title: Optional title for the notification
        author: Optional author name
        description: Optional description
    """
    try:
        # Get all active users with email addresses from MongoDB
        if mongodb.is_connected():
            users_cursor = mongodb.users.find({
                'is_active': True,
                'email': {'$exists': True, '$ne': ''}
            })
            users_list = list(users_cursor)
            
            if not users_list:
                logger.warning("No active users with email addresses found in MongoDB")
                return False
            
            recipient_list = [user['email'] for user in users_list]
            logger.info(f"Found {len(recipient_list)} users in MongoDB: {recipient_list}")
        else:
            # Fallback to Django database if MongoDB not connected
            users = CustomUser.objects.filter(is_active=True).exclude(email='')
            
            if not users.exists():
                logger.warning("No active users with email addresses found")
                return False
            
            recipient_list = [user.email for user in users]
            logger.info(f"Found {len(recipient_list)} users in Django DB: {recipient_list}")
        
        # Get current date and time
        from datetime import datetime
        now = datetime.now()
        date_str = now.strftime("%B %d, %Y")
        time_str = now.strftime("%I:%M %p")
        
        # Use provided values or defaults
        email_title = title or f"New Fact-Check Response"
        email_author = author or "SatyaMatrix AI"
        email_description = description or "A new fact-check response is available for your query."
        
        # Prepare email content
        subject = f'SatyaMatrix: {email_title}'
        
        # HTML email content with black background and white text
        html_message = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="margin: 0; padding: 0; background-color: #000000; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #000000; padding: 20px;">
                    <tr>
                        <td align="center">
                            <table width="600" cellpadding="0" cellspacing="0" style="background-color: #000000; border: 2px solid #333333; border-radius: 12px; overflow: hidden;">
                                
                                <!-- Header -->
                                <tr>
                                    <td style="background-color: #111111; padding: 30px; text-align: center; border-bottom: 2px solid #333333;">
                                        <h1 style="color: #ffffff; margin: 0; font-size: 32px; font-weight: bold;">SatyaMatrix</h1>
                                        <p style="color: #888888; margin: 10px 0 0 0; font-size: 14px;">The Network of Truth</p>
                                    </td>
                                </tr>
                                
                                <!-- Title Section -->
                                <tr>
                                    <td style="background-color: #000000; padding: 30px;">
                                        <h2 style="color: #ffffff; margin: 0 0 20px 0; font-size: 24px; font-weight: bold;">{email_title}</h2>
                                        
                                        <!-- Metadata -->
                                        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 20px;">
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <span style="color: #888888; font-size: 14px;">Author:</span>
                                                    <span style="color: #ffffff; font-size: 14px; margin-left: 10px;">{email_author}</span>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <span style="color: #888888; font-size: 14px;">Date:</span>
                                                    <span style="color: #ffffff; font-size: 14px; margin-left: 10px;">{date_str}</span>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <span style="color: #888888; font-size: 14px;">Time:</span>
                                                    <span style="color: #ffffff; font-size: 14px; margin-left: 10px;">{time_str}</span>
                                                </td>
                                            </tr>
                                        </table>
                                        
                                        <!-- Description -->
                                        <div style="background-color: #111111; border: 1px solid #333333; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                                            <h3 style="color: #ffffff; margin: 0 0 10px 0; font-size: 16px;">Description</h3>
                                            <p style="color: #cccccc; margin: 0; line-height: 1.6; font-size: 14px;">{email_description}</p>
                                        </div>
                                        
                                        <!-- Query Section -->
                                        <div style="background-color: #111111; border: 1px solid #333333; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                                            <h3 style="color: #ffffff; margin: 0 0 10px 0; font-size: 16px;">Query</h3>
                                            <p style="color: #cccccc; margin: 0; line-height: 1.6; font-size: 14px;">{chat_message}</p>
                                        </div>
                                        
                                        <!-- Response Section -->
                                        <div style="background-color: #111111; border: 1px solid #333333; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                                            <h3 style="color: #ffffff; margin: 0 0 10px 0; font-size: 16px;">Response</h3>
                                            <p style="color: #cccccc; margin: 0; line-height: 1.6; font-size: 14px;">{response_text[:500]}{'...' if len(response_text) > 500 else ''}</p>
                                        </div>
                                        
                                        <!-- CTA Button -->
                                        <table width="100%" cellpadding="0" cellspacing="0">
                                            <tr>
                                                <td align="center">
                                                    <a href="{settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'http://localhost:8000'}/auth/chat/" 
                                                       style="display: inline-block; background-color: #ffffff; color: #000000; text-decoration: none; 
                                                              padding: 14px 40px; border-radius: 6px; font-weight: bold; font-size: 16px;">
                                                        View Full Conversation
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Footer -->
                                <tr>
                                    <td style="background-color: #111111; padding: 20px; text-align: center; border-top: 2px solid #333333;">
                                        <p style="color: #666666; margin: 0; font-size: 12px;">
                                            This is an automated notification from SatyaMatrix<br>
                                            © 2025 SatyaMatrix - The Network of Truth
                                        </p>
                                    </td>
                                </tr>
                                
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
        
        # Plain text version
        plain_message = f"""
SatyaMatrix - The Network of Truth

{email_title}

Author: {email_author}
Date: {date_str}
Time: {time_str}

Description:
{email_description}

Query:
{chat_message}

Response:
{response_text[:500]}{'...' if len(response_text) > 500 else ''}

View full conversation at: {settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'http://localhost:8000'}/auth/chat/

---
This is an automated notification from SatyaMatrix
© 2025 SatyaMatrix - The Network of Truth
        """
        
        # Send email to all users (one by one to ensure delivery)
        logger.info(f"Sending email to {len(recipient_list)} users: {recipient_list}")
        
        # Send individual emails to each user
        success_count = 0
        failed_count = 0
        
        for user_email in recipient_list:
            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user_email],  # Send to one user at a time
                    html_message=html_message,
                    fail_silently=False,
                )
                success_count += 1
                logger.info(f"✅ Email sent to {user_email}")
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ Failed to send to {user_email}: {str(e)}")
        
        logger.info(f"Email sending complete: {success_count} succeeded, {failed_count} failed")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False


def send_bulk_notification(subject, message, html_message=None):
    """
    Send bulk notification to all active users
    
    Args:
        subject: Email subject
        message: Plain text message
        html_message: Optional HTML message
    """
    try:
        # Get all active users with email addresses from MongoDB
        if mongodb.is_connected():
            users_cursor = mongodb.users.find({
                'is_active': True,
                'email': {'$exists': True, '$ne': ''}
            })
            users_list = list(users_cursor)
            
            if not users_list:
                logger.warning("No active users with email addresses found in MongoDB")
                return False
            
            recipient_list = [user['email'] for user in users_list]
            logger.info(f"Found {len(recipient_list)} users in MongoDB for bulk notification")
        else:
            # Fallback to Django database
            users = CustomUser.objects.filter(is_active=True).exclude(email='')
            
            if not users.exists():
                logger.warning("No active users with email addresses found")
                return False
            
            recipient_list = [user.email for user in users]
            logger.info(f"Found {len(recipient_list)} users in Django DB for bulk notification")
        
        logger.info(f"Sending bulk notification to {len(recipient_list)} users")
        
        # Send individual emails to each user
        success_count = 0
        failed_count = 0
        
        for user_email in recipient_list:
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user_email],
                    html_message=html_message,
                    fail_silently=False,
                )
                success_count += 1
                logger.info(f"✅ Bulk email sent to {user_email}")
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ Failed to send to {user_email}: {str(e)}")
        
        logger.info(f"Bulk email complete: {success_count} succeeded, {failed_count} failed")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error sending bulk email: {str(e)}")
        return False
