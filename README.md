# AI Multi-Source News Bot with Video Generation

Automated news aggregation bot that:

1. **Fetches** hot topics from multiple sources (Reddit, Hacker News, Chinese news)
2. **Summarizes** with AI (Gemini/OpenAI) in appropriate language (English/Chinese)
3. **Generates** voiceover with text-to-speech
4. **Renders** vertical video (9:16) with captions
5. **Emails** daily summaries with HTML formatting
6. **Schedules** automatic runs at configured times

## Features

✨ **Multi-Source Support**
- Reddit (configurable subreddits)
- Hacker News (AI-filtered topics)
- Chinese News (RSS feeds from multiple sources)
- Twitter (requires API credentials)

🧠 **AI-Powered**
- Gemini Flash for intelligent summarization
- Chinese language detection and summaries
- 3-4 sentence summaries with comment insights

📧 **Email Notifications**
- HTML formatted emails with topic summaries
- Configurable SMTP (Gmail, etc.)
- Includes scores, comments, and sources

🎬 **Video Generation**
- Vertical format (1080x1920) for social media
- Text-to-speech with edge-tts or pyttsx3
- Burned-in captions with customizable styling
- Optional background music

⏰ **Automated Scheduling**
- Daily, hourly, or interval-based runs
- Configurable run times
- Run on start option

## Quick Start

### 1) Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Install FFmpeg
- Ubuntu/Debian:
  ```bash
  sudo apt-get update && sudo apt-get install -y ffmpeg
  ```
- Windows: install FFmpeg and add it to PATH.
- macOS:
  ```bash
  brew install ffmpeg
  ```

### 3) Configure
Copy `config.example.yaml` to `config.yaml` and edit:
- Moltbook hot page URL(s)
- Output directory
- Summarizer backend (OpenAI-compatible endpoint or a local model)
- TTS method

### 4) Run

**One-time run:**
```bash
python run.py
```

**Automated scheduling:**
```bash
# Enable scheduler in config.yaml first
python scheduler.py
```

See [Scheduler Guide](docs/SCHEDULER_GUIDE.md) for scheduling options.

Outputs will be written to:
`output/<YYYY-MM-DD>/final.mp4` plus intermediate files (`topics.json`, `script.txt`, `captions.srt`, etc.).

## Configuration

Key settings in `config.yaml`:

**Sources:**
```yaml
sources:
  reddit:
    enabled: true
    subreddits: ["artificial", "MachineLearning", "LocalLLaMA"]
  hackernews:
    enabled: true
  chinanews:
    enabled: true
    top_n: 9  # Get 9 Chinese news topics
```

**Summarizer:**
```yaml
summarizer:
  backend: "gemini"  # Use "local_dummy" for testing without API
```

**Video:**
```yaml
video:
  enabled: true  # Set false to skip video (faster, email only)
  width: 1080
  height: 1920
```

**Email:**
```yaml
email:
  enabled: true
  to_email: "your-email@gmail.com"
  smtp:
    password: "your-gmail-app-password"
```

**Scheduler:**
```yaml
scheduler:
  enabled: true
  mode: "daily"  # Options: daily, hourly, interval
  time: "08:00"  # For daily mode
```

## Documentation

- [Scheduler Guide](docs/SCHEDULER_GUIDE.md) - Automated scheduling setup
- [Multi-Source Guide](docs/MULTI_SOURCE_GUIDE.md) - Configure news sources
- [Email Setup Guide](docs/EMAIL_SETUP_GUIDE.md) - Email notifications
- [Chinese News Integration](docs/CHINESE_NEWS_INTEGRATION.md) - Chinese language support
- [Video Creation Guide](docs/VIDEO_CREATION_GUIDE.md) - Video generation options

## How the video is built
- Creates a 1080x1920 background (solid color)
- Burns subtitles (SRT) onto the video
- Mixes voiceover audio
- Optional background music

If you want a nicer background, set `background_image` in config (a local JPG/PNG).

## Extending
- Upload to S3/R2: add a small uploader step after render
- Auto-publish: integrate official TikTok Content Posting API (OAuth required)

## Troubleshooting
- If you get `ffmpeg not found`, confirm `ffmpeg -version` works in your terminal.
- If Moltbook HTML changes, adjust selectors in `app/moltbook_fetch.py`.
