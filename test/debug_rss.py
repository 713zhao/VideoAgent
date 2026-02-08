#!/usr/bin/env python3
"""Debug China News RSS feed."""

import requests

url = "https://www.chinanews.com/rss/"
response = requests.get(url, timeout=15)

print("Status Code:", response.status_code)
print("Content Type:", response.headers.get('content-type'))
print("\nFirst 1000 characters:")
print(response.text[:1000])
