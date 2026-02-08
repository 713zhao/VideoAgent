# Multi-Source Hot Topics Fetcher - User Guide

## 🎉 Overview

The bot now fetches hot AI-related topics from **multiple sources** instead of just Moltbook:

- ✅ **Reddit** - Multiple AI/ML subreddits
- ✅ **Hacker News** - Top AI stories
- ⏸️ **Twitter** - Requires API credentials (optional)
- ⏸️ **Moltbook** - Currently disabled (no content yet)

## 🚀 Quick Start

### Test the Multi-Source Fetcher
```bash
.\env\Scripts\Activate.ps1
python test_multi_source.py
```

This will:
1. Fetch top 3 topics from each enabled source
2. Select the overall top 3 based on score
3. Fetch comments for the top 3
4. Analyze and display results
5. Save to JSON file

### Run the Full Pipeline
```bash
python run.py
```

This generates a complete video with topics from all sources.

## ⚙️ Configuration

### Edit `config.yaml`

```yaml
sources:
  # Reddit Configuration
  reddit:
    enabled: true  # Enable/disable Reddit
    subreddits:
      - "artificial"
      - "MachineLearning"
      - "LocalLLaMA"
      - "ArtificialIntelligence"
    limit_per_subreddit: 5
    time_filter: "day"  # hour, day, week, month, year, all
  
  # Hacker News Configuration
  hackernews:
    enabled: true  # Enable/disable Hacker News
    api_url: "https://hacker-news.firebaseio.com/v0"
    max_stories: 30
  
  # Twitter Configuration (Optional)
  twitter:
    enabled: false  # Set to true if you have API credentials
    search_queries:
      - "AI agents"
      - "LLM agents"
      - "autonomous agents"
    max_tweets_per_query: 10
    bearer_token_env: "TWITTER_BEARER_TOKEN"  # Environment variable name
  
  # Moltbook Configuration
  moltbook:
    enabled: false  # Currently no content available
    hot_urls:
      - "https://moltbook.com/"
    fetch_limit: 20
  
  # General Settings
  timeout_s: 15
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  polite_delay_s: 1.0
  top_n_per_source: 3  # How many to select from each source
```

## 📊 How It Works

### 1. **Fetch from Each Source**
   - Gets top posts/stories from each enabled source
   - Filters by AI-related keywords (for HN)
   - Respects rate limits with polite delays

### 2. **Select Top 3 Per Source**
   - Ranks by score (upvotes, likes, etc.)
   - Takes top N from each source

### 3. **Choose Overall Top 3**
   - Combines all topics
   - Selects top 3 by score
   - **Ensures diversity**: Max 2 from any single source

### 4. **Fetch Comments**
   - Gets detailed comments for top 3
   - Identifies funny/interesting comments
   - Includes author and score info

### 5. **Generate Summary**
   - Creates narration script
   - Generates captions
   - Identifies key discussion points

## 🎯 Current Results

**From the test run:**

### Top 3 Topics Selected:
1. **The AI boom is causing shortages everywhere else** (Hacker News)
   - Score: 343 | Comments: 556
   
2. **I trained a 1.8M params model from scratch** (Reddit r/LocalLLaMA)
   - Score: 327 | Comments: 59
   
3. **OpenAI may tailor ChatGPT for UAE** (Reddit r/artificial)
   - Score: 244 | Comments: 89

### Sample Comments Analyzed:
- ✅ Fetched 27 total comments
- ✅ Identified interesting/funny comments
- ✅ Preserved author info and scores

## 🔧 Customization

### Add More Subreddits
```yaml
reddit:
  subreddits:
    - "artificial"
    - "MachineLearning"
    - "LocalLLaMA"
    - "singularity"        # Add more here
    - "ArtificialInteligence"
    - "LLMDevs"
```

### Change Time Filter
```yaml
reddit:
  time_filter: "week"  # Get weekly hot topics instead of daily
```

### Enable Twitter (if you have API access)
```yaml
twitter:
  enabled: true
  bearer_token_env: "TWITTER_BEARER_TOKEN"
```

Then set environment variable:
```bash
$env:TWITTER_BEARER_TOKEN = "your-token-here"
```

### Adjust Number of Topics
```yaml
sources:
  top_n_per_source: 5  # Get top 5 from each source instead of 3
```

## 📁 Output Files

### `topics.json`
Contains all topic data including:
- Title, URL, score
- Source, author
- Comments with scores
- Excerpt/description

### `analysis_results_*.json`
From test script:
- Detailed analysis
- Comments analysis
- Timestamp

## 🛠️ API Access

### Reddit
✅ **No API key needed!** Uses public JSON API

### Hacker News  
✅ **No API key needed!** Uses official public API

### Twitter
❌ **Requires API credentials** 
- Get from https://developer.twitter.com
- Set Bearer Token in environment variable

### Moltbook
⏸️ **Currently empty** - Will work when content is available

## 🎬 Integration with Video Pipeline

The video generation automatically uses topics from all sources:

```bash
python run.py
```

This will:
1. Fetch from all enabled sources
2. Select top 3 overall
3. Generate AI summary
4. Create TTS narration
5. Generate captions
6. Render final video

Output: `output/YYYY-MM-DD/final.mp4`

## 💡 Tips

1. **Test First**: Run `test_multi_source.py` before full pipeline
2. **Check Subreddits**: Make sure subreddit names are correct
3. **Time Filters**: Use "day" for daily content, "week" for weekly
4. **Diversity**: Bot ensures topics come from different sources
5. **Comments**: More popular posts = more/better comments

## 🐛 Troubleshooting

### "404 Not Found" for Subreddit
- Check subreddit name spelling
- Remove that subreddit from config

### "No topics fetched"
- Check internet connection
- Verify sources are enabled in config
- Try different time_filter

### No Comments Fetched
- Normal for HN (API doesn't include all comments)
- Reddit comments should work if post has them
- Check topic URL is accessible

## 📈 Future Enhancements

Potential additions:
- [ ] GitHub trending repos
- [ ] Product Hunt
- [ ] Discord/Slack channels (via webhooks)
- [ ] RSS feeds
- [ ] Custom APIs

## 🎓 Example Use Cases

1. **Daily AI News Video**
   - Sources: Reddit + HN
   - Time filter: "day"
   - Top 3 overall

2. **Weekly AI Roundup**
   - Sources: All enabled
   - Time filter: "week"
   - Top 5 per source

3. **Specific Community Focus**
   - Source: Reddit only
   - Subreddits: LocalLLaMA, Oobabooga
   - Deep dive into community discussions

---

**Last Updated**: February 8, 2026
**Status**: ✅ Fully Functional
**Sources Active**: Reddit ✅ | Hacker News ✅ | Twitter ⏸️ | Moltbook ⏸️
