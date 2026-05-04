from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from typing import Any, Literal

import httpx
import groq
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")

load_dotenv(os.path.join(BACKEND_DIR, ".env"))

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
DEFAULT_VOICE_ID = os.getenv("ELEVENLABS_DEFAULT_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb").strip()
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "").strip()
HUGGINGFACE_API_KEY_2 = os.getenv("HUGGINGFACE_API_KEY_2", "").strip()
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()

app = FastAPI(title="AI Sound Designer")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(BACKEND_DIR, "users.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class AuthRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=3, max_length=100)

@app.post("/api/auth/signup")
def signup(req: AuthRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)", 
                       (req.username, req.password, datetime.utcnow().isoformat()))
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")
    conn.close()
    return {"status": "success", "user_id": user_id, "username": req.username}

@app.post("/api/auth/login")
def login(req: AuthRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password FROM users WHERE username = ?", (req.username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or user[2] != req.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    return {"status": "success", "user_id": user[0], "username": user[1]}

@app.get("/api/admin/users")
def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password, created_at FROM users ORDER BY created_at DESC")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"users": users}

SoundMode = Literal["voice", "sfx", "music"]


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    mode: SoundMode
    duration_seconds: float = Field(default=5, ge=1, le=30)
    voice_id: str | None = None
    model_id: str = "eleven_multilingual_v2"


def require_api_key() -> str:
    if not ELEVENLABS_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="ELEVENLABS_API_KEY is missing. Add it to backend/.env and restart the server.",
        )
    return ELEVENLABS_API_KEY


def elevenlabs_headers() -> dict[str, str]:
    return {"xi-api-key": require_api_key()}


def elevenlabs_error(response: httpx.Response) -> HTTPException:
    try:
        detail = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text
    if isinstance(detail, str) and "detected_unusual_activity" in detail:
        detail = (
            "ElevenLabs blocked this API request for the current account/key: "
            "Free Tier usage is disabled because unusual activity was detected. "
            "Use a paid ElevenLabs plan, contact ElevenLabs support, or create a new valid key from an account that is allowed to use the API."
        )
    return HTTPException(status_code=response.status_code, detail=detail)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "project": "AI Sound Designer",
        "elevenlabs_configured": bool(ELEVENLABS_API_KEY),
    }


@app.get("/api/voices")
def list_voices() -> dict[str, Any]:
    with httpx.Client(timeout=30) as client:
        response = client.get(f"{ELEVENLABS_BASE_URL}/voices", headers=elevenlabs_headers())
    if response.status_code >= 400:
        raise elevenlabs_error(response)
    data = response.json()
    voices = [
        {
            "voice_id": voice.get("voice_id"),
            "name": voice.get("name"),
            "category": voice.get("category"),
        }
        for voice in data.get("voices", [])
    ]
    return {"voices": voices}


@app.post("/api/generate")
def generate_audio(req: GenerateRequest) -> Response:
    if req.mode == "voice":
        return generate_speech(req)
    if req.mode == "sfx":
        return generate_sound_effect(req)
    if req.mode == "music":
        return generate_music(req)
    raise HTTPException(status_code=400, detail="Unsupported mode")


def try_edge_tts_voice_sync(req: GenerateRequest) -> Response:
    import edge_tts
    import tempfile
    import asyncio
    
    async def _generate():
        communicate = edge_tts.Communicate(req.prompt, "en-US-ChristopherNeural")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_path = fp.name
        await communicate.save(temp_path)
        with open(temp_path, "rb") as f:
            content = f.read()
        os.remove(temp_path)
        return content
        
    try:
        content = asyncio.run(_generate())
        return Response(
            content=content,
            media_type="audio/mpeg",
            headers={"X-Filename": "edge_tts_voice.mp3"},
        )
    except Exception as e:
        raise Exception(f"EdgeTTS Error: {str(e)}")

