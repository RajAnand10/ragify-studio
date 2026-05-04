import os, httpx, wave, struct
from dotenv import load_dotenv
load_dotenv("backend/.env")
api_key = os.getenv("ELEVENLABS_API_KEY")

# Create a valid 5-second silent WAV file
with wave.open("dummy.wav", "w") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(44100)
    for _ in range(44100 * 5):
        f.writeframesraw(struct.pack("<h", 0))

with open("dummy.wav", "rb") as f:
    files = {"audio": ("dummy.wav", f, "audio/wav")}
    response = httpx.post(
        "https://api.elevenlabs.io/v1/audio-isolation",
        headers={"xi-api-key": api_key},
        files=files
    )
print("Status:", response.status_code)
# Do not print response.text if it's binary audio
if response.status_code >= 400:
    print("Response:", response.text)
else:
    print("Success! Got isolated audio of size:", len(response.content))
