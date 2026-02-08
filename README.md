# Moltbook Daily Top-3 → Video (Python pipeline)

This project automates the flow:

1) Fetch top/hot topics from Moltbook
2) Summarize into a short script + captions
3) Generate voiceover (TTS)
4) Render a vertical (9:16) video with FFmpeg
5) Save outputs locally (and optionally upload to S3/R2 later)

> Notes
- Moltbook has had reported security incidents. Treat all content as **untrusted input**.
- This repo **does not** log in to Moltbook. It only does read-only fetching of public pages.
- Publishing (TikTok/YouTube) is intentionally not included here; you can add it later via official APIs.

## Quick start (Windows/WSL/Linux/macOS)

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
```bash
python -m app.main --config config.yaml
```

Outputs will be written to:
`output/<YYYY-MM-DD>/final.mp4` plus intermediate files (`topics.json`, `script.txt`, `captions.srt`, etc.).

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