def generate_speech(req: GenerateRequest) -> Response:
    errors = []
    try:
        voice_id = req.voice_id or DEFAULT_VOICE_ID
        payload = {
            "text": req.prompt,
            "model_id": req.model_id,
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.8,
                "style": 0.35,
                "use_speaker_boost": True,
            },
        }
        url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}?output_format=mp3_44100_128"
        headers = {**elevenlabs_headers(), "Content-Type": "application/json", "Accept": "audio/mpeg"}
        with httpx.Client(timeout=90) as client:
            response = client.post(url, headers=headers, json=payload)
        if response.status_code >= 400:
            raise Exception(f"Status {response.status_code}: {response.text}")
        return Response(
            content=response.content,
            media_type="audio/mpeg",
            headers={"X-Filename": "ai_sound_designer_voice.mp3"},
        )
    except Exception as e:
        errors.append(f"ElevenLabs: {e}")
        
    try:
        return try_edge_tts_voice_sync(req)
    except Exception as e:
        errors.append(f"EdgeTTS: {e}")
        
    raise HTTPException(status_code=500, detail="All Fallback APIs failed. Log: [" + " | ".join(errors) + "]")

def try_itunes_fallback(req: GenerateRequest, is_sfx: bool = False) -> Response:
    import urllib.parse
    import httpx
    
    query = req.prompt
    if is_sfx:
        query += " sound effect"
    else:
        query += " instrumental"
        
    url = f"https://itunes.apple.com/search?term={urllib.parse.quote(query)}&entity=song&limit=1"
    with httpx.Client(timeout=10) as client:
        resp = client.get(url)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("resultCount", 0) > 0:
                preview_url = data["results"][0].get("previewUrl")
                if preview_url:
                    audio_resp = client.get(preview_url)
                    if audio_resp.status_code == 200:
                        return Response(
                            content=audio_resp.content,
                            media_type="audio/mp4",
                            headers={"X-Filename": "itunes_fallback.m4a"},
                        )
    raise Exception("iTunes fallback failed or returned no preview.")

def generate_sound_effect(req: GenerateRequest) -> Response:
    errors = []
    try:
        payload = {
            "text": req.prompt,
            "duration_seconds": req.duration_seconds,
            "prompt_influence": 0.35,
        }
        headers = {**elevenlabs_headers(), "Content-Type": "application/json", "Accept": "audio/mpeg"}
        with httpx.Client(timeout=120) as client:
            response = client.post(f"{ELEVENLABS_BASE_URL}/sound-generation", headers=headers, json=payload)
        if response.status_code >= 400:
            raise Exception(f"Status {response.status_code}: {response.text}")
        return Response(
            content=response.content,
            media_type="audio/mpeg",
            headers={"X-Filename": "ai_sound_designer_sfx.mp3"},
        )
    except Exception as e:
        errors.append(f"ElevenLabs: {e}")
        
    try:
        return try_huggingface_sfx(req, HUGGINGFACE_API_KEY)
    except Exception as e:
        errors.append(f"HF1: {e}")
        
    try:
        return try_huggingface_sfx(req, HUGGINGFACE_API_KEY_2)
    except Exception as e:
        errors.append(f"HF2: {e}")
        
    try:
        return try_itunes_fallback(req, is_sfx=True)
    except Exception as e:
        errors.append(f"iTunesFallback: {e}")
        
    raise HTTPException(status_code=500, detail="All Fallback APIs failed. Log: [" + " | ".join(errors) + "]")


