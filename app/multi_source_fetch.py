"""
Multi-source fetcher for hot AI topics from Reddit, Hacker News, Twitter, etc.
"""
from __future__ import annotations
import time
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin
import json
import urllib3
import xml.etree.ElementTree as ET
from datetime import datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@dataclass
class Topic:
    title: str
    url: str
    score: Optional[int] = None
    excerpt: str = ""
    source: str = "unknown"
    comments_count: int = 0
    author: str = ""
    comments: List[Dict[str, str]] = None
    content: str = ""  # Full article content
    
    def __post_init__(self):
        if self.comments is None:
            self.comments = []

class RedditFetcher:
    """Fetch hot topics from Reddit using the JSON API."""
    
    def __init__(self, user_agent: str, timeout_s: int):
        self.user_agent = user_agent
        self.timeout = timeout_s
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})
    
    def fetch_subreddit(self, subreddit: str, limit: int = 5, time_filter: str = "day") -> List[Topic]:
        """Fetch hot posts from a subreddit using Reddit JSON API."""
        try:
            # Reddit provides JSON API by adding .json to URL
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}&t={time_filter}"
            print(f"  📡 Fetching r/{subreddit}...")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            topics = []
            for post in data.get('data', {}).get('children', []):
                post_data = post.get('data', {})
                
                # Skip stickied posts
                if post_data.get('stickied', False):
                    continue
                
                title = post_data.get('title', '')
                permalink = post_data.get('permalink', '')
                url = f"https://www.reddit.com{permalink}" if permalink else post_data.get('url', '')
                score = post_data.get('score', 0)
                num_comments = post_data.get('num_comments', 0)
                author = post_data.get('author', '[deleted]')
                selftext = post_data.get('selftext', '')[:300]
                
                topics.append(Topic(
                    title=title,
                    url=url,
                    score=score,
                    excerpt=selftext,
                    source=f"Reddit r/{subreddit}",
                    comments_count=num_comments,
                    author=author
                ))
            
            print(f"    ✓ Found {len(topics)} posts from r/{subreddit}")
            return topics
            
        except Exception as e:
            print(f"    ⚠️ Error fetching r/{subreddit}: {e}")
            return []
    
    def fetch_comments(self, post_url: str, limit: int = 30) -> List[Dict[str, str]]:
        """Fetch top comments from a Reddit post."""
        try:
            # Add .json to get JSON response
            json_url = post_url.rstrip('/') + '.json?limit=30'
            response = self.session.get(json_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            comments = []
            if len(data) > 1:
                comment_data = data[1].get('data', {}).get('children', [])
                
                for comment in comment_data[:limit]:
                    if comment.get('kind') == 't1':  # Comment type
                        c_data = comment.get('data', {})
                        body = c_data.get('body', '')
                        author = c_data.get('author', '[deleted]')
                        score = c_data.get('score', 0)
                        
                        if body and len(body) > 10:  # Skip very short comments
                            comments.append({
                                'author': author,
                                'text': body[:500],
                                'score': score
                            })
            
            return comments
            
        except Exception as e:
            print(f"    ⚠️ Error fetching comments: {e}")
            return []

class HackerNewsFetcher:
    """Fetch hot topics from Hacker News using the official API."""
    
    def __init__(self, api_url: str, timeout_s: int):
        self.api_url = api_url
        self.timeout = timeout_s
        self.session = requests.Session()
    
    def fetch_top_stories(self, max_stories: int = 30) -> List[Topic]:
        """Fetch top stories from Hacker News."""
        try:
            print(f"  📡 Fetching Hacker News top stories...")
            
            # Get top story IDs
            top_stories_url = f"{self.api_url}/topstories.json"
            response = self.session.get(top_stories_url, timeout=self.timeout)
            response.raise_for_status()
            story_ids = response.json()[:max_stories]
            
            topics = []
            for story_id in story_ids[:max_stories]:  # Limit to avoid too many requests
                try:
                    story_url = f"{self.api_url}/item/{story_id}.json"
                    story_response = self.session.get(story_url, timeout=self.timeout)
                    story_data = story_response.json()
                    
                    # Filter for stories about AI, agents, LLM, etc.
                    title = story_data.get('title', '').lower()
                    ai_keywords = ['ai', 'agent', 'llm', 'gpt', 'artificial intelligence', 
                                   'machine learning', 'ml', 'neural', 'chatbot', 'claude',
                                   'openai', 'anthropic', 'deepmind', 'langchain']
                    
                    if any(keyword in title for keyword in ai_keywords):
                        topics.append(Topic(
                            title=story_data.get('title', ''),
                            url=story_data.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                            score=story_data.get('score', 0),
                            excerpt='',
                            source="Hacker News",
                            comments_count=story_data.get('descendants', 0),
                            author=story_data.get('by', '')
                        ))
                    
                    time.sleep(0.1)  # Be nice to HN API
                    
                except Exception as e:
                    continue
            
            print(f"    ✓ Found {len(topics)} AI-related stories from Hacker News")
            return topics
            
        except Exception as e:
            print(f"    ⚠️ Error fetching Hacker News: {e}")
            return []
    
    def fetch_comments(self, story_id: str, limit: int = 30) -> List[Dict[str, str]]:
        """Fetch top comments from a HN story."""
        try:
            story_url = f"{self.api_url}/item/{story_id}.json"
            response = self.session.get(story_url, timeout=self.timeout)
            story_data = response.json()
            
            comments = []
            kid_ids = story_data.get('kids', [])[:limit]
            
            for kid_id in kid_ids:
                try:
                    comment_url = f"{self.api_url}/item/{kid_id}.json"
                    comment_response = self.session.get(comment_url, timeout=self.timeout)
                    comment_data = comment_response.json()
                    
                    text = comment_data.get('text', '')
                    author = comment_data.get('by', '')
                    
                    if text and len(text) > 10:
                        # Remove HTML tags
                        soup = BeautifulSoup(text, 'html.parser')
                        clean_text = soup.get_text()
                        
                        comments.append({
                            'author': author,
                            'text': clean_text[:500],
                            'score': 0  # HN API doesn't provide comment scores
                        })
                    
                    time.sleep(0.1)
                    
                except:
                    continue
            
            return comments
            
        except Exception as e:
            print(f"    ⚠️ Error fetching HN comments: {e}")
            return []

class ChinaNewsRSSFetcher:
    """Fetch news from China News RSS feed."""
    
    def __init__(self, user_agent: str, timeout_s: int):
        self.user_agent = user_agent
        self.timeout = timeout_s
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})
    
    def fetch_rss(self, rss_url: str, limit: int = 10) -> List[Topic]:
        """Fetch news from RSS feed."""
        try:
            print(f"  📡 Fetching China News RSS...")
            
            response = self.session.get(rss_url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse RSS XML
            root = ET.fromstring(response.content)
            
            topics = []
            items = root.findall('.//item')[:limit]
            
            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')
                description_elem = item.find('description')
                
                if title_elem is not None and link_elem is not None:
                    title = title_elem.text or ''
                    url = link_elem.text or ''
                    description = description_elem.text if description_elem is not None else ''
                    
                    # Clean HTML from description if present
                    if description:
                        soup = BeautifulSoup(description, 'html.parser')
                        description = soup.get_text()[:300]
                    
                    topics.append(Topic(
                        title=title,
                        url=url,
                        score=100,  # RSS doesn't have scores, use default
                        excerpt=description,
                        source="China News",
                        comments_count=0,
                        author="China News"
                    ))
            
            print(f"    ✓ Found {len(topics)} news items from China News")
            return topics
            
        except Exception as e:
            print(f"    ⚠️ Error fetching China News RSS: {e}")
            return []

class TwitterFetcher:
    """Fetch hot topics from Twitter/X (requires API credentials)."""
    
    def __init__(self, bearer_token: Optional[str], timeout_s: int):
        self.bearer_token = bearer_token
        self.timeout = timeout_s
        self.session = requests.Session()
        if bearer_token:
            self.session.headers.update({
                'Authorization': f'Bearer {bearer_token}'
            })
    
    def fetch_tweets(self, query: str, max_results: int = 10) -> List[Topic]:
        """Fetch tweets matching a search query."""
        if not self.bearer_token:
            print("  ⚠️ Twitter API disabled (no bearer token)")
            return []
        
        try:
            print(f"  📡 Searching Twitter for '{query}'...")
            
            url = "https://api.twitter.com/2/tweets/search/recent"
            params = {
                'query': query,
                'max_results': max_results,
                'tweet.fields': 'public_metrics,author_id,created_at'
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            topics = []
            for tweet in data.get('data', []):
                metrics = tweet.get('public_metrics', {})
                topics.append(Topic(
                    title=tweet.get('text', '')[:100] + '...',
                    url=f"https://twitter.com/i/web/status/{tweet.get('id')}",
                    score=metrics.get('like_count', 0) + metrics.get('retweet_count', 0) * 2,
                    excerpt=tweet.get('text', '')[:300],
                    source="Twitter",
                    comments_count=metrics.get('reply_count', 0),
                    author=tweet.get('author_id', '')
                ))
            
            print(f"    ✓ Found {len(topics)} tweets for '{query}'")
            return topics
            
        except Exception as e:
            print(f"    ⚠️ Error fetching Twitter: {e}")
            return []

def fetch_article_content(url: str, user_agent: str, timeout: int = 15) -> str:
    """
    Fetch full article content from a URL.
    Extracts main text content from HTML pages.
    """
    try:
        session = requests.Session()
        session.headers.update({'User-Agent': user_agent})
        response = session.get(url, timeout=timeout, verify=False, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Try to find main content area
        # Common article containers
        main_content = None
        selectors = [
            'article', 
            '[role="main"]',
            '.post-content',
            '.article-content',
            '.entry-content',
            '.content',
            'main',
            '#content'
        ]
        
        for selector in selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # If no specific container found, use body
        if not main_content:
            main_content = soup.find('body')
        
        if main_content:
            # Extract all paragraphs
            paragraphs = main_content.find_all('p')
            text_parts = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
            full_text = '\n\n'.join(text_parts)
            
            # Limit to reasonable length (first 5000 characters)
            return full_text[:5000] if full_text else ""
        
        return ""
        
    except Exception as e:
        print(f"    ⚠️ Could not fetch content from {url[:50]}...: {e}")
        return ""

def fetch_all_sources(sources_cfg: Dict[str, Any]) -> Dict[str, List[Topic]]:
    """
    Fetch topics from all enabled sources.
    
    Returns:
        Dictionary mapping source name to list of topics
    """
    all_topics = {}
    
    timeout = sources_cfg.get('timeout_s', 15)
    user_agent = sources_cfg.get('user_agent', 'Mozilla/5.0')
    top_n = sources_cfg.get('top_n_per_source', 3)
    
    # Reddit
    reddit_cfg = sources_cfg.get('reddit', {})
    if reddit_cfg.get('enabled', False):
        print("\n" + "="*60)
        print("🔴 FETCHING FROM REDDIT")
        print("="*60)
        
        reddit = RedditFetcher(user_agent, timeout)
        reddit_topics = []
        
        for subreddit in reddit_cfg.get('subreddits', []):
            topics = reddit.fetch_subreddit(
                subreddit,
                limit=reddit_cfg.get('limit_per_subreddit', 5),
                time_filter=reddit_cfg.get('time_filter', 'day')
            )
            reddit_topics.extend(topics)
            time.sleep(sources_cfg.get('polite_delay_s', 1.0))
        
        # Sort by score and take top N
        reddit_topics.sort(key=lambda t: t.score or 0, reverse=True)
        all_topics['reddit'] = reddit_topics[:top_n]
        
        print(f"\n✓ Selected top {len(all_topics['reddit'])} Reddit topics")
    
    # Hacker News
    hn_cfg = sources_cfg.get('hackernews', {})
    if hn_cfg.get('enabled', False):
        print("\n" + "="*60)
        print("🟠 FETCHING FROM HACKER NEWS")
        print("="*60)
        
        hn = HackerNewsFetcher(hn_cfg.get('api_url', ''), timeout)
        hn_topics = hn.fetch_top_stories(hn_cfg.get('max_stories', 30))
        
        # Sort by score and take top N
        hn_topics.sort(key=lambda t: t.score or 0, reverse=True)
        all_topics['hackernews'] = hn_topics[:top_n]
        
        print(f"\n✓ Selected top {len(all_topics['hackernews'])} Hacker News topics")
    
    # Twitter
    twitter_cfg = sources_cfg.get('twitter', {})
    if twitter_cfg.get('enabled', False):
        print("\n" + "="*60)
        print("🔵 FETCHING FROM TWITTER")
        print("="*60)
        
        import os
        bearer_token = os.getenv(twitter_cfg.get('bearer_token_env', 'TWITTER_BEARER_TOKEN'))
        twitter = TwitterFetcher(bearer_token, timeout)
        
        twitter_topics = []
        for query in twitter_cfg.get('search_queries', []):
            topics = twitter.fetch_tweets(query, twitter_cfg.get('max_tweets_per_query', 10))
            twitter_topics.extend(topics)
            time.sleep(sources_cfg.get('polite_delay_s', 1.0))
        
        # Sort by score and take top N
        twitter_topics.sort(key=lambda t: t.score or 0, reverse=True)
        all_topics['twitter'] = twitter_topics[:top_n]
        
        print(f"\n✓ Selected top {len(all_topics['twitter'])} Twitter topics")
    
    # China News RSS
    chinanews_cfg = sources_cfg.get('chinanews', {})
    if chinanews_cfg.get('enabled', False):
        print("\n" + "="*60)
        print("🟡 FETCHING FROM CHINA NEWS")
        print("="*60)
        
        chinanews = ChinaNewsRSSFetcher(user_agent, timeout)
        
        chinanews_topics = []
        for rss_url in chinanews_cfg.get('rss_urls', []):
            topics = chinanews.fetch_rss(rss_url, chinanews_cfg.get('limit', 10))
            chinanews_topics.extend(topics)
            time.sleep(sources_cfg.get('polite_delay_s', 1.0))
        
        # Take top N (no sorting since RSS doesn't have scores)
        # Use source-specific top_n if configured, otherwise use default
        chinanews_top_n = chinanews_cfg.get('top_n', top_n)
        all_topics['chinanews'] = chinanews_topics[:chinanews_top_n]
        
        print(f"\n✓ Selected top {len(all_topics['chinanews'])} China News topics")
    
    return all_topics

def fetch_comments_for_topic(topic: Topic, sources_cfg: Dict[str, Any]) -> List[Dict[str, str]]:
    """Fetch comments for a specific topic based on its source."""
    timeout = sources_cfg.get('timeout_s', 15)
    user_agent = sources_cfg.get('user_agent', 'Mozilla/5.0')
    
    if 'Reddit' in topic.source:
        reddit = RedditFetcher(user_agent, timeout)
        return reddit.fetch_comments(topic.url)
    elif topic.source == 'Hacker News':
        # Extract story ID from URL
        if 'item?id=' in topic.url:
            story_id = topic.url.split('item?id=')[1].split('&')[0]
            hn = HackerNewsFetcher(sources_cfg.get('hackernews', {}).get('api_url', ''), timeout)
            return hn.fetch_comments(story_id)
    
    return []

def choose_top3_overall(all_topics: Dict[str, List[Topic]]) -> List[Topic]:
    """
    Choose top 3 topics across all sources based on score.
    Ensures diversity by taking at most 2 from any single source.
    """
    # Flatten all topics
    all_flat = []
    for source, topics in all_topics.items():
        all_flat.extend(topics)
    
    # Sort by score
    all_flat.sort(key=lambda t: t.score or 0, reverse=True)
    
    # Select top 3 with diversity
    selected = []
    source_counts = {}
    
    for topic in all_flat:
        source_count = source_counts.get(topic.source, 0)
        if source_count < 2:  # Max 2 from any source
            selected.append(topic)
            source_counts[topic.source] = source_count + 1
        
        if len(selected) >= 3:
            break
    
    return selected
