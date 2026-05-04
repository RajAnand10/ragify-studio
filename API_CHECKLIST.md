# API Checklist For AI Sound Designer

Before coding the real chatbot, collect these details for the API you choose.

## Required

- API provider name:
- Website/docs link:
- API key:
- Base URL:
- Text-to-sound endpoint:
- Authentication method:
- Request method: `POST` or other
- Request JSON body example:
- Response example:
- Does it return audio directly, an audio URL, or a job ID?
- Supported output formats: WAV, MP3, etc.
- Free tier or pricing limit:

## Good APIs To Research

- ElevenLabs sound effects API
- Stability AI audio / sound generation
- Replicate audio models
- Hugging Face audio generation models
- Groq/OpenAI only for chatbot text planning, not sound generation unless paired with an audio API

## Final App Flow

1. User types a prompt.
2. Chatbot improves the prompt for sound design.
3. Backend sends prompt to the sound API.
4. API returns audio.
5. Frontend shows audio player, waveform, and download button.
