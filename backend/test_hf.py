import httpx
import os
from dotenv import load_dotenv

load_dotenv(".env")
hf_key = os.getenv("HUGGINGFACE_API_KEY")

def test_tts(model):
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {hf_key}"}
    response = httpx.post(url, headers=headers, json={"inputs": "Hello, this is a test of voice fallback."})
    print(f"TTS Status for {model}:", response.status_code)

test_tts("espnet/kan-bayashi_ljspeech_vits")
test_tts("suno/bark-small")