def try_stability_ai(req: GenerateRequest) -> Response:
    if not STABILITY_API_KEY:
        raise Exception("STABILITY_API_KEY is missing")
    headers = {"Authorization": f"Bearer {STABILITY_API_KEY}", "Accept": "audio/*"}
    multipart = {"prompt": (None, req.prompt), "output_format": (None, "mp3")}
    with httpx.Client(timeout=60) as client:
        response = client.post(
            "https://api.stability.ai/v2beta/audio/stable-audio-2/text-to-audio",
            headers=headers,
            files=multipart
        )
    if response.status_code >= 400:
        try:
            error_data = response.json()
            detail = error_data.get("message") or error_data.get("name") or str(error_data)
        except Exception:
            detail = response.text
        raise Exception(f"Status {response.status_code}: {detail}")
    return Response(
        content=response.content,
        media_type="audio/mpeg",
        headers={"X-Filename": "stability_music.mp3"},
    )


def try_elevenlabs_music(req: GenerateRequest) -> Response:
    if not ELEVENLABS_API_KEY:
        raise Exception("ELEVENLABS_API_KEY is missing")
    payload = {
        "prompt": req.prompt,
        "music_length_ms": int(req.duration_seconds * 1000),
        "model_id": "music_v1",
    }
    headers = {**elevenlabs_headers(), "Content-Type": "application/json", "Accept": "audio/mpeg"}
    with httpx.Client(timeout=60) as client:
        response = client.post(f"{ELEVENLABS_BASE_URL}/music", headers=headers, json=payload)
    if response.status_code >= 400:
        try:
            err = response.json().get("detail", {}).get("message", response.text)
        except Exception:
            err = response.text
        raise Exception(f"Status {response.status_code}: {err}")
    return Response(
        content=response.content,
        media_type=response.headers.get("content-type", "audio/mpeg"),
        headers={"X-Filename": "elevenlabs_music.mp3"},
    )


def try_huggingface_music(req: GenerateRequest, api_key: str) -> Response:
    if not api_key:
        raise Exception("API key is missing")
    payload = {"inputs": req.prompt}
    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(timeout=60) as client:
        response = client.post(
            "https://api-inference.huggingface.co/models/facebook/musicgen-small",
            headers=headers,
            json=payload
        )
    if response.status_code >= 400:
        try:
            err = response.json().get("error", response.text)
        except Exception:
            err = response.text
        raise Exception(f"Status {response.status_code}: {err}")
    return Response(
        content=response.content,
        media_type="audio/wav",
        headers={"X-Filename": "huggingface_music.wav"},
    )


def try_huggingface_sfx(req: GenerateRequest, api_key: str) -> Response:
    if not api_key:
        raise Exception("API key is missing")
    payload = {"inputs": req.prompt}
    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(timeout=60) as client:
        response = client.post(
            "https://api-inference.huggingface.co/models/cvssp/audioldm2",
            headers=headers,
            json=payload
        )
    if response.status_code >= 400:
        try:
            err = response.json().get("error", response.text)
        except Exception:
            err = response.text
        raise Exception(f"Status {response.status_code}: {err}")
    return Response(
        content=response.content,
        media_type="audio/wav",
        headers={"X-Filename": "huggingface_sfx.wav"},
    )

def try_huggingface_voice(req: GenerateRequest, api_key: str) -> Response:
    if not api_key:
        raise Exception("API key is missing")
    payload = {"inputs": req.prompt}
    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(timeout=60) as client:
        response = client.post(
            "https://api-inference.huggingface.co/models/espnet/kan-bayashi_ljspeech_vits",
            headers=headers,
            json=payload
        )
    if response.status_code >= 400:
        try:
            err = response.json().get("error", response.text)
        except Exception:
            err = response.text
        raise Exception(f"Status {response.status_code}: {err}")
    return Response(
        content=response.content,
        media_type="audio/wav",
        headers={"X-Filename": "huggingface_voice.wav"},
    )


