# MoviePy vs FFmpeg Video Creation

## 🎬 Two Approaches Available

You now have **two ways** to create videos in this bot:

### 1. FFmpeg Approach (Current/Default)
**File:** `create_simple_video.py`

**Pros:**
- ⚡ **Fast** - Professional rendering speed
- 🎯 **Lightweight** - Small script, powerful output
- 🏆 **Better quality** - Industry-standard encoding
- 🔧 **Flexible** - Full FFmpeg power available

**Cons:**
- 📦 Requires FFmpeg installation
- 🤓 Slightly more setup

**When to use:**
- Production videos
- Need fast rendering
- Want best quality
- Batch processing

---

### 2. MoviePy Approach (New)
**File:** `create_video_moviepy.py`

**Pros:**
- 🐍 **Pure Python** - No external tools (easier)
- 📝 **Simple API** - Easier to customize
- 🎨 **Rich effects** - Built-in transitions, effects
- 🛠️ **Programmatic** - Easy to script complex animations

**Cons:**
- 🐌 **Slower** - Python processing overhead
- 🔤 Requires ImageMagick for text
- 📦 Larger memory footprint

**When to use:**
- Quick prototypes
- Learning/experimenting
- Complex Python logic
- Don't want to install FFmpeg

---

## 📦 Installation

### FFmpeg Approach
```powershell
# Install FFmpeg
choco install ffmpeg

# Run
python create_simple_video.py
```

### MoviePy Approach
```powershell
# Install MoviePy
pip install moviepy

# Install ImageMagick (for text rendering)
# Download from: https://imagemagick.org/script/download.php
# OR: choco install imagemagick

# Run
python create_video_moviepy.py
```

---

## 🚀 Quick Start

### FFmpeg Version
```bash
.\env\Scripts\Activate.ps1
python create_simple_video.py
```
**Output:** `test_output/final.mp4`

### MoviePy Version
```bash
.\env\Scripts\Activate.ps1
pip install moviepy
python create_video_moviepy.py
```
**Output:** `test_output_moviepy/final.mp4`

---

## 📊 Performance Comparison

| Feature | FFmpeg | MoviePy |
|---------|--------|---------|
| Rendering Speed | ⚡⚡⚡⚡⚡ | ⚡⚡ |
| Setup Complexity | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Code Simplicity | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Output Quality | 🏆🏆🏆🏆🏆 | 🏆🏆🏆🏆 |
| Memory Usage | Light | Heavy |
| File Size | Optimized | Larger |
| Customization | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 💻 Code Comparison

### FFmpeg Approach (Simplified)
```python
# Generate audio
voice_mp3 = synthesize(cfg.tts, text, out_dir)

# Create captions
srt_path = write_srt(captions, out_dir)

# Render with FFmpeg
final_video = render_video(cfg.video, voice_mp3, srt_path, out_dir)
```

### MoviePy Approach
```python
from moviepy.editor import *

# Generate audio
voice_mp3 = synthesize(cfg.tts, text, out_dir)
audio = AudioFileClip(str(voice_mp3))

# Create background
bg = ColorClip(size=(1080, 1920), color=(16,18,20), duration=audio.duration)

# Create text clips
text_clips = []
for sentence in sentences:
    txt = TextClip(sentence, fontsize=52, color='white')
    txt = txt.set_position('center').set_duration(5)
    text_clips.append(txt)

# Composite
video = CompositeVideoClip([bg] + text_clips)
video = video.set_audio(audio)

# Export
video.write_videofile("output.mp4")
```

---

## 🎨 Customization Examples

### FFmpeg: Add Background Music
```yaml
# config.yaml
video:
  background_music: "./music/ambient.mp3"
  background_music_volume: 0.08
```
No code changes needed!

### MoviePy: Add Background Music
```python
from moviepy.editor import *

video = CompositeVideoClip([bg] + text_clips)
voice = AudioFileClip("narration.mp3")
music = AudioFileClip("ambient.mp3").volumex(0.08)

# Mix audio
final_audio = CompositeAudioClip([voice, music])
video = video.set_audio(final_audio)
```

---

## 🎯 Which Should You Use?

### Use FFmpeg if:
- ✅ You need production-quality videos
- ✅ Speed matters (batch processing)
- ✅ You want smaller file sizes
- ✅ You're comfortable installing tools

### Use MoviePy if:
- ✅ You want pure Python
- ✅ You're prototyping/learning
- ✅ You need complex programmatic animations
- ✅ You want easier debugging

---

## 🔄 Switching Between Them

Both scripts use the **same config** and **same TTS**:
- Edit `config.yaml` for both
- Same voice settings
- Same video dimensions
- Same background colors

Just run different scripts:
```bash
# FFmpeg version
python create_simple_video.py

# MoviePy version
python create_video_moviepy.py
```

---

## 📁 Output Structure

Both create similar outputs:

```
test_output/              # FFmpeg version
├── final.mp4            # Video output
├── voice.mp3            # Audio file
└── captions.srt         # Subtitle file

test_output_moviepy/     # MoviePy version
├── final.mp4            # Video output
└── voice.mp3            # Audio file
```

---

## 🛠️ Advanced Features

### FFmpeg Strengths:
- Hardware acceleration (GPU encoding)
- Precise frame control
- Complex filter chains
- Streaming support
- Format conversion

### MoviePy Strengths:
- Easy image manipulation
- Complex timing logic
- Frame-by-frame processing
- Integration with NumPy
- Easy clip composition

---

## 💡 Best Practice

**Recommended workflow:**

1. **Prototype with MoviePy** - Quick iterations, easy tweaks
2. **Produce with FFmpeg** - Fast rendering, best quality

Or just pick one and stick with it! Both work great.

---

## 🐛 Troubleshooting

### FFmpeg Issues
```
Error: "ffmpeg not found"
Fix: choco install ffmpeg
```

### MoviePy Issues
```
Error: "ImageMagick not found"
Fix: Download from https://imagemagick.org
     Or: choco install imagemagick

Error: "Text rendering failed"
Fix: Install ImageMagick with "Install legacy utilities" checked
```

---

## 📚 Learn More

- **FFmpeg Docs:** https://ffmpeg.org/documentation.html
- **MoviePy Docs:** https://zulko.github.io/moviepy/
- **Bot Config:** See `config.yaml` for all options
- **Full Guide:** See `VIDEO_CREATION_GUIDE.md`

---

**Both approaches are fully functional and production-ready!** Choose the one that fits your workflow. 🎬

