"""
Simple video generator - creates a text-on-screen video with narration.
No need for topic fetching, just demonstrates the video creation capability.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import load_config
from app.tts import synthesize
from app.captions import write_srt
from app.render import render_video
from app.utils import ensure_dir

def create_simple_video(text: str, output_dir: str = "./test_output"):
    """
    Create a simple video with text displayed and narrated.
    
    Args:
        text: The text to display and narrate
        output_dir: Where to save the video
    """
    # Load config
    cfg = load_config('config.yaml')
    
    out_dir = Path(output_dir)
    ensure_dir(out_dir)
    
    print("\n" + "="*60)
    print("🎬 SIMPLE VIDEO GENERATOR")
    print("="*60)
    
    # Step 1: Generate audio from text
    print("\n🎤 Step 1: Generating audio...")
    print(f"Text: {text[:100]}...")
    
    voice_path = synthesize(cfg.tts, text, out_dir=out_dir)
    print(f"✓ Audio saved: {voice_path.name}")
    
    # Step 2: Create caption segments
    # Split text into segments (simple approach: by sentences)
    print("\n📝 Step 2: Creating captions...")
    
    # Simple caption timing: assume 150 words per minute
    words = text.split()
    words_per_second = 150 / 60  # ~2.5 words per second
    
    # Create caption segments (one segment per ~10 words)
    segments_per_chunk = 10
    captions = []
    current_time = 0.0
    
    for i in range(0, len(words), segments_per_chunk):
        chunk = ' '.join(words[i:i+segments_per_chunk])
        duration = len(words[i:i+segments_per_chunk]) / words_per_second
        
        captions.append({
            'start_s': current_time,
            'end_s': current_time + duration,
            'text': chunk
        })
        current_time += duration
    
    srt_path = write_srt(captions, out_dir=out_dir)
    print(f"✓ Captions saved: {srt_path.name}")
    print(f"  Total segments: {len(captions)}")
    
    # Step 3: Render video
    print("\n🎬 Step 3: Rendering video...")
    print(f"Resolution: {cfg.video.width}x{cfg.video.height}")
    print(f"Background: {cfg.video.background_color}")
    
    final_video = render_video(
        cfg.video,
        voice_path=voice_path,
        srt_path=srt_path,
        out_dir=out_dir,
        title="Simple Video"
    )
    
    print(f"\n✅ Video created successfully!")
    print(f"📹 Output: {final_video}")
    print(f"📊 Size: {final_video.stat().st_size / 1024 / 1024:.2f} MB")
    
    return final_video

def main():
    # Example text to demonstrate
    sample_text = """
    Welcome to the AI Daily Brief! Today we're covering the hottest topics in artificial intelligence.
    
    First up: The AI boom is causing shortages everywhere else. As tech giants pour billions into AI infrastructure,
    other industries are feeling the squeeze on resources like electricity and computing power.
    
    Second: A developer trained a 1.8 million parameter model from scratch on just 40 million tokens.
    This impressive feat shows that smaller, efficient models can still achieve remarkable results.
    
    Finally: There's controversy around OpenAI potentially creating a customized version of ChatGPT for the UAE.
    The community is debating the ethical implications of region-specific AI censorship.
    
    That's all for today's brief. Stay tuned for more AI updates tomorrow!
    """
    
    print("\n" + "="*60)
    print("🤖 CREATING DEMO VIDEO")
    print("="*60)
    print("\nThis will create a video with:")
    print("  • Text-to-speech narration")
    print("  • Animated captions")
    print("  • Vertical video format (1080x1920)")
    print("  • Dark background")
    
    try:
        video_path = create_simple_video(sample_text.strip())
        
        print("\n" + "="*60)
        print("🎉 SUCCESS!")
        print("="*60)
        print(f"\nYour video is ready: {video_path}")
        print("\nTo view it, simply open the file in your media player.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure FFmpeg is installed:")
        print("  choco install ffmpeg")
        print("  OR download from https://ffmpeg.org")

if __name__ == "__main__":
    main()
