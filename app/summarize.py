from __future__ import annotations
from typing import List, Dict, Any, Tuple
import json
import requests
from datetime import datetime
import os

from .moltbook_fetch import Topic
from .config import SummarizerCfg

def get_system_prompt(sentence_count: int) -> str:
  return f"""You are an engaging news summarizer for AI and tech topics.

INPUT: Multiple hot topics from various news sources. Each topic includes:
- Title
- URL
- Full article content (most important - use this for detailed understanding)

IMPORTANT LANGUAGE RULE:
- For Chinese sources (China News, Chinese websites), provide summaries and narration in Chinese (中文)
- For English sources (Reddit, Hacker News, Twitter), provide summaries and narration in English
- Detect the language of the source content and match it in your response

Your task:
1. For EACH topic provided, write a concise summary with LESS THAN {sentence_count} sentences (aim for {sentence_count - 1} sentences):
  - Analyze the FULL ARTICLE CONTENT (not just the title)
  - Explain the key points and main arguments from the article
  - Focus on article content; DO NOT incorporate community comments or upvote counts
  - **Use Chinese for Chinese sources, English for English sources**
  - KEEP IT CONCISE - stay under {sentence_count} sentences per summary

2. Create an engaging narration script using NUMBERED LIST FORMAT:
  - Use format: "1. [Topic Title]: [Summary]"
  - Each topic should be on its own numbered line
  - Present topics in order received
  - Use summaries based on article content only
  - **Use appropriate language for each topic (Chinese for Chinese sources, English for English sources)**
   
  Example format:
  1. [First Topic Title]: [Concise summary in less than {sentence_count} sentences]
   
  2. [Second Topic Title]: [Concise summary in less than {sentence_count} sentences]

3. Create on-screen captions synchronized with narration

4. Do NOT include URLs, emails, phone numbers, API keys, passwords, personal data, community comments, or upvote counts

Output JSON with keys:
  topics: [{{title, source, summary (LESS THAN {sentence_count} sentences), key_points: [...]}}]
  narration: string (numbered list format as shown above)
  captions: [{{start_s, end_s, text}}]
  hashtags: [string, ...]
"""

