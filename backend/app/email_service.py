import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from datetime import datetime
from pathlib import Path
from backend.app.config import MOCK_EMAIL_DIR, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM

logger = logging.getLogger("email_service")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AI Matching Alert: Lost Item Found!</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f3f4f6;
            margin: 0;
            padding: 20px;
            color: #1f2937;
        }}
        .container {{
            max-width: 600px;
            background: #ffffff;
            margin: 0 auto;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            border: 1px solid #e5e7eb;
        }}
        .header {{
            background: linear-gradient(135deg, #4f46e5, #6366f1);
            color: #ffffff;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 700;
        }}
        .header p {{
            margin: 5px 0 0 0;
            opacity: 0.9;
            font-size: 14px;
        }}
        .content {{
            padding: 30px 20px;
        }}
        .alert-bar {{
            background-color: #eef2ff;
            border-left: 4px solid #4f46e5;
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 25px;
            font-size: 15px;
            font-weight: 500;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 25px;
        }}
        .card {{
            background: #f9fafb;
            border: 1px solid #f3f4f6;
            border-radius: 8px;
            padding: 15px;
        }}
        .card h3 {{
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 16px;
            color: #4f46e5;
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 5px;
        }}
        .card p {{
            margin: 5px 0;
            font-size: 13px;
            line-height: 1.4;
        }}
        .img-container {{
            margin-top: 10px;
            text-align: center;
        }}
        .item-img {{
            max-width: 100%;
            max-height: 150px;
            border-radius: 6px;
            object-fit: cover;
            border: 1px solid #e5e7eb;
        }}
        .no-img {{
            font-size: 12px;
            color: #9ca3af;
            font-style: italic;
            padding: 20px 0;
        }}
        .instructions {{
            background: #fffbeb;
            border: 1px solid #fde68a;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
        }}
        .instructions h3 {{
            margin-top: 0;
            color: #b45309;
            font-size: 15px;
        }}
        .instructions p {{
            margin: 5px 0;
            font-size: 13px;
            line-height: 1.4;
        }}
        .button-container {{
            text-align: center;
            margin-top: 30px;
        }}
        .btn {{
            background-color: #4f46e5;
            color: #ffffff !important;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            font-size: 14px;
            display: inline-block;
            box-shadow: 0 4px 6px rgba(79, 70, 229, 0.2);
        }}
        .footer {{
            background-color: #f9fafb;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #9ca3af;
            border-top: 1px solid #e5e7eb;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>We Found a Match!</h1>
            <p>AI Matching Alert from AI Lost & Found Assistant</p>
        </div>
        <div class="content">
            <div class="alert-bar">
                Good news, {owner_name}! Our AI system matched your reported lost item with a confidence score of <strong>{confidence:.1f}%</strong>.
            </div>

            <div style="display: flex; gap: 16px; margin-bottom: 20px;">
                <!-- Lost Item details -->
                <div class="card" style="flex: 1;">
                    <h3>Your Lost Item</h3>
                    <p><strong>Name:</strong> {lost_name}</p>
                    <p><strong>Description:</strong> {lost_description}</p>
                    <p><strong>Date Lost:</strong> {lost_date}</p>
                    <p><strong>Location:</strong> {lost_location}</p>
                    <div class="img-container">
                        {lost_img_html}
                    </div>
                </div>

                <!-- Found Item details -->
                <div class="card" style="flex: 1;">
                    <h3>Matched Found Item</h3>
                    <p><strong>Description:</strong> {found_description}</p>
                    <p><strong>Date Found:</strong> {found_date}</p>
                    <p><strong>Location Found:</strong> {found_location}</p>
                    <div class="img-container">
                        {found_img_html}
                    </div>
                </div>
            </div>

            <div class="instructions">
                <h3>Collection Instructions</h3>
                <p>Please log in to your dashboard to review this match. If this is indeed your item, you can approve the match and proceed to the designated collection counter at <strong>{found_location}</strong> to claim it.</p>
                <p><strong>Verification Code:</strong> LF-MATCH-{match_id}</p>
                <p><em>Note: You must bring a valid ID and be prepared to unlock/verify ownership of the item.</em></p>
            </div>

            <div class="button-container">
                <a href="http://localhost:8000/#/matches" class="btn">View Match Dashboard</a>
            </div>
        </div>
        <div class="footer">
            &copy; {year} AI Lost & Found Assistant. All rights reserved.<br>
            This is an automated notification. Please do not reply directly to this email.
        </div>
    </div>
</body>
</html>
"""

def generate_image_html(image_url: str) -> str:
    if image_url:
        # If it's a relative path, point to backend local server
        url = image_url
        if not image_url.startswith("http"):
            url = f"http://localhost:8000/{image_url}"
        return f'<img class="item-img" src="{url}" alt="Item image"/>'
    return '<div class="no-img">No Image Uploaded</div>'

def send_match_notification(match, db_session) -> bool:
    """
    Renders the HTML email template and writes it to the local mock folder.
    Attempts to send a real email via SMTP if configured.
    """
    try:
        lost_item = match.lost_item
        found_item = match.found_item
        owner = lost_item.owner
        
        # Render details
        lost_date_str = lost_item.date_lost.strftime("%Y-%m-%d")
        found_date_str = found_item.date_found.strftime("%Y-%m-%d")
        
        lost_img_html = generate_image_html(lost_item.image_path)
        found_img_html = generate_image_html(found_item.image_path)
        
        html_content = HTML_TEMPLATE.format(
            owner_name=owner.username,
            confidence=match.confidence_score * 100,
            lost_name=lost_item.name,
            lost_description=lost_item.description,
            lost_date=lost_date_str,
            lost_location=lost_item.location,
            lost_img_html=lost_img_html,
            found_description=found_item.description,
            found_date=found_date_str,
            found_location=found_item.location,
            found_img_html=found_img_html,
            match_id=match.id,
            year=datetime.now().year
        )
        
        # 1. Save locally as mock email for preview
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"match_email_{match.id}_{timestamp}.html"
        filepath = MOCK_EMAIL_DIR / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        logger.info(f"Simulated email match notification saved to {filepath}")
        print(f"\n[EMAIL SIMULATION] Match email written to {filepath.resolve()}\n")
        
        # 2. Send via SMTP if host is provided
        if SMTP_HOST:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"AI Matching Alert: We found a potential match for your lost {lost_item.name}!"
            msg['From'] = SMTP_FROM
            msg['To'] = owner.email
            
            # Simple text fallback
            text_fallback = (
                f"Hi {owner.username},\n\n"
                f"We found a potential match for your lost item '{lost_item.name}' "
                f"with a confidence of {match.confidence_score * 100:.1f}%.\n\n"
                f"Please log in to your dashboard to review this match.\n"
                f"Match ID: LF-MATCH-{match.id}\n"
            )
            
            part1 = MIMEText(text_fallback, 'plain')
            part2 = MIMEText(html_content, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                if SMTP_USER and SMTP_PASSWORD:
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, owner.email, msg.as_string())
            logger.info(f"Real email sent to {owner.email} via SMTP")
            
        return True
    except Exception as e:
        logger.error(f"Error in send_match_notification: {str(e)}")
        print(f"[EMAIL ERROR] Failed to send email: {str(e)}")
        return False
