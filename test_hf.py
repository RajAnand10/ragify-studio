import os
import requests
from dotenv import load_dotenv

load_dotenv("backend/.env")
hf_key = os.getenv("HUGGINGFACE_API_KEY")

headers = {"Authorization": f"Bearer {hf_key}"}
payload = {"inputs": "A lion roaring loudly"}

models = [
    "cvssp/audioldm2",
    "facebook/audiogen-medium",
    "haoheliu/AudioLDM2"
]

for model in models:
    print(f"Testing {model}...")
    url = f"https://api-inference.huggingface.co/models/{model}"
    resp = requests.post(url, headers=headers, json=payload)
    print(resp.status_code)
    if resp.status_code == 200:
        print("Success!")
    else:
        print(resp.text[:200])
