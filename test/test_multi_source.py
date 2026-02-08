"""
Standalone script to fetch and display top 3 hot topics from each source.
Run this to test the multi-source fetcher.
"""
import sys
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import load_config
from app.multi_source_fetch import fetch_all_sources, fetch_comments_for_topic, choose_top3_overall

def display_topics_by_source(all_topics):
    """Display topics organized by source."""
    print("\n" + "="*80)
    print("📊 TOPICS BY SOURCE (TOP 3 FROM EACH)")
    print("="*80)
    
    for source_name, topics in all_topics.items():
        print(f"\n{'─'*80}")
        print(f"📌 {source_name.upper()}")
        print('─'*80)
        
        if not topics:
            print("  ⚠️ No topics found")
            continue
        
        for i, topic in enumerate(topics, 1):
            print(f"\n  {i}. {topic.title}")
            print(f"     Source: {topic.source}")
            print(f"     Score: {topic.score} | Comments: {topic.comments_count}")
            if topic.author:
                print(f"     Author: {topic.author}")
            if topic.excerpt:
                print(f"     Excerpt: {topic.excerpt[:150]}...")
            print(f"     URL: {topic.url}")

def display_top3_overall(all_topics):
    """Display the top topics from each source."""
    # Flatten to show all topics
    all_selected = []
    for source, topics in all_topics.items():
        all_selected.extend(topics)
    
    print("\n" + "="*80)
    # Count topics per source
    source_counts = {}
    for topic in all_selected:
        source = topic.source.split()[0] if topic.source else "Unknown"
        source_counts[source] = source_counts.get(source, 0) + 1
    
    count_str = " + ".join([f"{count} {source}" for source, count in source_counts.items()])
    print(f"🏆 ALL SELECTED TOPICS ({len(all_selected)} total: {count_str})")
    print("="*80)
    
    for i, topic in enumerate(all_selected, 1):
        print(f"\n{'─'*80}")
        rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
        print(f"{rank_emoji} TOPIC #{i}")
        print('─'*80)
        print(f"Title: {topic.title}")
        print(f"Source: {topic.source}")
        print(f"Score: {topic.score} | Comments: {topic.comments_count}")
        if topic.author:
            print(f"Author: {topic.author}")
        if topic.excerpt:
            print(f"Excerpt: {topic.excerpt[:200]}...")
        print(f"URL: {topic.url}")

def display_comments_analysis(all_selected):
    """Display comments analysis for selected topics."""
    print("\n" + "="*80)
    print("💬 COMMENTS ANALYSIS")
    print("="*80)
    
    for i, topic in enumerate(all_selected, 1):
        print(f"\n{'─'*80}")
        print(f"📌 TOPIC #{i}: {topic.title[:60]}")
        print('─'*80)
        
        comments = topic.comments
        if not comments:
            print("  ⚠️ No comments fetched")
            continue
        
        print(f"  Total comments analyzed: {len(comments)}")
        
        # Show sample comments
        print(f"\n  📝 Sample Comments:")
        for j, comment in enumerate(comments[:5], 1):
            score_str = f" ({comment.get('score', 0)} pts)" if comment.get('score') else ""
            print(f"\n    {j}. @{comment['author']}{score_str}:")
            text = comment['text'].replace('\n', ' ')[:200]
            print(f"       {text}...")
        
        # Try to identify interesting comments
        interesting_keywords = ['😂', '🤣', 'lol', 'lmao', 'haha', 'amazing', 'incredible', 
                               'mind-blowing', 'brilliant', 'genius', 'wow', 'holy']
        
        interesting = []
        for comment in comments:
            text_lower = comment['text'].lower()
            if any(kw in text_lower for kw in interesting_keywords):
                interesting.append(comment)
        
        if interesting:
            print(f"\n  😄 Interesting/Funny Comments:")
            for j, comment in enumerate(interesting[:3], 1):
                score_str = f" ({comment.get('score', 0)} pts)" if comment.get('score') else ""
                print(f"\n    {j}. @{comment['author']}{score_str}:")
                text = comment['text'].replace('\n', ' ')[:250]
                print(f"       {text}...")

def main():
    print("\n" + "="*80)
    print("🚀 MULTI-SOURCE HOT TOPICS ANALYZER")
    print("="*80)
    print("Sources: Reddit, Hacker News, Twitter (if configured)")
    
    # Load config
    cfg = load_config('config.yaml')
    sources_dict = cfg.sources.model_dump()
    
    # Show which sources are enabled
    print("\n📋 Enabled Sources:")
    if sources_dict['reddit']['enabled']:
        print(f"  ✓ Reddit: {', '.join(sources_dict['reddit']['subreddits'])}")
    if sources_dict['hackernews']['enabled']:
        print(f"  ✓ Hacker News")
    if sources_dict['twitter']['enabled']:
        print(f"  ✓ Twitter")
    else:
        print(f"  ⚠️ Twitter (disabled - requires API credentials)")
    if sources_dict['moltbook']['enabled']:
        print(f"  ✓ Moltbook")
    
    # Fetch topics from all sources
    all_topics = fetch_all_sources(sources_dict)
    
    if not all_topics:
        print("\n❌ No topics fetched from any source")
        return
    
    # Display by source
    display_topics_by_source(all_topics)
    
    # Get all selected topics (3 from each source)
    all_selected = []
    for source_name, topics in all_topics.items():
        all_selected.extend(topics)
    
    display_top3_overall(all_topics)
    
    # Fetch and display comments
    print("\n" + "="*80)
    print(f"💬 FETCHING COMMENTS FOR ALL {len(all_selected)} TOPICS")
    print("="*80)
    
    for topic in all_selected:
        print(f"\n  📥 Fetching comments for: {topic.title[:60]}...")
        comments = fetch_comments_for_topic(topic, sources_dict)
        topic.comments = comments
        print(f"     ✓ Fetched {len(comments)} comments")
    
    display_comments_analysis(all_selected)
    
    # Save results
    output_file = f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump([{
            'title': t.title,
            'url': t.url,
            'score': t.score,
            'source': t.source,
            'comments_count': t.comments_count,
            'author': t.author,
            'excerpt': t.excerpt,
            'comments': t.comments
        } for t in all_selected], f, ensure_ascii=False, indent=2)
    
    print(f"\n" + "="*80)
    print(f"✅ ANALYSIS COMPLETE")
    print("="*80)
    print(f"Results saved to: {output_file}")
    print(f"Total topics analyzed: {len(all_selected)} ({sum(len(topics) for topics in all_topics.values())} total)")
    print(f"Sources: {', '.join(all_topics.keys())}")
    print(f"Topics per source: 3 from each")

if __name__ == "__main__":
    main()