def select_topics_with_ai(cfg: SummarizerCfg, headlines: List[Topic], max_topics: int = 3, priority_keywords: List[str] = None) -> List[int]:
  """
  Use AI to select the most interesting topics from headlines.
  
  Args:
    cfg: Summarizer configuration
    headlines: List of Topic objects with basic info (title, url, score, source, excerpt)
    max_topics: Maximum number of topics to select (1-3)
    priority_keywords: Keywords to prioritize (e.g., AI, finance)
    
  Returns:
    List of indices of selected topics
  """
  if not priority_keywords:
    priority_keywords = ["AI", "artificial intelligence", "machine learning", "finance", "financial"]
  
  selection_prompt = f"""You are an expert content curator for tech and finance news.

Your task: Review the following {len(headlines)} headlines and select the {max_topics} MOST INTERESTING and RELEVANT topics for a daily brief.

PRIORITY: Give higher priority to topics about:
{', '.join(priority_keywords)}

SELECTION CRITERIA:
1. Relevance to AI, technology, and finance
2. Newsworthiness and impact
3. Community engagement (score and comments)
4. Diversity of topics (don't select too similar topics)

INPUT HEADLINES:
"""
  
  headlines_data = [
    {
      'index': i,
      'title': t.title,
      'source': t.source,
      'score': t.score,
      'comments': t.comments_count,
      'excerpt': t.excerpt[:200] if t.excerpt else ''
    } for i, t in enumerate(headlines)
  ]
  
  selection_prompt += json.dumps(headlines_data, ensure_ascii=False, indent=2)
  selection_prompt += f"""

OUTPUT: Return a JSON object with ONLY these keys:
{{
  "selected_indices": [list of 1-{max_topics} indices of selected topics],
  "reasoning": "brief explanation of why these topics were selected"
}}

Select {max_topics} topics (or fewer if there aren't enough quality options).
"""
  
  if cfg.backend == "local_dummy":
    # Fallback: just select first max_topics items
    return list(range(min(max_topics, len(headlines))))
  
  if cfg.backend == "gemini":
    from google import genai
    from google.genai import types
    
    gemini_cfg = cfg.gemini
    client = genai.Client(api_key=gemini_cfg.api_key())
    
    contents = [
      types.Content(
        role="user",
        parts=[types.Part.from_text(text=selection_prompt)]
      )
    ]
    
    generate_content_config = types.GenerateContentConfig(
      temperature=0.3,
      max_output_tokens=1000,
      response_mime_type="application/json"
    )
    
    print("🤖 AI is selecting the most interesting topics...")
    try:
      content_parts = []
      for chunk in client.models.generate_content_stream(
        model=gemini_cfg.model,
        contents=contents,
        config=generate_content_config
      ):
        if chunk.text:
          content_parts.append(chunk.text)
      
      content = "".join(content_parts).strip()
      
      # Remove markdown code blocks if present
      if content.startswith("```json"):
        content = content[7:]
      if content.startswith("```"):
        content = content[3:]
      if content.endswith("```"):
        content = content[:-3]
      content = content.strip()
      
      result = json.loads(content)
      selected_indices = result.get("selected_indices", [])
      reasoning = result.get("reasoning", "")
      
      print(f"✓ AI selected {len(selected_indices)} topics")
      print(f"  Reasoning: {reasoning}")
      
      return selected_indices
    except Exception as e:
      print(f"⚠️  AI selection failed: {e}")
      print("⚠️  Falling back to top topics by score")
      # Fallback: select top topics by score
      sorted_topics = sorted(enumerate(headlines), key=lambda x: x[1].score or 0, reverse=True)
      return [i for i, _ in sorted_topics[:max_topics]]
  
  # Fallback for other backends
  return list(range(min(max_topics, len(headlines))))

def _dummy(topics: List[Topic], include_chinese: bool = False) -> Dict[str, Any]:
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
    
    # Create summary based solely on article content/title (do not include comments or upvote counts)
    if is_chinese:
      if content_preview:
        summary = f"{tp.title}。文章内容：{content_preview}..."
      else:
        summary = f"{tp.title}。"
    else:
      if content_preview:
        summary = f"{tp.title}. Article preview: {content_preview}..."
      else:
        summary = f"{tp.title}."
    
    entry = {
      "title": tp.title,
      "source": tp.source,
      "url": getattr(tp, 'url', None),
      "key_points": [
        "Based on article content"
      ]
    }
    if include_chinese:
      # Provide both English and Chinese summaries (dummy: duplicate or mirror)
      if is_chinese:
        entry["summary_zh"] = summary
        entry["summary_en"] = tp.title if not content_preview else f"{tp.title}. {content_preview[:150]}..."
      else:
        entry["summary_en"] = summary
        entry["summary_zh"] = summary
    else:
      entry["summary"] = summary
    out_topics.append(entry)
    
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
  # For dummy, create a chinese narration copy if requested
  if include_chinese:
    if any('summary_zh' in t for t in out_topics):
      narration_zh_parts = []
      for i, tp in enumerate(topics, 1):
        summary_zh = out_topics[i-1].get('summary_zh', out_topics[i-1].get('summary', ''))
        narration_zh_parts.append(f"{i}. {tp.title}: {summary_zh}\n\n")
      narration_zh = "".join(narration_zh_parts)
    else:
      narration_zh = ""
  else:
    narration_zh = None

  out = {
    "topics": out_topics,
    "narration": narration,
    "captions": captions,
    "hashtags": ["#AI", "#TechNews", "#MachineLearning", "#DailyBrief"]
  }
  if include_chinese and narration_zh is not None:
    out["narration_zh"] = narration_zh
  return out

