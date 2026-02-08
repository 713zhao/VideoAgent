# Email Notification Setup Guide

## 📧 Overview

The bot can automatically send email summaries after processing AI topics. The email includes:
- ✅ Top 3 topics with scores and links
- ✅ AI-generated summary/narration
- ✅ Beautiful HTML formatting
- ✅ Plain text fallback

## 🚀 Quick Setup

### 1. Edit config.yaml

Open `config.yaml` and update the email section:

```yaml
email:
  enabled: true
  to_email: "claw.zhao@gmail.com"  # Already set for you!
  from_email: "your-email@gmail.com"  # ⬅️ Change this
  from_name: "AI Daily Bot"
```

### 2. Generate Gmail App Password

**For Gmail users (recommended):**

1. Go to your Google Account: https://myaccount.google.com
2. Click **Security** (left sidebar)
3. Enable **2-Step Verification** (required)
4. Go to **App Passwords**: https://myaccount.google.com/apppasswords
5. Select **Mail** and device of your choice
6. Click **Generate**
7. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### 3. Set Environment Variable

**PowerShell (Windows):**
```powershell
# Set for current session
$env:EMAIL_PASSWORD = "your-app-password-here"

# OR set permanently
[System.Environment]::SetEnvironmentVariable('EMAIL_PASSWORD', 'your-app-password-here', 'User')
```

**Bash/Linux:**
```bash
export EMAIL_PASSWORD="your-app-password-here"

# OR add to ~/.bashrc
echo 'export EMAIL_PASSWORD="your-app-password-here"' >> ~/.bashrc
```

### 4. Test It!

```bash
.\env\Scripts\Activate.ps1
python run.py
```

You should receive an email after the AI summary is generated!

---

## 📝 Configuration Options

### Email Settings (config.yaml)

```yaml
email:
  # Enable/disable email notifications
  enabled: true
  
  # Who receives the email
  to_email: "claw.zhao@gmail.com"
  
  # Who sends the email (your Gmail)
  from_email: "your-email@gmail.com"
  from_name: "AI Daily Bot"
  
  # SMTP server configuration
  smtp:
    host: "smtp.gmail.com"      # Gmail SMTP server
    port: 587                    # TLS port
    use_tls: true                # Use encryption
    password_env: "EMAIL_PASSWORD"  # Environment variable name
  
  # Email content options
  subject_template: "AI Daily Brief - {date}"  # {date} is replaced
  include_topics: true          # Show raw topics
  include_summary: true         # Show AI summary
  include_video_link: false     # Future: link to video
```

---

## 🔧 Using Other Email Providers

### Outlook/Office365

```yaml
email:
  smtp:
    host: "smtp-mail.outlook.com"
    port: 587
    use_tls: true
```

### Yahoo Mail

```yaml
email:
  smtp:
    host: "smtp.mail.yahoo.com"
    port: 587
    use_tls: true
```

### Custom SMTP Server

```yaml
email:
  smtp:
    host: "smtp.yourserver.com"
    port: 587
    use_tls: true
    password_env: "YOUR_EMAIL_PASSWORD"  # Custom env var
```

---

## 📧 Email Format

### What You'll Receive

**Subject:** `AI Daily Brief - 2026-02-08`

**Content includes:**

1. **Header**
   - Date
   - Bot name

2. **Top Topics** (if enabled)
   - Title with ranking
   - Source badge (Reddit/HN)
   - Score and comment count
   - Brief excerpt
   - Link to original

3. **AI Summary** (if enabled)
   - Narration script
   - Key points
   - Hashtags

4. **Footer**
   - Bot signature
   - Source attribution

**Format:**
- Beautiful HTML with colors and styling
- Plain text fallback for email clients that don't support HTML
- Mobile-responsive design

---

## 🛡️ Security Best Practices

### ✅ DO:
- Use App Passwords (not your main password)
- Store password in environment variable
- Never commit passwords to git
- Use 2-factor authentication

### ❌ DON'T:
- Put passwords in config.yaml
- Share your app password
- Use your main email password
- Commit .env files

