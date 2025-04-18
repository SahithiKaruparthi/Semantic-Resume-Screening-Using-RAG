
# agents/scheduler.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime, timedelta

def send_invite(email, job_title):
    """
    Send interview invitation email
    """
    # For development/demo purposes, just print the invitation
    # In production, this would connect to email service or calendar API
    
    # Generate a fake interview date (1 week from now)
    interview_date = datetime.now() + timedelta(days=7)
    formatted_date = interview_date.strftime("%A, %B %d, %Y at %I:%M %p")
    
    print(f"\n--- INTERVIEW INVITATION (DEMO) ---")
    print(f"To: {email}")
    print(f"Subject: Interview Invitation - {job_title}")
    print(f"We're pleased to invite you to interview for the {job_title} position.")
    print(f"Your interview is scheduled for: {formatted_date}")
    print(f"Please confirm your availability.")
    print(f"--- END OF INVITATION ---\n")
    
    # In a real implementation, you would use something like:
    """
    if os.getenv("EMAIL_ENABLED") == "True":
        sender_email = os.getenv("SENDER_EMAIL")
        password = os.getenv("EMAIL_PASSWORD")
        
        # Create message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = email
        message["Subject"] = f"Interview Invitation - {job_title}"
        
        # Email body
        body = f'''
        Dear Candidate,
        
        We're pleased to invite you to interview for the {job_title} position.
        
        Your interview is scheduled for: {formatted_date}
        
        Please confirm your availability by replying to this email.
        
        Best regards,
        HR Team
        '''
        
        message.attach(MIMEText(body, "plain"))
        
        # Send email
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, password)
            server.send_message(message)
            server.quit()
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    """
    
    return True