import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv('/Users/rajanand/.gemini/antigravity/scratch/chatbot-sound-design/CHATBOT/backend/.env')
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents='What is the capital of France?',
    )
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
