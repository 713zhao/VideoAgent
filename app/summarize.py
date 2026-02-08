from __future__ import annotations
from typing import List, Dict, Any, Tuple
import json
import requests

from .moltbook_fetch import Topic
from .config import SummarizerCfg

SYSTEM_PROMPT = """You are an engaging news summarizer for AI and tech topics.

INPUT: Multiple hot topics from Reddit, Hacker News, China News, etc. Each topic includes:
- Title
- URL
- Full article content (most important - use this for detailed understanding)
- Comments from the community

IMPORTANT LANGUAGE RULE:
- For Chinese sources (China News, Chinese websites), provide summaries and narration in Chinese (中文)
- For English sources (Reddit, Hacker News, Twitter), provide summaries and narration in English
- Detect the language of the source content and match it in your response

Your task:
1. For EACH topic provided, write a comprehensive 4-5 sentence summary that:
   - Analyzes the FULL ARTICLE CONTENT (not just the title)
   - Explains the key points and main arguments from the article
   - Incorporates interesting insights from community comments
   - Discusses why it's generating discussion and community sentiment
   - **Use Chinese for Chinese sources, English for English sources**
   - Prioritize article content over comments

2. Create an engaging narration script using NUMBERED LIST FORMAT:
   - Use format: "1. [Topic Title]: [Summary]"
   - Each topic should be on its own numbered line
   - Present topics in order received
   - Include detailed summaries based on article content
   - Mention interesting community reactions
   - **Use appropriate language for each topic (Chinese for Chinese sources, English for English sources)**
   
   Example format:
   1. [First Topic Title]: [Detailed summary covering article content and community discussion...]
   
   2. [Second Topic Title]: [Detailed summary covering article content and community discussion...]
   
   3. [Third Topic Title]: [Detailed summary covering article content and community discussion...]

3. Create on-screen captions synchronized with narration

4. Do NOT include URLs, emails, phone numbers, API keys, passwords, or personal data

Output JSON with keys:
  topics: [{title, source, summary (4-5 sentences based on article content + comment insights), key_points: [...]}]
  narration: string (numbered list format as shown above)
  captions: [{start_s, end_s, text}]
  hashtags: [string, ...]
"""

def _dummy(topics: List[Topic]) -> Dict[str, Any]:
  # Enhanced baseline with better summaries
  out_topics = []
  captions = []
  t = 0.0
  seg = 8.0
  
  narration_parts = []
  topic_counter = 1
  
  # Process all topics in order
  for tp in topics:
    # Detect if this is a Chinese source
    is_chinese = 'China' in tp.source or 'chinanews' in tp.source.lower()
    
    # Use article content if available, otherwise use excerpt
    content_preview = ""
    if hasattr(tp, 'content') and tp.content:
      content_preview = tp.content[:300]
    elif tp.excerpt:
      content_preview = tp.excerpt[:200]
    
    # Create summary with content and comment insights
    comment_insight = ""
    if tp.comments and len(tp.comments) > 0:
      top_comment = tp.comments[0].get('text', '')[:100]
      if is_chinese:
        comment_insight = f" 社区正在积极讨论此话题，有用户指出：{top_comment}..."
      else:
        comment_insight = f" The community is actively discussing this, with one user noting: {top_comment}..."
    
    if is_chinese:
      if content_preview:
        summary = f"{tp.title}。文章内容：{content_preview}... 该话题获得了{tp.score}点赞和{tp.comments_count}条评论。{comment_insight}"
      else:
        summary = f"{tp.title}。该话题获得了{tp.score}点赞和{tp.comments_count}条评论，显示出社区的强烈关注。{comment_insight}"
    else:
      if content_preview:
        summary = f"{tp.title}. Article preview: {content_preview}... This topic has {tp.score} upvotes and {tp.comments_count} comments.{comment_insight}"
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
    
    # Add to narration using numbered format
    narration_parts.append(f"{topic_counter}. {tp.title}: {summary}\n\n")
    
    # Create caption
    captions.append({
      "start_s": t,
      "end_s": t + seg,
      "text": f"{topic_counter}. {tp.title[:50]}..."
    })
    t += seg
    topic_counter += 1
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
    from google.genai import types
    import os
    
    gemini_cfg = cfg.gemini
    client = genai.Client(api_key=gemini_cfg.api_key())
    
    prompt = f"{SYSTEM_PROMPT}\n\nINPUT:\n{json.dumps([t.__dict__ for t in topics], ensure_ascii=False)}"
    
    # Use streaming to get complete response
    contents = [
      types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)]
      )
    ]
    
    generate_content_config = types.GenerateContentConfig(
      temperature=gemini_cfg.temperature,
      max_output_tokens=gemini_cfg.max_tokens,
      response_mime_type="application/json"
    )
    
    # Collect all chunks from streaming response
    print("🔄 Streaming response from Gemini...")
    content_parts = []
    try:
      for chunk in client.models.generate_content_stream(
        model=gemini_cfg.model,
        contents=contents,
        config=generate_content_config
      ):
        if chunk.text:
          content_parts.append(chunk.text)
      
      content = "".join(content_parts).strip()
      print(f"✓ Received complete response ({len(content)} characters)")
      
    except Exception as e:
      print(f"⚠️  Streaming failed: {e}")
      print("⚠️  Falling back to dummy summarizer")
      return _dummy(topics)
    
    # Remove markdown code blocks if present
    if content.startswith("```json"):
      content = content[7:]
    if content.startswith("```"):
      content = content[3:]
    if content.endswith("```"):
      content = content[:-3]
    content = content.strip()
    
    # Try to parse JSON
    try:
      return json.loads(content)
    except json.JSONDecodeError as e:
      print(f"⚠️  JSON parse failed: {e}")
      print(f"📄 Response length: {len(content)} characters")
      print(f"📄 First 500 chars:\n{content[:500]}")
      print(f"📄 Last 500 chars:\n{content[-500:]}")
      
      # Try to extract JSON from text (find first { to last })
      start = content.find('{')
      end = content.rfind('}')
      if start != -1 and end != -1 and end > start:
        json_str = content[start:end+1]
        try:
          return json.loads(json_str)
        except json.JSONDecodeError as e2:
          print(f"⚠️  Extracted JSON parse also failed: {e2}")
      
      # If all else fails, use dummy fallback
      print("⚠️  Falling back to dummy summarizer")
      return _dummy(topics)

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
