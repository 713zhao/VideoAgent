"""
Test email functionality - sends a test email to verify configuration.
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import load_config
from app.email_sender import send_summary_email
from datetime import datetime

def main():
    print("\n" + "="*60)
    print("📧 EMAIL CONFIGURATION TEST")
    print("="*60)
    
    # Load config
    try:
        cfg = load_config('config.yaml')
    except Exception as e:
        print(f"\n❌ Error loading config: {e}")
        return
    
    # Check if email is enabled
    if not cfg.email.enabled:
        print("\n⚠️ Email is DISABLED in config.yaml")
        print("Set email.enabled to true to test")
        return
    
    # Display current configuration
    print("\n📋 Current Configuration:")
    print(f"  From: {cfg.email.from_email} ({cfg.email.from_name})")
    print(f"  To: {cfg.email.to_email}")
    print(f"  SMTP: {cfg.email.smtp.host}:{cfg.email.smtp.port}")
    
    # Check password configuration
    has_direct_password = bool(cfg.email.smtp.password)
    has_env_password = bool(os.environ.get(cfg.email.smtp.password_env))
    
    if has_direct_password:
        print(f"  Password: ✓ Set directly in config.yaml")
    elif has_env_password:
        print(f"  Password: ✓ Set in environment variable ({cfg.email.smtp.password_env})")
    else:
        print(f"  Password: ✗ Not set")
    
    # Check if password is configured
    if not has_direct_password and not has_env_password:
        print(f"\n❌ No password configured!")
        print("\nOption 1: Set directly in config.yaml (easier)")
        print("  email:")
        print("    smtp:")
        print("      password: 'your-app-password'")
        print("\nOption 2: Use environment variable (more secure)")
        print(f"  PowerShell: $env:{cfg.email.smtp.password_env} = 'your-app-password'")
        print(f"  Bash: export {cfg.email.smtp.password_env}='your-app-password'")
        print("\nGenerate Gmail App Password at:")
        print("  https://myaccount.google.com/apppasswords")
        return
    
    if has_direct_password:
        print("\n✓ Password configured in config.yaml")
    else:
        print(f"\n✓ Password configured in environment variable")
    
    # Create test data
    test_topics = [
        {
            'title': 'Test Topic #1: AI Makes Breakthrough in Quantum Computing',
            'url': 'https://example.com/topic1',
            'score': 1234,
            'source': 'Test Source',
            'comments_count': 567,
            'author': 'TestUser1',
            'excerpt': 'This is a test excerpt for the first topic. It demonstrates how topics will appear in the email with proper formatting and links.'
        },
        {
            'title': 'Test Topic #2: New LLM Model Achieves 99% Accuracy',
            'url': 'https://example.com/topic2',
            'score': 890,
            'source': 'Reddit r/MachineLearning',
            'comments_count': 234,
            'author': 'TestUser2',
            'excerpt': 'Another test excerpt showing how multiple topics look in the email. Each topic gets its own styled box with metadata.'
        },
        {
            'title': 'Test Topic #3: Debate Over AI Safety Regulations',
            'url': 'https://example.com/topic3',
            'score': 456,
            'source': 'Hacker News',
            'comments_count': 123,
            'author': 'TestUser3',
            'excerpt': 'A third test topic to show the complete format with all three topics rendered in the email.'
        }
    ]
    
    test_summary = {
        'narration': '''Welcome to your test AI Daily Brief!

This is a test email to verify your email configuration is working correctly. If you're reading this, congratulations - everything is set up properly!

Here's what the AI summary would normally include:
• Analysis of the top 3 topics
• Key points from discussions
• Interesting insights from comments

The actual emails will contain real AI-generated summaries of hot topics from Reddit, Hacker News, and other sources.

Stay tuned for real AI updates!''',
        'hashtags': ['#test', '#ai', '#dailybrief', '#success']
    }
    
    # Ask for confirmation
    print("\n" + "="*60)
    print("📨 READY TO SEND TEST EMAIL")
    print("="*60)
    print(f"\nThis will send a test email to: {cfg.email.to_email}")
    print("\nThe email will include:")
    print("  • 3 sample topics")
    print("  • Test AI summary")
    print("  • HTML formatting (with plain text fallback)")
    
    response = input("\nSend test email? (y/n): ").lower().strip()
    
    if response != 'y':
        print("\n⚠️ Test cancelled")
        return
    
    # Send test email
    print("\n📤 Sending test email...")
    
    success = send_summary_email(
        to_email=cfg.email.to_email,
        from_email=cfg.email.from_email,
        from_name=cfg.email.from_name,
        subject=f"TEST - AI Daily Bot - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        smtp_config=cfg.email.smtp.model_dump(),
        topics=test_topics,
        summary=test_summary,
        include_topics=cfg.email.include_topics,
        include_summary=cfg.email.include_summary
    )
    
    if success:
        print("\n" + "="*60)
        print("✅ SUCCESS!")
        print("="*60)
        print(f"\nTest email sent to: {cfg.email.to_email}")
        print("\n📬 Check your inbox (including spam/junk folder)")
        print("\nIf you received the email, your configuration is correct!")
        print("The bot will now send automatic summaries when you run:")
        print("  python run.py")
    else:
        print("\n" + "="*60)
        print("❌ FAILED")
        print("="*60)
        print("\nCommon issues:")
        print("  1. Wrong email/password")
        print("  2. Need Gmail App Password (not regular password)")
        print("  3. 2-Step Verification not enabled")
        print("  4. Firewall blocking port 587")
        print("\nSee EMAIL_SETUP_GUIDE.md for detailed troubleshooting")

if __name__ == "__main__":
    main()
