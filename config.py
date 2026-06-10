from enum import Enum

AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg")

GEMINI_MODEL = "gemini-2.5-flash"
OPENAI_WHISPER_MODEL = "whisper-1"

LOCAL_WHISPER_CLI_PATH = # Please insert your path to the whisper.cpp executable here
LOCAL_WHISPER_MODEL_PATH = # Please insert your path to the whisper.cpp model file here

TRANSCRIPTION_MODELS = {
    "Gemini Flash":   "gemini/gemini-2.5-flash",
    "OpenAI Whisper": "openai/whisper-1",
    "Local Whisper": "local/whisper",
}

TRANSLATION_MODELS = {
    "Gemini Flash":   "gemini/gemini-2.5-flash",
    "Claude Sonnet": "anthropic/claude-sonnet-4-20250514",
    "GPT-4o":       "openai/gpt-4o",
}

class AIClientUsage(Enum):
    TRANSCRIPTION = 0
    TRANSLATION = 1