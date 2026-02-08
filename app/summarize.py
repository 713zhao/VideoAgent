from __future__ import annotations
from typing import List, Dict, Any, Tuple
import json
import requests

from .moltbook_fetch import Topic
from .config import SummarizerCfg

SYSTEM_PROMPT = """You are an engaging news summarizer for AI and tech topics.

INPUT: Multiple hot topics from Reddit, Hacker News, China News, etc., with comments.

IMPORTANT LANGUAGE RULE:
- For Chinese sources (China News, Chinese websites), provide summaries and narration in Chinese (中文)
- For English sources (Reddit, Hacker News, Twitter), provide summaries and narration in English
- Detect the language of the source content and match it in your response

Your task:
1. For EACH topic provided, write a 3-4 sentence summary that includes:
   - What the topic is about
   - Why it's generating discussion
   - Key insights or interesting points from the comments
   - Overall sentiment or debate
   - **Use Chinese for Chinese sources, English for English sources**

2. Create an engaging narration script for a video that:
   - Introduces each source (Reddit, Hacker News, China News, etc.)
   - Presents all topics with their summaries
   - Mentions interesting community reactions
   - Total length: suitable for 2-3 minute video
   - **Use appropriate language for each section**

3. Create on-screen captions synchronized with narration

4. Do NOT include URLs, emails, phone numbers, API keys, passwords, or personal data

Output JSON with keys:
  topics: [{title, source, summary (3-4 sentences including comment insights), key_points: [...]}]
  narration: string (full script)
  captions: [{start_s, end_s, text}]
  hashtags: [string, ...]
"""

def _dummy(topics: List[Topic]) -> Dict[str, Any]:
  # Enhanced baseline with better summaries
  out_topics = []
  captions = []
  t = 0.0
  seg = 8.0
  
  # Group topics by source
  by_source = {}
  for tp in topics:
    source = tp.source.split()[0] if tp.source else "Unknown"
    if source not in by_source:
      by_source[source] = []
    by_source[source].append(tp)
  
  narration_parts = ["Welcome to today's AI and Tech Brief. Let's dive into what's trending across the community.\n\n"]
  
  for source, source_topics in by_source.items():
    # Detect if this is a Chinese source
    is_chinese = source in ['China', 'chinanews'] or 'China News' in source
    
    if is_chinese:
      narration_parts.append(f"来自{source}：\n")
    else:
      narration_parts.append(f"From {source}:\n")
    
    for i, tp in enumerate(source_topics, 1):
      # Create summary with comment insights
      comment_insight = ""
      if tp.comments and len(tp.comments) > 0:
        top_comment = tp.comments[0].get('text', '')[:100]
        if is_chinese:
          comment_insight = f" 社区正在积极讨论此话题，有用户指出：{top_comment}..."
        else:
          comment_insight = f" The community is actively discussing this, with one user noting: {top_comment}..."
      
      if is_chinese:
        summary = f"{tp.title}。该话题获得了{tp.score}点赞和{tp.comments_count}条评论，显示出社区的强烈关注。{comment_insight}"
      else:
        summary = f"{tp.title}. This topic has {tp.score} upvotes and {tp.comments_count} comments, showing strong community interest.{comment_insight}"
      
      out_topics.append({
        "title": tp.title,
        "source": tp.source,
        "summary": summary,
        "key_points": [
          f"Score: {tp.score} points" if not is_chinese else f"评分：{tp.score}分",
          f"Comments: {tp.comments_count}" if not is_chinese else f"评论：{tp.comments_count}条",
          "Generating active discussion" if not is_chinese else "引发热烈讨论"
        ]
      })
      
      narration_parts.append(f"Topic {i}: {summary}\n\n")
      
      # Create caption
      captions.append({
        "start_s": t,
        "end_s": t + seg,
        "text": f"{source} - {tp.title[:50]}..."
      })
      t += seg
  
  narration_parts.append("That's your brief for today. Stay tuned for more updates tomorrow!")
  narration = "".join(narration_parts)

  return {
    "topics": out_topics,
    "narration": narration,
    "captions": captions,
    "hashtags": ["#AI", "#TechNews", "#MachineLearning", "#DailyBrief"]
  }

def summarize(cfg: SummarizerCfg, topics: List[Topic]) -> Dict[str, Any]:
  if cfg.backend == "local_dummy":
    return _dummy(topics)
  
  if cfg.backend == "gemini":
    from google import genai
    import os
    
    gemini_cfg = cfg.gemini
    client = genai.Client(api_key=gemini_cfg.api_key())
    
    prompt = f"{SYSTEM_PROMPT}\n\nINPUT:\n{json.dumps([t.__dict__ for t in topics], ensure_ascii=False)}"
    
    response = client.models.generate_content(
      model=gemini_cfg.model,
      contents=prompt,
      config={
        "temperature": gemini_cfg.temperature,
        "max_output_tokens": gemini_cfg.max_tokens,
        "response_mime_type": "application/json"
      }
    )
    
    # Extract JSON from response
    content = response.text.strip()
    # Remove markdown code blocks if present
    if content.startswith("```json"):
      content = content[7:]
    if content.startswith("```"):
      content = content[3:]
    if content.endswith("```"):
      content = content[:-3]
    content = content.strip()
    
    return json.loads(content)

  # OpenAI-compatible Chat Completions
  oai = cfg.openai_compatible
  base = oai.base_url.rstrip("/")
  url = f"{base}/chat/completions"
  payload = {
    "model": oai.model,
    "temperature": oai.temperature,
    "max_tokens": oai.max_tokens,
    "messages": [
      {"role": "system", "content": SYSTEM_PROMPT},
      {"role": "user", "content": json.dumps([t.__dict__ for t in topics], ensure_ascii=False)},
    ],
    "response_format": {"type": "json_object"},
  }
  headers = {
    "Authorization": f"Bearer {oai.api_key()}",
    "Content-Type": "application/json"
  }
  r = requests.post(url, headers=headers, json=payload, timeout=60)
  r.raise_for_status()
  data = r.json()
  content = data["choices"][0]["message"]["content"]
  return json.loads(content)