def summarize(cfg: SummarizerCfg, topics: List[Topic], include_chinese: bool = False) -> Dict[str, Any]:
  if cfg.backend == "local_dummy":
    return _dummy(topics, include_chinese=include_chinese)
  
  def _llm_debug_log(tag: str, backend: str, model: str, payload: Any, response: str | None = None):
    try:
      log_path = os.environ.get('VIDEOAGENT_LLM_LOG', '/tmp/videoagent_llm_debug.log')
      ts = datetime.utcnow().isoformat() + 'Z'
      with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"---\n{ts} | {tag} | backend={backend} model={model}\n")
        try:
          f.write("PAYLOAD:\n")
          if isinstance(payload, (dict, list)):
            f.write(json.dumps(payload, ensure_ascii=False, indent=2))
          else:
            f.write(str(payload))
          f.write('\n')
        except Exception:
          f.write(str(payload) + '\n')
        if response is not None:
          f.write("RESPONSE:\n")
          f.write(response[:20000])
          f.write('\n')
    except Exception:
      pass
  
  if cfg.backend == "gemini":
    from google import genai
    from google.genai import types
    import os
    
    gemini_cfg = cfg.gemini
    client = genai.Client(api_key=gemini_cfg.api_key())
    
    # Build sanitized input for the LLM: exclude comments, upvote/comment counts, and scores
    sanitized = []
    for t in topics:
      sanitized.append({
        'title': t.title,
        'url': getattr(t, 'url', None),
        'source': t.source,
        'author': t.author,
        'excerpt': t.excerpt,
        'content': getattr(t, 'content', None)
      })
    # If Gemini tool/hybrid mode is enabled, ask the model which URLs it needs full
    # content for (planning). Server will fetch only those URLs and re-run summarization.
    try:
      if getattr(gemini_cfg, 'enable_tools', False) and getattr(gemini_cfg, 'tool_fetch_mode', 'server') == 'hybrid':
        plan_prompt = """You will be given a list of topics (title, url, excerpt).
Return JSON with a single key `fetch_urls` containing an array of URLs for which you need the full article content
to write high-quality summaries. Do NOT return summaries now — only the JSON {"fetch_urls": [...] }.
Only include URLs that are necessary; keep the list minimal.

INPUT:
""" + json.dumps([{ 'title': s['title'], 'url': s['url'], 'excerpt': s.get('excerpt', '') } for s in sanitized], ensure_ascii=False)

        plan_contents = [
          types.Content(
            role="user",
            parts=[types.Part.from_text(text=plan_prompt)]
          )
        ]
        plan_config = types.GenerateContentConfig(
          temperature=0.0,
          max_output_tokens=256,
          response_mime_type="application/json"
        )
        print("🔎 Asking model which URLs to fetch (hybrid mode)...")
        plan_parts = []
        try:
          for chunk in client.models.generate_content_stream(model=gemini_cfg.model, contents=plan_contents, config=plan_config):
            if chunk.text:
              plan_parts.append(chunk.text)
          plan_resp = "".join(plan_parts).strip()
          # clean code fences
          if plan_resp.startswith("```json"):
            plan_resp = plan_resp[7:]
          if plan_resp.startswith("```"):
            plan_resp = plan_resp[3:]
          if plan_resp.endswith("```"):
            plan_resp = plan_resp[:-3]
          plan_resp = plan_resp.strip()
          try:
            plan_json = json.loads(plan_resp)
            fetch_urls = plan_json.get('fetch_urls', []) if isinstance(plan_json, dict) else []
          except Exception:
            fetch_urls = []
        except Exception as e:
          print(f"⚠️ URL planning failed: {e}")
          fetch_urls = []

        try:
          _llm_debug_log("REQUEST_PLAN", "gemini", gemini_cfg.model, {"plan_prompt": plan_prompt})
          _llm_debug_log("RESPONSE_PLAN", "gemini", gemini_cfg.model, {"plan_prompt": plan_prompt}, response=plan_resp)
        except Exception:
          pass

        if fetch_urls:
          print(f"ℹ️ Model requested {len(fetch_urls)} URLs to be fetched by server")
          # Lazy import to avoid circular deps
          from .multi_source_fetch import fetch_article_content
          user_agent = os.environ.get('VIDEOAGENT_USER_AGENT', 'Mozilla/5.0')
          timeout = 15
          for s in sanitized:
            if s.get('url') in fetch_urls:
              try:
                content = fetch_article_content(s.get('url'), user_agent, timeout)
                if content:
                  s['content'] = content[:getattr(gemini_cfg, 'tool_max_fetch_chars', 5000)]
                  # also update original Topic objects so downstream sees content
                  for tp in topics:
                    if getattr(tp, 'url', None) == s.get('url'):
                      tp.content = s['content']
              except Exception:
                continue
        else:
          # If model returned no explicit fetch list, auto-fetch for topics with
          # missing or very short content to improve summary quality. We keep
          # this conservative: only fetch when content is empty or excerpt is
          # very short.
          auto_fetch = [s.get('url') for s in sanitized if s.get('url') and (not s.get('content') or len(s.get('excerpt', '')) < 200)]
          if auto_fetch:
            print(f"ℹ️ Auto-fetching {len(auto_fetch)} URLs with missing/short content")
            from .multi_source_fetch import fetch_article_content
            user_agent = os.environ.get('VIDEOAGENT_USER_AGENT', 'Mozilla/5.0')
            timeout = 15
            for s in sanitized:
              if s.get('url') in auto_fetch:
                try:
                  content = fetch_article_content(s.get('url'), user_agent, timeout)
                  if content:
                    s['content'] = content[:getattr(gemini_cfg, 'tool_max_fetch_chars', 5000)]
                    for tp in topics:
                      if getattr(tp, 'url', None) == s.get('url'):
                        tp.content = s['content']
                except Exception:
                  continue
    except Exception:
      pass
    # If include_chinese is requested, instruct the LLM to output both English and Chinese summaries
    bilingual_instructions = ""
    if include_chinese:
      bilingual_instructions = "\n\nIf possible, for each topic return both an English summary and a Chinese summary.\nReturn JSON with keys: topics:[{title, source, url, summary_en, summary_zh, key_points}], narration (English), narration_zh (Chinese), captions, hashtags."

    prompt = f"{get_system_prompt(cfg.summary_sentence_count)}{bilingual_instructions}\n\nINPUT:\n{json.dumps(sanitized, ensure_ascii=False)}"
    
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
    
    # Log request payload (sanitized) for debugging
    try:
      _llm_debug_log("REQUEST", "gemini", gemini_cfg.model, {"prompt": prompt})
    except Exception:
      pass

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
      try:
        _llm_debug_log("RESPONSE", "gemini", gemini_cfg.model, {"prompt": prompt}, response=content)
      except Exception:
        pass

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

    def _parse_with_repair(raw: str):
      # Attempt normal JSON parse, then try common mojibake repairs.
      try:
        parsed = json.loads(raw)
        return parsed
      except json.JSONDecodeError as e:
        print(f"⚠️  JSON parse failed: {e}")
      # Try to recover from latin-1 <-> utf-8 mojibake by re-decoding
      try:
        repaired = raw.encode('latin-1').decode('utf-8')
        parsed = json.loads(repaired)
        print("🔧 Repaired response by latin-1->utf-8 re-decode")
        return parsed
      except Exception:
        pass
      try:
        repaired = raw.encode('utf-8', errors='replace').decode('latin-1')
        parsed = json.loads(repaired)
        print("🔧 Repaired response by utf-8->latin-1 re-decode")
        return parsed
      except Exception:
        pass

      # Try to extract JSON substring
      start = raw.find('{')
      end = raw.rfind('}')
      if start != -1 and end != -1 and end > start:
        json_str = raw[start:end+1]
        try:
          parsed = json.loads(json_str)
          print("🔧 Extracted JSON substring and parsed")
          return parsed
        except Exception:
          pass

      # As a last diagnostic, print a short hex snippet of the raw bytes
      try:
        raw_bytes = raw.encode('utf-8', errors='replace')
        hex_snip = raw_bytes[:200].hex()
        print(f"🧾 Diagnostic hex (first 200 bytes): {hex_snip[:400]}")
      except Exception:
        print("🧾 Diagnostic: unable to produce hex snippet")

      return None

    parsed = _parse_with_repair(content)
    if parsed is None:
      print("⚠️  Falling back to dummy summarizer")
      return _dummy(topics, include_chinese=include_chinese)
    # Ensure topics carry original URLs when missing
    if isinstance(parsed, dict) and 'topics' in parsed:
      for i, tp in enumerate(topics):
        if i < len(parsed['topics']):
          if not parsed['topics'][i].get('url'):
            parsed['topics'][i]['url'] = getattr(tp, 'url', None)
    # If bilingual requested but LLM returned only single-language keys, try to normalize
    if include_chinese and isinstance(parsed, dict) and 'topics' in parsed:
      for t in parsed['topics']:
        # If LLM returned 'summary' but not 'summary_en'/'summary_zh', duplicate
        if 'summary' in t and 'summary_en' not in t and 'summary_zh' not in t:
          t['summary_en'] = t['summary']
          t['summary_zh'] = t['summary']
    return parsed

  # OpenAI-compatible Chat Completions
  oai = cfg.openai_compatible
  base = oai.base_url.rstrip("/")
  url = f"{base}/chat/completions"
  payload = {
    "model": oai.model,
    "temperature": oai.temperature,
    "max_tokens": oai.max_tokens,
    "messages": [
      {"role": "system", "content": get_system_prompt(cfg.summary_sentence_count)},
      {"role": "user", "content": json.dumps(sanitized, ensure_ascii=False) + ("\n\nPlease also provide both English and Chinese summaries in the output." if include_chinese else "")},
    ],
    "response_format": {"type": "json_object"},
  }
  headers = {
    "Authorization": f"Bearer {oai.api_key()}",
    "Content-Type": "application/json"
  }
  try:
    _llm_debug_log("REQUEST", "openai_compatible", oai.model, payload)
  except Exception:
    pass

  r = requests.post(url, headers=headers, json=payload, timeout=60)
  r.raise_for_status()
  data = r.json()
  content = data["choices"][0]["message"]["content"]
  try:
    _llm_debug_log("RESPONSE", "openai_compatible", oai.model, payload, response=content)
  except Exception:
    pass
  def _parse_openai_content(raw_content):
    # reuse same repair attempts as above
    try:
      parsed = json.loads(raw_content)
      return parsed
    except Exception:
      pass
    try:
      repaired = raw_content.encode('latin-1').decode('utf-8')
      parsed = json.loads(repaired)
      print("🔧 Repaired OpenAI response by latin-1->utf-8 re-decode")
      return parsed
    except Exception:
      pass
    # try substring
    start = raw_content.find('{')
    end = raw_content.rfind('}')
    if start != -1 and end != -1 and end > start:
      try:
        parsed = json.loads(raw_content[start:end+1])
        print("🔧 Extracted JSON substring from OpenAI response and parsed")
        return parsed
      except Exception:
        pass
    # diagnostic
    try:
      raw_bytes = raw_content.encode('utf-8', errors='replace')
      print(f"🧾 OpenAI diagnostic hex (first 200 bytes): {raw_bytes[:200].hex()[:400]}")
    except Exception:
      print("🧾 OpenAI diagnostic: unable to produce hex snippet")
    return None

  parsed = _parse_openai_content(content)
  if parsed is None:
    print("⚠️  Could not parse OpenAI-compatible response; falling back to dummy summarizer")
    return _dummy(topics)
  if isinstance(parsed, dict) and 'topics' in parsed:
    for i, tp in enumerate(topics):
      if i < len(parsed['topics']):
        if not parsed['topics'][i].get('url'):
          parsed['topics'][i]['url'] = getattr(tp, 'url', None)
  return parsed