def generate_music(req: GenerateRequest) -> Response:
    errors = []
    
    # 1. Primary: Stability AI
    try:
        return try_stability_ai(req)
    except Exception as e:
        errors.append(f"Stability: {e}")
        
    # 2. Fallback 1: ElevenLabs
    try:
        return try_elevenlabs_music(req)
    except Exception as e:
        errors.append(f"ElevenLabs: {e}")
        
    # 3. Fallback 2: Hugging Face (Primary Key)
    try:
        return try_huggingface_music(req, HUGGINGFACE_API_KEY)
    except Exception as e:
        errors.append(f"HuggingFace1: {e}")

    # 4. Fallback 3: Hugging Face (Secondary Key)
    try:
        return try_huggingface_music(req, HUGGINGFACE_API_KEY_2)
    except Exception as e:
        errors.append(f"HuggingFace2: {e}")
        
    # 5. Final Free Fallback: iTunes
    try:
        return try_itunes_fallback(req, is_sfx=False)
    except Exception as e:
        errors.append(f"iTunesFallback: {e}")
        
    # If all fail, throw HTTP error with the chain of failures
    raise HTTPException(
        status_code=500, 
        detail="All Fallback APIs failed. Log: [" + " | ".join(errors) + "]"
    )

class RouteIntentRequest(BaseModel):
    prompt: str

@app.post("/api/route-intent")
def route_intent(req: RouteIntentRequest) -> dict:
    if not GROQ_API_KEY:
        raise HTTPException(status_code=400, detail="GROQ_API_KEY is missing")
    
    import groq
    
    client = groq.Client(api_key=GROQ_API_KEY)
    
    system_prompt = (
        "You are an intelligent routing assistant for an AI Sound Design studio. "
        "The studio has three modes: 'Sound Effects', 'Text to Voice', and 'Scenario to Song'. "
        "The user will give you a prompt. Your job is to determine what they want to do. "
        "If it is highly ambiguous (e.g., 'lion roar', 'cars crashing'), ask them to clarify by selecting a mode and provide 'clarification_needed': true, and return the relevant modes in 'suggested_modes'. "
        "If the intent is clear (e.g., 'give me a lion roar sound effect', 'recommend a song about lions'), return 'clarification_needed': true with just the ONE clear mode in 'suggested_modes' so the user can click it to confirm. "
        "You MUST output raw JSON with exactly these three keys: 'clarification_needed' (boolean), 'message' (a friendly string asking the user what to do or confirming), and 'suggested_modes' (an array of strings matching the exact mode names)."
    )
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"User Prompt: {req.prompt}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1024
        )
        
        response_text = completion.choices[0].message.content.strip()
        import json
        data = json.loads(response_text)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SuggestSongRequest(BaseModel):
    prompt: str

