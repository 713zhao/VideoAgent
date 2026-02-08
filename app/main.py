from __future__ import annotations
import argparse
import json
from pathlib import Path
from datetime import datetime

from .config import load_config
from .multi_source_fetch import fetch_all_sources, fetch_comments_for_topic, choose_top3_overall
from .summarize import summarize
from .tts import synthesize
from .captions import write_srt
from .render import render_video
from .utils import ensure_dir, sha256_file, copytree_overwrite
from .email_sender import send_summary_email

def run_once(cfg_path: str) -> Path:
  cfg = load_config(cfg_path)

  today = datetime.now().strftime("%Y-%m-%d")
  out_root = Path(cfg.output.root_dir)
  day_dir = ensure_dir(out_root / today)

  # 1) Fetch topics from multiple sources
  print("\n" + "="*60)
  print("📥 FETCHING TOPICS FROM MULTIPLE SOURCES")
  print("="*60)
  
  # Convert SourcesCfg to dict for the fetcher
  sources_dict = cfg.sources.model_dump()
  all_topics = fetch_all_sources(sources_dict)
  
  # Show results by source
  print("\n" + "="*60)
  print("📊 TOPICS BY SOURCE")
  print("="*60)
  for source_name, topics in all_topics.items():
    print(f"\n🔹 {source_name.upper()} - Top {len(topics)} topics:")
    for i, topic in enumerate(topics, 1):
      print(f"  {i}. {topic.title[:80]}")
      print(f"     Score: {topic.score} | Comments: {topic.comments_count}")
      print(f"     URL: {topic.url}")
  
  # Use all topics from each source (3 per source)
  all_selected_topics = []
  for source_name, topics in all_topics.items():
    all_selected_topics.extend(topics)
  
  print(f"\n" + "="*60)
  print(f"🔝 SELECTED TOPICS: {len(all_selected_topics)} total (3 from each source)")
  print("="*60)
  for i, topic in enumerate(all_selected_topics, 1):
    print(f"\n  {i}. {topic.title[:80]}")
    print(f"     Source: {topic.source}")
    print(f"     URL: {topic.url}")
    print(f"     Score: {topic.score}")
    print(f"     Comments: {topic.comments_count}")
  
  # Fetch comments for all selected topics
  print(f"\n" + "="*60)
  print(f"💬 FETCHING COMMENTS FOR ALL {len(all_selected_topics)} TOPICS")
  print("="*60)
  for topic in all_selected_topics:
    print(f"\n  📥 Fetching comments for: {topic.title[:60]}...")
    comments = fetch_comments_for_topic(topic, sources_dict)
    topic.comments = comments
    print(f"     ✓ Fetched {len(comments)} comments")

  topics_json = day_dir / "topics.json"
  topics_json.write_text(
    json.dumps([{
      'title': t.title,
      'url': t.url,
      'score': t.score,
      'source': t.source,
      'comments_count': t.comments_count,
      'author': t.author,
      'excerpt': t.excerpt,
      'comments': t.comments
    } for t in all_selected_topics], ensure_ascii=False, indent=2),
    encoding="utf-8"
  )

  # 2) Summarize + script + captions
  print("\n" + "="*60)
  print("📝 GENERATING SUMMARY AND SCRIPT")
  print("="*60)
  print(f"Using backend: {cfg.summarizer.backend}")
  bundle = summarize(cfg.summarizer, all_selected_topics)

  print(f"\n✓ NARRATION SCRIPT ({len(bundle.get('narration', ''))} characters):")
  print("-" * 60)
  print(bundle.get("narration", "")[:500])
  if len(bundle.get("narration", "")) > 500:
    print(f"... (truncated, full script in script.txt)")
  print("-" * 60)
  
  print(f"\n✓ CAPTIONS: {len(bundle.get('captions', []))} segments")
  for i, cap in enumerate(bundle.get("captions", [])[:3], 1):
    print(f"  {i}. [{cap.get('start_s', 0):.1f}s - {cap.get('end_s', 0):.1f}s] {cap.get('text', '')[:60]}")
  if len(bundle.get("captions", [])) > 3:
    print(f"  ... and {len(bundle.get('captions', [])) - 3} more")

  print(f"\n✓ HASHTAGS: {', '.join(bundle.get('hashtags', []))}")

  script_txt = day_dir / "script.txt"
  script_txt.write_text(bundle.get("narration", ""), encoding="utf-8")

  summary_json = day_dir / "summary.json"
  summary_json.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")

  # Send email notification
  if cfg.email.enabled:
    print("\n" + "="*60)
    print("📧 SENDING EMAIL NOTIFICATION")
    print("="*60)
    
    # Prepare topics for email
    topics_for_email = [{
      'title': t.title,
      'url': t.url,
      'score': t.score,
      'source': t.source,
      'comments_count': t.comments_count,
      'author': t.author,
      'excerpt': t.excerpt
    } for t in all_selected_topics]
    
    # Format subject with date
    subject = cfg.email.subject_template.format(date=today)
    
    email_sent = send_summary_email(
      to_email=cfg.email.to_email,
      from_email=cfg.email.from_email,
      from_name=cfg.email.from_name,
      subject=subject,
      smtp_config=cfg.email.smtp.model_dump(),
      topics=topics_for_email,
      summary=bundle,
      include_topics=cfg.email.include_topics,
      include_summary=cfg.email.include_summary
    )
    
    if email_sent:
      print(f"✓ Email sent to {cfg.email.to_email}")
    else:
      print(f"⚠️ Failed to send email (continuing anyway...)")
  else:
    print("\n⚠️ Email notifications disabled in config")

  # Video generation (can be disabled)
  final_mp4 = None
  if cfg.video.enabled:
    # 3) TTS
    print("\n" + "="*60)
    print("🎤 GENERATING TEXT-TO-SPEECH")
    print("="*60)
    print(f"Using TTS backend: {cfg.tts.backend}")
    voice_path = synthesize(cfg.tts, bundle.get("narration", ""), out_dir=day_dir)
    print(f"✓ Voice generated: {voice_path.name}")

    # 4) Captions
    print("\n" + "="*60)
    print("📄 WRITING SUBTITLES")
    print("="*60)
    srt_path = write_srt(bundle.get("captions", []), out_dir=day_dir)
    print(f"✓ Captions written: {srt_path.name}")

    # 5) Render video
    print("\n" + "="*60)
    print("🎬 RENDERING VIDEO")
    print("="*60)
    print(f"Resolution: {cfg.video.width}x{cfg.video.height} @ {cfg.video.fps}fps")
    print(f"Background: {cfg.video.background_color}")
    final_mp4 = render_video(cfg.video, voice_path=voice_path, srt_path=srt_path, out_dir=day_dir)
    print(f"✓ Video rendered: {final_mp4.name}")

    # 6) Checksums + latest
    print("\n" + "="*60)
    print("💾 FINALIZING")
    print("="*60)
    sha_hash = sha256_file(final_mp4)
    (day_dir / "final.sha256").write_text(sha_hash, encoding="utf-8")
    print(f"✓ Checksum: {sha_hash[:16]}...")
  else:
    print("\n" + "="*60)
    print("⏭️  VIDEO GENERATION DISABLED")
    print("="*60)
    print("Skipping TTS, captions, and video rendering")
    print("Summary and topics saved to JSON files")

  if cfg.output.write_latest:
    latest = out_root / "latest"
    copytree_overwrite(day_dir, latest)
    print(f"✓ Copied to: {latest}")

  print("\n" + "="*60)
  print("✅ ALL DONE!")
  print("="*60)
  
  if final_mp4:
    print(f"📹 Video: {final_mp4.name}")
  else:
    print("📝 Summary only (video disabled)")

  return final_mp4

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--config", default="config.yaml", help="Path to config YAML")
  args = ap.parse_args()
  out = run_once(args.config)
  if out:
    print(f"\n📹 FINAL OUTPUT: {out}")
    print(f"📁 Full path: {out.absolute()}\n")
  else:
    print(f"\n✓ Summary and topics generated (video disabled)\n")

if __name__ == "__main__":
  main()
