#!/usr/bin/env python3
"""Find actual RSS feed URLs from China News."""

import requests
from bs4 import BeautifulSoup

url = "https://www.chinanews.com/rss/"
response = requests.get(url, timeout=15)
soup = BeautifulSoup(response.content, 'html.parser')

# Find all links that might be RSS feeds
rss_links = []
for link in soup.find_all('a', href=True):
    href = link.get('href', '')
    if 'rss' in href or '.xml' in href:
        rss_links.append({
            'text': link.get_text().strip(),
            'href': href if href.startswith('http') else f"https://www.chinanews.com{href}"
        })

print(f"Found {len(rss_links)} RSS feed links:\n")
for i, rss in enumerate(rss_links[:10], 1):  # Show first 10
    print(f"{i}. {rss['text']}")
    print(f"   URL: {rss['href']}\n")
