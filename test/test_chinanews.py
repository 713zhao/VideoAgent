#!/usr/bin/env python3
"""Simple test for China News RSS fetcher."""

import sys
sys.path.insert(0, '.')

from app.multi_source_fetch import ChinaNewsRSSFetcher

def main():
    print("Testing China News RSS Fetcher...")
    print("="*60)
    
    fetcher = ChinaNewsRSSFetcher(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        timeout_s=15
    )
    
    rss_url = "https://www.chinanews.com.cn/rss/scroll-news.xml"
    print(f"Fetching from: {rss_url}\n")
    
    topics = fetcher.fetch_rss(rss_url, limit=5)
    
    print(f"\nFetched {len(topics)} topics:\n")
    for i, topic in enumerate(topics, 1):
        print(f"{i}. {topic.title}")
        print(f"   URL: {topic.url}")
        print(f"   Excerpt: {topic.excerpt[:100] if topic.excerpt else 'N/A'}...")
        print()

if __name__ == "__main__":
    main()
