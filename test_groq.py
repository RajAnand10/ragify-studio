import os
import json
from dotenv import load_dotenv
import groq

load_dotenv('/Users/rajanand/.gemini/antigravity/scratch/chatbot-sound-design/CHATBOT/backend/.env')
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = groq.Client(api_key=GROQ_API_KEY)

system_prompt = (
    "You are a highly knowledgeable global music AI assistant. "
    "A user will give you a scenario, mood, or a direct request for a specific song, artist, or genre (e.g., Punjabi, Bollywood, Devotional, Pop). "
    "You MUST pay very close attention to cultural or genre keywords (like 'devotional', 'bhakti', 'dijit/diljit', etc.) and correct any typos in the user's prompt. "
    "If the user asks for a specific artist or genre, YOU MUST strictly honor that request and suggest a real, popular song fitting that exact request. "
    "Ensure the song is very well known and available on Apple Music. "
    "You MUST output raw JSON with exactly these three keys: 'song_title', 'artist', and 'explanation'. "
)

prompts = [
    "I AM RIDING BIKE I NNED TO LISTEN DEVOTATIONAL SONG",
    "I AM RIDING BIKE I NNED TO LISTEN DEVOTATIONAL SONG. PALY DIJIT SONG"
]

for p in prompts:
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Scenario or Request: {p}"}
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=256
    )
    print(f"Prompt: {p}")
    print("Response:", completion.choices[0].message.content)
    print("-" * 50)
