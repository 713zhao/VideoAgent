from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
import os
import yaml

class RedditCfg(BaseModel):
  enabled: bool = True
  subreddits: List[str] = ["artificial", "MachineLearning"]
  limit_per_subreddit: int = 5
  time_filter: str = "day"

class HackerNewsCfg(BaseModel):
  enabled: bool = True
  api_url: str = "https://hacker-news.firebaseio.com/v0"
  max_stories: int = 30

class TwitterCfg(BaseModel):
  enabled: bool = False
  search_queries: List[str] = ["AI agents", "LLM agents"]
  max_tweets_per_query: int = 10
  bearer_token_env: str = "TWITTER_BEARER_TOKEN"

class MoltbookCfg(BaseModel):
  enabled: bool = False
  hot_urls: List[str] = ["https://moltbook.com/"]
  fetch_limit: int = 20

class ChinaNewsCfg(BaseModel):
  enabled: bool = True
  rss_urls: List[str] = ["https://www.chinanews.com/rss/"]
  limit: int = 10
  top_n: Optional[int] = None  # Override default top_n_per_source

class AITopicSelectionCfg(BaseModel):
  enabled: bool = True
  max_topics_to_select: int = 3
  priority_keywords: List[str] = ["AI", "artificial intelligence", "machine learning", "finance", "financial", "economy"]
  # When true, perform selection based on headline+url+excerpt first,
  # and only fetch full article content for the chosen topics.
  # When false, fetch full article content for all headlines before selecting.
  selection_before_fetch: bool = True

class SourcesCfg(BaseModel):
  reddit: RedditCfg = Field(default_factory=RedditCfg)
  hackernews: HackerNewsCfg = Field(default_factory=HackerNewsCfg)
  twitter: TwitterCfg = Field(default_factory=TwitterCfg)
  moltbook: MoltbookCfg = Field(default_factory=MoltbookCfg)
  chinanews: ChinaNewsCfg = Field(default_factory=ChinaNewsCfg)
  timeout_s: int = 15
  user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  polite_delay_s: float = 1.0
  top_n_per_source: int = 3
  # Fetch robustness options (can also be set via environment variables)
  fetch_retries: int = 2
  fetch_backoff_factor: float = 0.5
  # Optional list of user-agents to rotate (overrides `user_agent` when set)
  fetch_user_agents: Optional[List[str]] = None
  # Optional environment variable name that holds an HTTP proxy (e.g. "HTTP_PROXY")
  proxy_env: Optional[str] = None
  ai_topic_selection: AITopicSelectionCfg = Field(default_factory=AITopicSelectionCfg)

class OpenAICompatibleCfg(BaseModel):
  base_url: str = "https://api.openai.com/v1"
  api_key_env: str = "OPENAI_API_KEY"
  model: str = "gpt-4o-mini"
  temperature: float = 0.3
  max_tokens: int = 900

  def api_key(self) -> str:
    key = os.environ.get(self.api_key_env, "")
    if not key:
      raise RuntimeError(f"Missing API key env var: {self.api_key_env}")
    return key

class GeminiCfg(BaseModel):
  api_key_env: str = "GEMINI_API_KEY"
  model: str = "gemini-2.5-flash"
  temperature: float = 0.3
  max_tokens: int = 900
  # If true and the provider supports tools/browsing, allow model-assisted fetching.
  enable_tools: bool = False
  # Mode for fetching URL content: 'server' (server fetches), 'hybrid' (model may request URLs to fetch),
  # 'model' (model fetches itself via provider tools). Default is server-only.
  tool_fetch_mode: Literal['server', 'hybrid', 'model'] = 'server'
  # When server fetches content on behalf of model, cap returned chars.
  tool_max_fetch_chars: int = 5000

  def api_key(self) -> str:
    # If the value starts with "AIza" it's likely the actual API key, not env var name
    if self.api_key_env.startswith("AIza"):
      return self.api_key_env
    key = os.environ.get(self.api_key_env, "")
    if not key:
      raise RuntimeError(f"Missing API key env var: {self.api_key_env}")
    return key

