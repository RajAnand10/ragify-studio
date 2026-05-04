import os
import requests
from dotenv import load_dotenv

load_dotenv("backend/.env")
key = os.getenv("STABILITY_API_KEY")

headers = {"Authorization": f"Bearer {key}", "Accept": "audio/*"}
files = {"prompt": (None, "A lion roaring loudly"), "output_format": (None, "mp3")}
url = "https://api.stability.ai/v2beta/audio/stable-audio-2/text-to-audio"
print("Testing Stability AI...")
resp = requests.post(url, headers=headers, files=files)
print(resp.status_code)
if resp.status_code == 200:
    print("Success! Got audio.")
else:
    print(resp.text[:200])
