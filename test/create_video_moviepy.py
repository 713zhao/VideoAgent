"""
MoviePy-based video generator - simpler approach without FFmpeg dependency.
Creates text-on-screen videos with narration using pure Python.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import load_config
from app.tts import synthesize
from app.utils import ensure_dir

def create_video_with_moviepy(text: str, output_dir: str = "./test_output_moviepy"):
    """
    Create a video using MoviePy (pure Python approach).
    
    Args:
        text: The text to display and narrate
        output_dir: Where to save the video
    """
    try:
        from moviepy.editor import (
            ColorClip, TextClip, CompositeVideoClip, 
            AudioFileClip, concatenate_videoclips
        )
    except ImportError:
        print("\n❌ MoviePy not installed!")
        print("\nInstall it with:")
        print("  pip install moviepy")
        print("\nNote: MoviePy also needs ImageMagick for text rendering.")
        print("Download from: https://imagemagick.org/script/download.php")
        return None
    
    # Load config
    cfg = load_config('config.yaml')
    
    out_dir = Path(output_dir)
    ensure_dir(out_dir)
    
    print("\n" + "="*60)
    print("🎬 MOVIEPY VIDEO GENERATOR")
    print("="*60)
    
    # Step 1: Generate audio from text
    print("\n🎤 Step 1: Generating audio...")
    print(f"Text: {text[:100]}...")
    
    voice_path = synthesize(cfg.tts, text, out_dir=out_dir)
    print(f"✓ Audio saved: {voice_path.name}")
    
    # Load audio to get duration
    audio = AudioFileClip(str(voice_path))
    duration = audio.duration
    print(f"✓ Audio duration: {duration:.1f} seconds")
    
    # Step 2: Create video clips with text
    print("\n🎨 Step 2: Creating video clips...")
    
    # Video dimensions from config
    w, h = cfg.video.width, cfg.video.height
    
    # Parse background color (hex to RGB)
    bg_color = cfg.video.background_color.lstrip('#')
    bg_rgb = tuple(int(bg_color[i:i+2], 16) for i in (0, 2, 4))
    
    print(f"Resolution: {w}x{h}")
    print(f"Background: {bg_rgb}")
    
    # Create background
    background = ColorClip(size=(w, h), color=bg_rgb, duration=duration)
    
    # Split text into segments for animated captions
    sentences = [s.strip() + '.' for s in text.strip().split('.') if s.strip()]
    
    # Calculate timing for each segment
    words_total = len(text.split())
    time_per_segment = duration / len(sentences)
    
    text_clips = []
    current_time = 0
    
    for i, sentence in enumerate(sentences):
        if not sentence.strip():
            continue
        
        # Create text clip
        try:
            txt_clip = TextClip(
                sentence,
                fontsize=cfg.video.captions.font_size,
                color='white',
                font='Arial-Bold',  # Safe default font
                size=(w - 100, None),  # Width with padding
                method='caption',
                align='center'
            )
            
            # Position at bottom with margin
            txt_clip = txt_clip.set_position(('center', h - cfg.video.captions.margin_v))
            
            # Set timing
            segment_duration = min(time_per_segment, duration - current_time)
            txt_clip = txt_clip.set_start(current_time).set_duration(segment_duration)
            
            # Add fade in/out
            txt_clip = txt_clip.crossfadein(0.3).crossfadeout(0.3)
            
            text_clips.append(txt_clip)
            current_time += segment_duration
            
        except Exception as e:
            print(f"  ⚠️ Warning: Could not create text for segment {i+1}: {e}")
            continue
    
    print(f"✓ Created {len(text_clips)} text segments")
    
    # Step 3: Composite everything
    print("\n🎬 Step 3: Composing video...")
    
    # Combine background with all text clips
    video = CompositeVideoClip([background] + text_clips, size=(w, h))
    
    # Add audio
    video = video.set_audio(audio)
    
    # Step 4: Export
    print("\n💾 Step 4: Exporting video...")
    print("This may take a few minutes...")
    
    output_file = out_dir / "final.mp4"
    
    try:
        video.write_videofile(
            str(output_file),
            fps=cfg.video.fps,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            verbose=False,
            logger=None  # Suppress verbose output
        )
    except Exception as e:
        print(f"\n⚠️ Export error: {e}")
        print("\nTrying alternative export method...")
        video.write_videofile(
            str(output_file),
            fps=cfg.video.fps,
            verbose=False,
            logger=None
        )
    
    # Clean up
    audio.close()
    video.close()
    
    print(f"\n✅ Video created successfully!")
    print(f"📹 Output: {output_file}")
    print(f"📊 Size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    return output_file

def main():
    # Example text
    sample_text = """
    Welcome to the AI Daily Brief! Today we're covering the hottest topics in artificial intelligence.
    
    First up: The AI boom is causing shortages everywhere else. As tech giants pour billions into AI infrastructure,
    other industries are feeling the squeeze on resources.
    
    Second: A developer trained a 1.8 million parameter model from scratch. This impressive feat shows that 
    smaller, efficient models can still achieve remarkable results.
    
    Finally: There's controversy around OpenAI potentially creating customized versions of ChatGPT.
    The community is debating the ethical implications.
    
    That's all for today's brief. Stay tuned for more AI updates tomorrow!
    """
    
    print("\n" + "="*60)
    print("🤖 MOVIEPY VIDEO CREATOR")
    print("="*60)
    print("\nThis creates a video using MoviePy (pure Python):")
    print("  • Text-to-speech narration")
    print("  • Animated captions with fade effects")
    print("  • Vertical video format (1080x1920)")
    print("  • No FFmpeg required (MoviePy handles it)")
    
    print("\n⚠️ Requirements:")
    print("  1. pip install moviepy")
    print("  2. ImageMagick (for text rendering)")
    print("     Download: https://imagemagick.org/script/download.php")
    
    input("\nPress Enter to continue...")
    
    try:
        video_path = create_video_with_moviepy(sample_text.strip())
        
        if video_path:
            print("\n" + "="*60)
            print("🎉 SUCCESS!")
            print("="*60)
            print(f"\nYour video is ready: {video_path}")
            print("\nTo view it, simply open the file in your media player.")
            
            print("\n💡 Tips:")
            print("  • MoviePy is slower than FFmpeg but easier to use")
            print("  • Edit config.yaml to customize appearance")
            print("  • Text size: video.captions.font_size")
            print("  • Background: video.background_color")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n📝 Common issues:")
        print("  1. Missing MoviePy: pip install moviepy")
        print("  2. Missing ImageMagick: https://imagemagick.org")
        print("  3. Font not found: Script will try to use Arial-Bold")

if __name__ == "__main__":
    main()
