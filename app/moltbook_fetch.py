from __future__ import annotations
import time
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@dataclass
class Topic:
  title: str
  url: str
  score: Optional[int] = None
  excerpt: str = ""

def _safe_int(x: str) -> Optional[int]:
  try:
    return int(x)
  except Exception:
    return None

def fetch_hot_topics(hot_urls: List[str], fetch_limit: int, timeout_s: int, user_agent: str, polite_delay_s: float) -> List[Topic]:
  """Fetch candidate topics from Moltbook hot/trending pages.

  This is best-effort HTML scraping. You will likely need to adjust CSS selectors
  to match Moltbook's UI/HTML structure.
  """
  sess = requests.Session()
  headers = {"User-Agent": user_agent}

  topics: List[Topic] = []
  for i, url in enumerate(hot_urls):
    resp = sess.get(url, headers=headers, timeout=timeout_s, verify=False)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    # Heuristic: collect links that look like post links.
    # You may refine this:
    # - by specific containers/classes
    # - by presence of vote counts
    # - by excluding nav/footer links
    candidates = []
    for a in soup.find_all("a", href=True):
      href = a.get("href", "")
      text = (a.get_text() or "").strip()
      if not text or len(text) < 12:
        continue
      if any(bad in href.lower() for bad in ["login", "signup", "register", "terms", "privacy", "settings"]):
        continue
      if href.startswith("#"):
        continue
      full = urljoin(url, href)
      candidates.append((text, full))

    # Deduplicate by URL
    seen = set()
    for title, link in candidates:
      if link in seen:
        continue
      seen.add(link)
      topics.append(Topic(title=title[:140], url=link))

    if polite_delay_s and i < len(hot_urls) - 1:
      time.sleep(polite_delay_s)

  # Trim and return
  # Score extraction is not implemented (depends on Moltbook HTML).
  # We'll just take first N unique topics.
  uniq: List[Topic] = []
  seen = set()
  for t in topics:
    if t.url in seen:
      continue
    seen.add(t.url)
    uniq.append(t)
    if len(uniq) >= fetch_limit:
      break
  return uniq

def choose_top3(topics: List[Topic]) -> List[Topic]:
  """Pick top 3 topics.
  If `score` exists, sort by score desc; else keep order.
  """
  with_score = [t for t in topics if t.score is not None]
  if with_score:
    topics = sorted(topics, key=lambda t: (t.score or 0), reverse=True)
  return topics[:3]
