"""
Email notification module for sending AI summary updates.
"""
from __future__ import annotations
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import os

def send_summary_email(
    to_email: str,
    from_email: str,
    from_name: str,
    subject: str,
    smtp_config: Dict[str, Any],
    topics: List[Dict[str, Any]],
    summary: Dict[str, Any],
    include_topics: bool = True,
    include_summary: bool = True,
) -> bool:
    """
    Send an email with AI summary of hot topics.
    
    Args:
        to_email: Recipient email address
        from_email: Sender email address
        from_name: Sender display name
        subject: Email subject
        smtp_config: SMTP server configuration
        topics: List of topic dictionaries
        summary: Summary bundle from AI
        include_topics: Include raw topic data
        include_summary: Include AI summary
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = to_email
        
        # Build email content
        html_content = build_html_email(topics, summary, include_topics, include_summary)
        text_content = build_text_email(topics, summary, include_topics, include_summary)
        
        # Attach both plain text and HTML versions
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Get SMTP password: try direct config first, then environment variable
        password = smtp_config.get('password', '')
        if not password:
            password = os.environ.get(smtp_config['password_env'], '')
        if not password:
            print(f"⚠️ Warning: No password found. Set 'password' in config.yaml or {smtp_config['password_env']} environment variable")
            return False
        
        # Connect and send
        print(f"📧 Connecting to {smtp_config['host']}:{smtp_config['port']}...")
        
        if smtp_config.get('use_tls', True):
            server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
            server.starttls()
        else:
            server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
        
        server.login(from_email, password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def build_html_email(topics: List[Dict], summary: Dict, include_topics: bool, include_summary: bool) -> str:
    """Build HTML email content."""
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #e01b24;
            margin-top: 0;
            border-bottom: 3px solid #e01b24;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #00d4aa;
            margin-top: 25px;
        }}
        .topic {{
            background: #f8f9fa;
            border-left: 4px solid #e01b24;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .topic-title {{
            font-weight: bold;
            font-size: 16px;
            color: #1a1a1b;
            margin-bottom: 8px;
        }}
        .topic-meta {{
            font-size: 14px;
            color: #666;
            margin: 5px 0;
        }}
        .source {{
            display: inline-block;
            background: #e01b24;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }}
        .summary {{
            background: #f0f8ff;
            border-left: 4px solid #00d4aa;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
            white-space: pre-wrap;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #666;
            text-align: center;
        }}
        a {{
            color: #00d4aa;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Daily Brief</h1>
        <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
"""
    
    # Show AI Summary FIRST
    if include_summary and summary:
        narration = summary.get('narration', '')
        if narration:
            html += f"""
        <h2>📝 AI Summary</h2>
        <div class="summary">{narration}</div>
"""
        
        hashtags = summary.get('hashtags', [])
        if hashtags:
            html += f"""
        <p><strong>Hashtags:</strong> {' '.join(hashtags)}</p>
"""
    
    # Then show Topics List
    if include_topics and topics:
        html += f"""
        <h2>📊 Top {len(topics)} Topics</h2>
"""
        for i, topic in enumerate(topics, 1):
            source = topic.get('source', 'Unknown')
            title = topic.get('title', 'No title')
            url = topic.get('url', '#')
            score = topic.get('score', 0)
            comments = topic.get('comments_count', 0)
            excerpt = topic.get('excerpt', '')
            
            html += f"""
        <div class="topic">
            <div class="topic-title">#{i}: {title}</div>
            <div class="topic-meta">
                <span class="source">{source}</span> • 
                ⭐ {score} points • 
                💬 {comments} comments
            </div>
"""
            if excerpt:
                html += f"""
            <p style="margin-top: 10px; font-size: 14px; color: #555;">{excerpt[:200]}...</p>
"""
            html += f"""
            <div style="margin-top: 10px;">
                <a href="{url}" target="_blank">Read More →</a>
            </div>
        </div>
"""
    
    html += """
        <div class="footer">
            <p>This email was generated automatically by AI Daily Bot</p>
            <p>Powered by Reddit, Hacker News & AI</p>
        </div>
    </div>
</body>
</html>
"""
    return html

def build_text_email(topics: List[Dict], summary: Dict, include_topics: bool, include_summary: bool) -> str:
    """Build plain text email content."""
    
    text = f"""
AI DAILY BRIEF
{'='*60}
Date: {datetime.now().strftime('%B %d, %Y')}

"""
    
    # Show AI Summary FIRST
    if include_summary and summary:
        narration = summary.get('narration', '')
        if narration:
            text += "AI SUMMARY\n"
            text += "="*60 + "\n"
            text += narration + "\n\n"
        
        hashtags = summary.get('hashtags', [])
        if hashtags:
            text += f"Hashtags: {' '.join(hashtags)}\n\n"
    
    # Then show Topics List
    if include_topics and topics:
        text += f"TOP {len(topics)} TOPICS\n"
        text += "="*60 + "\n\n"
        
        for i, topic in enumerate(topics, 1):
            source = topic.get('source', 'Unknown')
            title = topic.get('title', 'No title')
            url = topic.get('url', '#')
            score = topic.get('score', 0)
            comments = topic.get('comments_count', 0)
            excerpt = topic.get('excerpt', '')
            
            text += f"#{i}: {title}\n"
            text += f"Source: {source}\n"
            text += f"Score: {score} | Comments: {comments}\n"
            if excerpt:
                text += f"Excerpt: {excerpt[:150]}...\n"
            text += f"URL: {url}\n"
            text += "-"*60 + "\n\n"
    
    text += "\n" + "="*60 + "\n"
    text += "This email was generated automatically by AI Daily Bot\n"
    text += "Powered by Reddit, Hacker News & AI\n"
    
    return text
