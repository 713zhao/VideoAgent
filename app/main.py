from __future__ import annotations
import argparse
import json
from pathlib import Path
from datetime import datetime

from .config import load_config
from types import SimpleNamespace
from .multi_source_fetch import fetch_all_sources, fetch_comments_for_topic, choose_top3_overall, fetch_article_content
from .summarize import summarize, select_topics_with_ai
from .tts import synthesize
from .captions import write_srt
from .render import render_video
from .utils import ensure_dir, sha256_file, copytree_overwrite
from .utils import cleanup_old_outputs
from .email_sender import send_summary_email
from .telegram_sender import send_telegram_message

def run_once(cfg_path: str) -> Path:
  cfg = load_config(cfg_path)

  today = datetime.now().strftime("%Y-%m-%d")
  out_root = Path(cfg.output.root_dir)
  day_dir = ensure_dir(out_root / today)
  summary_json_path = day_dir / "summary.json"

  # If configured to NOT skip already-summarized items, prefer reusing
  # today's existing summary.json if present (avoid re-calling AI).
  reuse_entire_run = False
  bundle = None
  if not cfg.summarizer.skip_already_summarized:
    if summary_json_path.exists():
      try:
        existing = json.loads(summary_json_path.read_text(encoding="utf-8"))
        bundle = existing
        # Build selected topics from existing summary entries so downstream
        # code has the expected `all_selected_topics` variable.
        all_selected_topics = []
        for t in existing.get("topics", []):
          ns = SimpleNamespace(
            title=t.get("title", ""),
            url=t.get("url", ""),
            score=t.get("score", 0),
            comments_count=t.get("comments_count", 0),
            author=t.get("author", ""),
            excerpt=t.get("excerpt", ""),
            comments=t.get("comments", []),
            content=t.get("content", ""),
            source=t.get("source", "")
          )
          all_selected_topics.append(ns)
        reuse_entire_run = True
        print("✓ reuse_entire_run: reusing today's summary.json as configured (skip_already_summarized=False)")
      except Exception as _e:
        print(f"⚠️ Failed to load today's summary.json for reuse: {_e}")

  # 1) Fetch topics from multiple sources
  print("\n" + "="*60)
  print("📥 FETCHING HEADLINES FROM MULTIPLE SOURCES")
  print("="*60)
  
  # Convert SourcesCfg to dict for the fetcher
  sources_dict = cfg.sources.model_dump()
  all_topics = fetch_all_sources(sources_dict)
  
  # Show results by source
  print("\n" + "="*60)
  print("📊 HEADLINES BY SOURCE")
  print("="*60)
  for source_name, topics in all_topics.items():
    print(f"\n🔹 {source_name.upper()} - Fetched {len(topics)} headlines:")
    for i, topic in enumerate(topics[:5], 1):  # Show first 5
      print(f"  {i}. {topic.title[:80]}")
      print(f"     Score: {topic.score} | Comments: {topic.comments_count}")
    if len(topics) > 5:
      print(f"  ... and {len(topics) - 5} more headlines")
  
  # Combine all headlines into one list
  all_headlines = []
  for source_name, topics in all_topics.items():
    all_headlines.extend(topics)
  
  print(f"\n📊 Total headlines fetched: {len(all_headlines)}")

  # Optionally skip headlines that were already summarized previously (by URL)
  selection_pool = all_headlines
  if cfg.summarizer.skip_already_summarized and not reuse_entire_run:
    already_urls = set()
    already_titles = set()
    try:
      # Search for summary.json files under the output root and collect their topic URLs
      # Also collect titles as a fallback when older summary files omitted URLs.
      retain_days = int(cfg.output.retain_days or 0)
      for sf in out_root.rglob("summary.json"):
        try:
          # Optionally limit by history days when parent folder is YYYY-MM-DD
          if retain_days and retain_days > 0:
            parent_name = sf.parent.name
            try:
              dir_date = datetime.strptime(parent_name, "%Y-%m-%d")
              age_days = (datetime.now() - dir_date).days
              if age_days > retain_days:
                continue
            except Exception:
              # If folder name isn't a date, skip it when retain_days is set
              continue

          data = json.loads(sf.read_text(encoding="utf-8"))
          for t in data.get("topics", []):
            u = t.get("url")
            title = t.get("title")
            if u:
              already_urls.add(u)
            elif title:
              already_titles.add(title)
        except Exception:
          continue
    except Exception:
      already_urls = set()
      already_titles = set()

    if already_urls or already_titles:
      def _is_previously_summarized(topic):
        u = getattr(topic, 'url', None)
        if u and u in already_urls:
          return True
        title = getattr(topic, 'title', None)
        if title and title in already_titles:
          return True
        return False

      filtered = [t for t in all_headlines if not _is_previously_summarized(t)]
      print(f"ℹ️ Found {len(already_urls)} previously summarized URLs and {len(already_titles)} titles; {len(filtered)} new headlines remain")
      if len(filtered) > 0:
        selection_pool = filtered
      else:
        print("ℹ️ No new headlines after filtering — will allow previously summarized items to be selected")
    else:
      print("ℹ️ No previously summarized URLs found (within history window)")
  elif reuse_entire_run:
    # selection_pool should reflect the loaded topics when reusing today's summary
    selection_pool = all_selected_topics

  
  # Use AI to select the most interesting topics
  if cfg.sources.ai_topic_selection.enabled:
    print(f"\n" + "="*60)
    print("🤖 AI SELECTING MOST INTERESTING TOPICS")
    print("="*60)
    
    selected_indices = select_topics_with_ai(
      cfg.summarizer,
      selection_pool,
      max_topics=cfg.sources.ai_topic_selection.max_topics_to_select,
      priority_keywords=cfg.sources.ai_topic_selection.priority_keywords
    )

    all_selected_topics = [selection_pool[i] for i in selected_indices]
    
    print(f"\n✓ AI selected {len(all_selected_topics)} topics")
  else:
    # Fallback: use all topics from each source (old behavior)
    # Fallback: select from the filtered pool (or full list if filtering left none)
    all_selected_topics = list(selection_pool)
  
  print(f"\n" + "="*60)
  print(f"🔝 FINAL SELECTED TOPICS: {len(all_selected_topics)} total")
  print("="*60)
  for i, topic in enumerate(all_selected_topics, 1):
    print(f"\n  {i}. {topic.title[:80]}")
    print(f"     Source: {topic.source}")
    print(f"     URL: {topic.url}")
    print(f"     Score: {topic.score}")
    print(f"     Comments: {topic.comments_count}")
  
  # Fetch comments for selected topics only
  print(f"\n" + "="*60)
  print(f"💬 FETCHING COMMENTS FOR SELECTED {len(all_selected_topics)} TOPICS")
  print("="*60)
  for topic in all_selected_topics:
    print(f"\n  📥 Fetching comments for: {topic.title[:60]}...")
    comments = fetch_comments_for_topic(topic, sources_dict)
    topic.comments = comments
    print(f"     ✓ Fetched {len(comments)} comments")

  # Fetch full article content for selected topics only
  print(f"\n" + "="*60)
  print(f"📄 FETCHING FULL ARTICLE CONTENT FOR SELECTED {len(all_selected_topics)} TOPICS")
  print("="*60)
  user_agent = sources_dict.get('user_agent', 'Mozilla/5.0')
  timeout = sources_dict.get('timeout_s', 15)
  
  for topic in all_selected_topics:
    print(f"\n  📥 Fetching content for: {topic.title[:60]}...")
    content = fetch_article_content(topic.url, user_agent, timeout)
    topic.content = content
    if content:
      print(f"     ✓ Fetched {len(content)} characters of content")
    else:
      print(f"     ⚠️  No content extracted (will use title and comments)")

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
      'comments': t.comments,
      'content': t.content
    } for t in all_selected_topics], ensure_ascii=False, indent=2),
    encoding="utf-8"
  )

  # 2) Summarize + script + captions
  print("\n" + "="*60)
  print("📝 GENERATING SUMMARY AND SCRIPT")
  print("="*60)
  print(f"Using backend: {cfg.summarizer.backend}")
  summary_json = day_dir / "summary.json"
  if bundle is None:
    bundle = summarize(cfg.summarizer, all_selected_topics)

  # Option 2 workflow: produce English summaries then translate to Chinese
  chinese_bundle = None
  if cfg.email.send_chinese or cfg.telegram.send_chinese:
    try:
      from .translate import translate_bundle
      chinese_bundle = translate_bundle(cfg.summarizer, bundle, target_lang="zh")
      print(f"✓ Translated bundle to Chinese (narration {len(chinese_bundle.get('narration',''))} chars)")
    except Exception as _e:
      print(f"⚠️ Chinese translation step failed: {_e}")

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

    # Attempt to send summary to Telegram if configured via environment
    try:
      # Build a plain-text summary for Telegram
      from .email_sender import build_text_email
      tg_text = build_text_email(topics_for_email, bundle, include_topics=cfg.email.include_topics, include_summary=cfg.email.include_summary)
      # Trim to Telegram message sensible length
      tg_text_short = tg_text.strip()[:3800]
      send_telegram_message(tg_text_short)
    except Exception as _e:
      print("⚠️ Telegram send attempt failed (see above)")
  
    # Send Chinese email/telegram if enabled
    if chinese_bundle:
      # Chinese email
      if cfg.email.send_chinese:
        try:
          ch_subject = cfg.email.chinese_subject_template.format(date=today)
          # For email topics, translate the english topics list titles/excerpts into chinese versions
          topics_ch_for_email = [{
            'title': t.get('title', ''),
            'url': t.get('url', ''),
            'score': t.get('score', 0),
            'source': t.get('source', ''),
            'comments_count': t.get('comments_count', 0),
            'author': t.get('author', ''),
            'excerpt': t.get('excerpt', '')
          } for t in topics_for_email]

          email_sent = send_summary_email(
            to_email=cfg.email.to_email,
            from_email=cfg.email.from_email,
            from_name=cfg.email.from_name,
            subject=ch_subject,
            smtp_config=cfg.email.smtp.model_dump(),
            topics=topics_ch_for_email,
            summary=chinese_bundle,
            include_topics=cfg.email.include_topics,
            include_summary=cfg.email.include_summary
          )
          if email_sent:
            print(f"✓ Chinese email sent to {cfg.email.to_email}")
        except Exception as _e:
          print(f"⚠️ Failed to send Chinese email: {_e}")

      # Chinese Telegram
      if cfg.telegram.send_chinese:
        try:
          from .email_sender import build_text_email
          tg_ch_text = build_text_email(topics_for_email, chinese_bundle, include_topics=cfg.email.include_topics, include_summary=cfg.email.include_summary)
          tg_ch_short = tg_ch_text.strip()[:3800]
          send_telegram_message(tg_ch_short, bot_token_env=cfg.telegram.bot_token_env, chat_id_env=cfg.telegram.chat_id_env)
        except Exception as _e:
          print(f"⚠️ Failed to send Chinese Telegram: {_e}")
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

  # Cleanup old output directories according to config
  try:
    retain = int(cfg.output.retain_days or 0)
    if retain > 0:
      cleanup_old_outputs(cfg.output.root_dir, retain_days=retain, keep_latest=True)
  except Exception as _e:
    print(f"⚠️ Failed to cleanup old outputs: {_e}")

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