---

## 🧪 Testing Email

### Test with a simple script:

```python
from app.config import load_config
from app.email_sender import send_summary_email

cfg = load_config('config.yaml')

# Test data
test_topics = [{
    'title': 'Test Topic',
    'url': 'https://example.com',
    'score': 100,
    'source': 'Test',
    'comments_count': 50,
    'author': 'TestUser',
    'excerpt': 'This is a test'
}]

test_summary = {
    'narration': 'This is a test email from your AI Daily Bot!',
    'hashtags': ['#test', '#ai']
}

send_summary_email(
    to_email=cfg.email.to_email,
    from_email=cfg.email.from_email,
    from_name=cfg.email.from_name,
    subject="Test Email - AI Daily Bot",
    smtp_config=cfg.email.smtp.model_dump(),
    topics=test_topics,
    summary=test_summary,
    include_topics=True,
    include_summary=True
)
```

---

## 🐛 Troubleshooting

### "Authentication failed"
- ✅ Check you're using an **App Password**, not your regular password
- ✅ Verify the password is set in environment variable
- ✅ Make sure 2-Step Verification is enabled on your Google account

### "EMAIL_PASSWORD not set"
```powershell
# Set it:
$env:EMAIL_PASSWORD = "your-app-password"

# Verify it:
echo $env:EMAIL_PASSWORD
```

### "SMTP connection failed"
- ✅ Check your internet connection
- ✅ Verify SMTP host and port are correct
- ✅ Some networks block port 587 - try port 465
- ✅ Try disabling VPN temporarily

### "Less secure app access"
This is outdated. Gmail now requires:
- ✅ 2-Step Verification enabled
- ✅ App Passwords (not "less secure apps")

### Email not arriving
- ✅ Check spam/junk folder
- ✅ Verify recipient email is correct
- ✅ Check Gmail sent folder
- ✅ Look for bounce notifications

---

## 📊 Email Examples

### Minimal Email (only summary)
```yaml
email:
  include_topics: false
  include_summary: true
```

### Full Report (everything)
```yaml
email:
  include_topics: true
  include_summary: true
```

### Just Topics (no AI summary)
```yaml
email:
  include_topics: true
  include_summary: false
```

---

## 🔄 Integration with Pipeline

Email is sent automatically after AI summary generation:

```
1. Fetch Topics ✓
2. Generate Summary ✓
3. 📧 Send Email ← HERE
4. Generate TTS
5. Create Captions
6. Render Video
```

This means you get the email **immediately** after summarization, even if video rendering fails.

---

## 🎯 Pro Tips

1. **Create dedicated email**: Use a separate Gmail for sending (not your personal)
2. **Multiple recipients**: Modify `email_sender.py` to accept list of recipients
3. **Scheduling**: Use Windows Task Scheduler or cron to run daily
4. **Filtering**: Set up Gmail filter to auto-label bot emails
5. **Backup**: Emails serve as backup if video generation fails

---

## 📱 Mobile Notifications

To get instant notifications:
1. Enable Gmail push notifications on your phone
2. Create a Gmail filter for subject "AI Daily Brief"
3. Set it to never skip inbox + star it
4. Now you'll get instant alerts!

---

## ⚙️ Advanced: Multiple Recipients

Edit `app/email_sender.py`:

```python
# Change to_email to accept list
for recipient in to_email_list:
    msg['To'] = recipient
    server.send_message(msg)
```

Then in config:
```yaml
email:
  to_emails:  # plural
    - "claw.zhao@gmail.com"
    - "another@example.com"
```

---

## 📚 Further Reading

- Gmail App Passwords: https://support.google.com/accounts/answer/185833
- SMTP Settings: https://support.google.com/mail/answer/7126229
- Python smtplib docs: https://docs.python.org/3/library/smtplib.html

---

**Need help?** Check the config at [config.yaml](config.yaml) - email section is already configured for `claw.zhao@gmail.com`! Just add your sender email and app password.