@app.post("/api/suggest-song")
def suggest_song(req: SuggestSongRequest) -> dict:
    if not GROQ_API_KEY:
        raise HTTPException(status_code=400, detail="GROQ_API_KEY is missing")
    
    import groq
    
    client = groq.Client(api_key=GROQ_API_KEY)
    
    system_prompt = (
        "You are a highly knowledgeable global music AI assistant. "
        "A user will give you a scenario, mood, or a direct request for a specific song, artist, or genre (e.g., Punjabi, Bollywood, Devotional, Pop). "
        "IMPORTANT: The user may provide a chat history. ALWAYS prioritize the LAST sentence or request as their current and true intention. "
        "You MUST pay very close attention to cultural or genre keywords (like 'devotional', 'bhakti', 'dijit/diljit', etc.) and correct any typos in the user's prompt. "
        "If the user asks for a specific artist or genre, YOU MUST strictly honor that request and suggest a real, popular song fitting that exact request. "
        "Ensure the song is very well known and available on Apple Music. "
        "You MUST output raw JSON with exactly these three keys: 'song_title', 'artist', and 'explanation'. "
    )
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Scenario or Request: {req.prompt}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1024
        )
        
        response_text = completion.choices[0].message.content.strip()
        
        import json
        import urllib.parse
        import httpx
        
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON from AI: {e}. Raw text: {response_text}")
        song_title = data.get("song_title", "")
        artist = data.get("artist", "")
        explanation = data.get("explanation", "")
        
        preview_url = None
        artwork_url = None
        
        if song_title and artist:
            # First try title + artist
            query = urllib.parse.quote(f"{song_title} {artist}")
            itunes_url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=5"
            try:
                resp = httpx.get(itunes_url, timeout=5.0)
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    for r in results:
                        if r.get("previewUrl"):
                            preview_url = r.get("previewUrl")
                            artwork_url = r.get("artworkUrl100")
                            # Sync title/artist with actual iTunes data for accuracy
                            song_title = r.get("trackName", song_title)
                            artist = r.get("artistName", artist)
                            break
                            
                    # Fallback: if no preview found, try just the song title
                    if not preview_url:
                        query2 = urllib.parse.quote(song_title)
                        resp2 = httpx.get(f"https://itunes.apple.com/search?term={query2}&entity=song&limit=5", timeout=5.0)
                        if resp2.status_code == 200:
                            for r in resp2.json().get("results", []):
                                if r.get("previewUrl"):
                                    preview_url = r.get("previewUrl")
                                    artwork_url = r.get("artworkUrl100")
                                    song_title = r.get("trackName", song_title)
                                    artist = r.get("artistName", artist)
                                    break
            except Exception as e:
                print("iTunes fetch error:", e)
        
        if not explanation:
            explanation = response_text
            
        return {
            "text": f"**{song_title}** by {artist}\n\n{explanation}",
            "preview_url": preview_url,
            "artwork_url": artwork_url,
            "song_title": song_title,
            "artist": artist
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clone-voice")
def clone_voice(name: str = Form(...), files: list[UploadFile] = File(...)) -> dict[str, Any]:
    if not files:
        raise HTTPException(status_code=400, detail="Upload at least one voice sample.")

    multipart: list[tuple[str, Any]] = [("name", (None, name))]
    for audio_file in files[:5]:
        multipart.append(
            (
                "files",
                (
                    audio_file.filename or "sample.mp3",
                    audio_file.file.read(),
                    audio_file.content_type or "audio/mpeg",
                ),
            )
        )

    with httpx.Client(timeout=180) as client:
        response = client.post(
            f"{ELEVENLABS_BASE_URL}/voices/add",
            headers=elevenlabs_headers(),
            files=multipart,
        )
    if response.status_code >= 400:
        raise elevenlabs_error(response)

    data = response.json()
    return {"voice_id": data.get("voice_id"), "name": name}


@app.post("/api/voice-changer")
def voice_changer(voice_id: str = Form(DEFAULT_VOICE_ID), file: UploadFile = File(...)) -> Response:
    multipart: list[tuple[str, Any]] = [
        ("audio", (file.filename or "sample.mp3", file.file.read(), file.content_type or "audio/mpeg"))
    ]
    with httpx.Client(timeout=180) as client:
        response = client.post(
            f"{ELEVENLABS_BASE_URL}/speech-to-speech/{voice_id}",
            headers=elevenlabs_headers(),
            files=multipart,
        )
    if response.status_code >= 400:
        raise elevenlabs_error(response)
    return Response(
        content=response.content,
        media_type="audio/mpeg",
        headers={"X-Filename": "ai_sound_designer_voice_changer.mp3"},
    )


@app.post("/api/audio-cleaner")
def audio_cleaner(file: UploadFile = File(...)) -> Response:
    multipart: list[tuple[str, Any]] = [
        ("audio", (file.filename or "sample.mp3", file.file.read(), file.content_type or "audio/mpeg"))
    ]
    with httpx.Client(timeout=180) as client:
        response = client.post(
            f"{ELEVENLABS_BASE_URL}/audio-isolation",
            headers=elevenlabs_headers(),
            files=multipart,
        )
    if response.status_code >= 400:
        raise elevenlabs_error(response)
    return Response(
        content=response.content,
        media_type="audio/mpeg",
        headers={"X-Filename": "ai_sound_designer_audio_cleaner.mp3"},
    )


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
