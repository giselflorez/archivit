#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('PERPLEXITY_API_KEY')
print(f"API Key (first 10 chars): {api_key[:10]}...")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Try the correct Perplexity API format
payload = {
    "model": "sonar-small-online",
    "messages": [
        {
            "role": "user",
            "content": "What is founder?"
        }
    ]
}

print("\nTesting Perplexity API...")
print(f"URL: https://api.perplexity.ai/chat/completions")

try:
    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        json=payload,
        headers=headers,
        timeout=30
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code != 200:
        print(f"Error Response: {response.text}")
    else:
        print("Success!")
        result = response.json()
        print(f"Response: {result}")

except Exception as e:
    print(f"Exception: {e}")
