#!/usr/bin/env python3
"""Test Chinese language support in summaries."""

import sys
sys.path.insert(0, '.')

from app.multi_source_fetch import Topic
from app.summarize import _dummy

# Create test topics - mix of English and Chinese sources
topics = [
    Topic(
        title="I trained a 1.8M params model from scratch",
        url="https://reddit.com/test",
        score=350,
        excerpt="Working on my own architecture...",
        source="Reddit r/LocalLLaMA",
        comments_count=66,
        author="testuser",
        comments=[
            {"author": "user1", "text": "This is awesome! Great work.", "score": 50}
        ]
    ),
    Topic(
        title="香港举行AI赋能教学高峰会",
        url="https://www.chinanews.com.cn/dwq/test.shtml",
        score=100,
        excerpt="探讨AI在教育中的应用",
        source="China News",
        comments_count=0,
        author="China News",
        comments=[]
    ),
    Topic(
        title="煤铝共采千亿集群：山西资源改革",
        url="https://www.chinanews.com.cn/cj/test.shtml",
        score=100,
        excerpt="铝产业发展的新机遇",
        source="China News",
        comments_count=0,
        author="China News",
        comments=[]
    )
]

print("Testing Chinese language support in summaries...")
print("="*60)

result = _dummy(topics)

print("\n📝 Generated Summaries:\n")
for topic in result['topics']:
    print(f"Title: {topic['title']}")
    print(f"Source: {topic['source']}")
    print(f"Summary: {topic['summary']}")
    print("-" * 60)

print("\n🎙️ Narration Script:\n")
print(result['narration'])
