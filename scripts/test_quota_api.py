#!/usr/bin/env python3
"""Test real quota API via fetchAvailableModels."""
import json, urllib.request, os

TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)),
    "auth/home/.gemini/antigravity-cli/antigravity-oauth-token")

with open(TOKEN_FILE) as f:
    d = json.load(f)

t = d.get("token", {})
access_token = t.get("access_token", "")

req = urllib.request.Request(
    "https://daily-cloudcode-pa.googleapis.com/v1internal:fetchAvailableModels",
    data=b"{}",
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "antigravity"
    },
    method="POST"
)
try:
    r = urllib.request.urlopen(req, timeout=10)
    data2 = json.loads(r.read())
    models = data2.get("models", {})
    for k, v in models.items():
        qi = v.get("quotaInfo", {})
        print(f"  {k}: remaining={qi.get('remainingFraction')}, exhausted={qi.get('isExhausted')}, reset={qi.get('resetTime')}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP Error: {e.code} {body[:400]}")
except Exception as e:
    print(f"Error: {e}")