class SummarizerCfg(BaseModel):
  backend: Literal["openai_compatible", "gemini", "local_dummy"] = "local_dummy"
  openai_compatible: OpenAICompatibleCfg = Field(default_factory=OpenAICompatibleCfg)
  gemini: GeminiCfg = Field(default_factory=GeminiCfg)
  summary_sentence_count: int = 5
  max_summary_sentences: int = 5
  # When true, skip topics that have been summarized previously (by URL)
  # to avoid repeating the same news in future briefs.
  skip_already_summarized: bool = True
  # How many days of past outputs to scan for previously summarized URLs.
  # Uses `output.retain_days` from the main config; set there instead.
  # If zero, all past summary files will be scanned.

class EdgeTTSCfg(BaseModel):
  voice: str = "en-US-JennyNeural"
  rate: str = "+0%"
  volume: str = "+0%"

class Pyttsx3Cfg(BaseModel):
  rate: int = 170

class TTSCfg(BaseModel):
  backend: Literal["edge_tts", "pyttsx3", "none"] = "edge_tts"
  edge_tts: EdgeTTSCfg = Field(default_factory=EdgeTTSCfg)
  pyttsx3: Pyttsx3Cfg = Field(default_factory=Pyttsx3Cfg)
  audio_format: Literal["mp3", "wav"] = "mp3"

class CaptionsStyle(BaseModel):
  font_size: int = 52
  font: str = ""
  margin_v: int = 160

class VideoCfg(BaseModel):
  enabled: bool = True
  width: int = 1080
  height: int = 1920
  fps: int = 30
  pad_s: float = 1.0
  background_image: str = ""
  background_color: str = "#101214"
  captions: CaptionsStyle = Field(default_factory=CaptionsStyle)
  background_music: str = ""
  background_music_volume: float = 0.08

class OutputCfg(BaseModel):
  root_dir: str = "./output"
  write_latest: bool = True
  # Number of days of output to keep (older directories will be removed)
  retain_days: int = 30

class SmtpCfg(BaseModel):
  host: str = "smtp.gmail.com"
  port: int = 587
  use_tls: bool = True
  password: str = ""  # Direct password (less secure)
  password_env: str = "EMAIL_PASSWORD"  # Or use environment variable

class EmailCfg(BaseModel):
  enabled: bool = False
  to_email: str = ""
  from_email: str = ""
  from_name: str = "AI Daily Bot"
  smtp: SmtpCfg = Field(default_factory=SmtpCfg)
  subject_template: str = "AI Daily Brief - {date}"
  include_topics: bool = True
  include_summary: bool = True
  include_hashtags: bool = True
  include_top_topics: bool = True
  top_topics_count: int = 4
  include_video_link: bool = False
  # Whether to send a separate Chinese email translation
  send_chinese: bool = True
  chinese_subject_template: str = "AI 每日简报 - {date}"

class SchedulerCfg(BaseModel):
  enabled: bool = False
  mode: Literal["daily", "hourly", "interval"] = "daily"
  time: str = "08:00"  # HH:MM format for daily mode
  interval_minutes: int = 60  # For interval mode
  run_on_start: bool = False

class TelegramCfg(BaseModel):
  # Control whether to send a separate Chinese Telegram message
  send_chinese: bool = False
  bot_token_env: str = "TELEGRAM_BOT_TOKEN"
  chat_id_env: str = "TELEGRAM_CHAT_ID"

class AppCfg(BaseModel):
  sources: SourcesCfg = Field(default_factory=SourcesCfg)
  summarizer: SummarizerCfg = Field(default_factory=SummarizerCfg)
  tts: TTSCfg = Field(default_factory=TTSCfg)
  video: VideoCfg = Field(default_factory=VideoCfg)
  output: OutputCfg = Field(default_factory=OutputCfg)
  email: EmailCfg = Field(default_factory=EmailCfg)
  scheduler: SchedulerCfg = Field(default_factory=SchedulerCfg)
  telegram: TelegramCfg = Field(default_factory=TelegramCfg)

def load_config(path: str) -> AppCfg:
  with open(path, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)
  return AppCfg.model_validate(data)
