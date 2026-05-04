import os
import requests
from dotenv import load_dotenv

load_dotenv("backend/.env")
hf_key = os.getenv("HUGGINGFACE_API_KEY")

headers = {"Authorization": f"Bearer {hf_key}"}
payload = {"inputs": "A dog barking loudly"}

print("Testing suno/bark...")
url = "https://api-inference.huggingface.co/models/suno/bark"
resp = requests.post(url, headers=headers, json=payload)
print(resp.status_code)
if resp.status_code == 200:
    print("Success!")
else:
    print(resp.text[:200])
