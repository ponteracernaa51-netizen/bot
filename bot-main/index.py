"""
index.py — quick API smoke-test (development only, not used by the bot).

Usage:
    python index.py
"""

import httpx
import os
from dotenv import load_dotenv

load_dotenv()

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "")

url = "https://api.together.xyz/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json",
}
body = {
    "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    "messages": [{"role": "user", "content": "Say hello"}],
}

r = httpx.post(url, json=body, headers=headers)
print(r.status_code)
print(r.text)