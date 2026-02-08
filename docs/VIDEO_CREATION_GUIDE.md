# Simple Video Creation Guide

## 🎬 Overview

Create videos with **text on screen + audio narration** using different approaches.

## Option 1: Current Bot (FFmpeg) ⭐ RECOMMENDED

### What You Need:
- **FFmpeg** (free, open-source video tool)
- **edge-tts** (already installed, free TTS)

### Install FFmpeg:

**Windows (PowerShell):**
```powershell
# Option A: Chocolatey
choco install ffmpeg

# Option B: Winget
winget install ffmpeg

# Option C: Manual
# Download from https://ffmpeg.org/download.html
# Extract and add to PATH
```

**Verify Installation:**
```bash
ffmpeg -version
```

### Quick Start:

```bash
.\env\Scripts\Activate.ps1
python create_simple_video.py
```

This generates a complete video with:
- ✅ Text-to-speech narration (MP3)
- ✅ Animated captions/subtitles 
- ✅ Vertical video (1080x1920 for social media)
- ✅ Background color or image
- ✅ Optional background music

### Customize in config.yaml:

```yaml
tts:
  backend: "edge_tts"  # Free, high quality
  edge_tts:
    voice: "en-US-JennyNeural"  # Change voice
    rate: "+10%"  # Speed up/slow down
    
video:
  width: 1080
  height: 1920  # Vertical for TikTok/Instagram
  fps: 30
  background_color: "#101214"  # Dark background
  captions:
    font_size: 52
    margin_v: 160  # Distance from bottom
```

### Advantages:
- ✅ Professional quality
- ✅ Highly customizable
- ✅ Free and open-source
- ✅ Industry standard
- ✅ Supports complex effects

---

## Option 2: Python Libraries (Simpler, Limited)

### MoviePy (Python-only)

**Install:**
```bash
pip install moviepy
```

**Example:**
```python
from moviepy.editor import *

# Create text clip
txt = TextClip("Hello World!", fontsize=70, color='white', size=(1080, 1920))
txt = txt.set_duration(5)  # 5 seconds

# Create background
bg = ColorClip(size=(1080, 1920), color=(16, 18, 20), duration=5)

# Combine
video = CompositeVideoClip([bg, txt.set_position('center')])

# Add audio
audio = AudioFileClip("narration.mp3")
video = video.set_audio(audio)

# Export
video.write_videofile("output.mp4", fps=30)
```

**Pros:**
- Pure Python (no external tools)
- Simple API

**Cons:**
- Slower rendering
- Less flexible
- Less stable for complex videos

---

## Option 3: Online APIs (Cloud-based)

### Shotstack API

**Website:** https://shotstack.io

**Install:**
```bash
pip install shotstack-sdk
```

**Example:**
```python
import shotstack_sdk as shotstack

# Configure API
configuration = shotstack.Configuration(host="https://api.shotstack.io/stage")
configuration.api_key['DeveloperKey'] = 'YOUR_API_KEY'

# Create video with text + narration
# (See docs for full API)
```

**Pros:**
- No local processing
- Fast rendering
- Professional templates

**Cons:**
- ❌ Costs money (free tier limited)
- ❌ Requires internet
- ❌ Less control

---

## Option 4: Manim (Animation Library)

**For mathematical/technical animations**

**Install:**
```bash
pip install manim
```

**Example:**
```python
from manim import *

class SimpleVideo(Scene):
    def construct(self):
        text = Text("AI Daily Brief", font_size=72)
        self.play(Write(text))
        self.wait(2)
```

**Pros:**
- Beautiful animations
- Great for educational content

**Cons:**
- Steeper learning curve
- Overkill for simple text

---

## Comparison Table

| Feature | FFmpeg (Current) | MoviePy | Shotstack | Manim |
|---------|------------------|---------|-----------|-------|
| Cost | ✅ Free | ✅ Free | 💰 Paid | ✅ Free |
| Speed | ⚡ Fast | 🐌 Slow | ⚡ Fast | 🐌 Slow |
| Quality | 🏆 High | ✅ Good | 🏆 High | 🏆 High |
| Ease | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Flexibility | 🔥 High | ✅ Medium | ⚠️ Limited | 🔥 High |
| Setup | Simple | Simplest | API Key | Complex |

---

## Current Bot Architecture

```
Input Text
    ↓
[TTS Service] → MP3 file
    ↓
[Caption Generator] → SRT file  
    ↓
[FFmpeg Renderer] → MP4 video
    ↓
Output: final.mp4
```

### Files Involved:

1. **app/tts.py** - Converts text to MP3
   - Uses edge-tts (free, Microsoft voices)
   - Alternative: pyttsx3 (offline but robotic)

2. **app/captions.py** - Creates SRT subtitle file
   - Splits text into timed segments
   - Standard SRT format

3. **app/render.py** - Combines everything
   - Uses FFmpeg to render video
   - Adds background, subtitles, audio
   - Exports final MP4

---

## Quick Recipes

### 1. Simple Text Video (Current Bot)
```bash
python create_simple_video.py
```
Output: `test_output/final.mp4`

### 2. Full Pipeline with Topics
```bash
python run.py
```
Output: `output/2026-02-08/final.mp4`

### 3. Custom Text Video
```python
from app.config import load_config
from create_simple_video import create_simple_video

text = "Your custom text here..."
video = create_simple_video(text, output_dir="./my_video")
```

---

## Troubleshooting

### "FFmpeg not found"
```bash
# Install FFmpeg first
choco install ffmpeg

# Verify
ffmpeg -version
```

### "No TTS audio generated"
- Check config.yaml → tts.backend
- Try "edge_tts" (requires internet)
- Or "pyttsx3" (offline, lower quality)

### "Video too long/short"
- Adjust caption timing in create_simple_video.py
- Change words_per_second value

### "Text not visible"
- Increase font_size in config.yaml
- Adjust margin_v (distance from bottom)
- Change background_color for contrast

---

## Advanced Customization

### Change Video Format
```yaml
video:
  width: 1920   # Horizontal
  height: 1080
```

### Add Background Image
```yaml
video:
  background_image: "./backgrounds/space.jpg"
```

### Add Background Music
```yaml
video:
  background_music: "./music/ambient.mp3"
  background_music_volume: 0.08  # 8% volume
```

### Change Voice
```yaml
tts:
  edge_tts:
    voice: "en-GB-SoniaNeural"  # British female
    # Or: "en-US-GuyNeural"      # US male
    # Or: "en-AU-NatashaNeural"  # Australian
```

See all voices: https://speech.microsoft.com/portal/voicegallery

---

## Recommended Setup

For best results:

1. ✅ **Use FFmpeg** (current approach)
2. ✅ **Use edge-tts** (free, high quality)
3. ✅ **Vertical video** (1080x1920 for social)
4. ✅ **Large captions** (font_size: 52+)
5. ✅ **Dark background** (better readability)

---

**Need Help?**
- Check [MULTI_SOURCE_GUIDE.md](MULTI_SOURCE_GUIDE.md) for full pipeline
- Run `python create_simple_video.py` for a working example
- See [config.yaml](config.yaml) for all options
