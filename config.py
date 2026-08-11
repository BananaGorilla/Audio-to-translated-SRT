from enum import Enum

AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg")

GEMINI_MODEL = "gemini-2.5-flash"
OPENAI_WHISPER_MODEL = "whisper-1"

# Environment variable names for the local whisper.cpp setup.  The paths are
# configured from the Settings screen instead of being hard-coded in source.
LOCAL_WHISPER_CLI_PATH = "LOCAL_WHISPER_CLI_PATH"
LOCAL_WHISPER_MODEL_PATH = "LOCAL_WHISPER_MODEL_PATH"

SELECTED_TRANSCRIPTION_MODEL = "SELECTED_TRANSCRIPTION_MODEL"
SELECTED_TRANSLATION_MODEL = "SELECTED_TRANSLATION_MODEL"

# Environment variable name for the GGUF model used by the local translator.
LOCAL_LLM_GGUF_FILE_PATH = "LOCAL_LLM_GGUF_FILE_PATH"

# Lookup tables
TranscriptionModelLookup = {
    "Gemini Flash":   "gemini/gemini-2.5-flash",
    "OpenAI Whisper": "openai/whisper-1",
    "Local Whisper": "local/whisper",
}

TranslationModelLookup = {
    "Gemini Flash": "gemini/gemini-2.5-flash",
    "Claude Sonnet": "anthropic/claude-sonnet-4-20250514",
    "GPT-4o": "openai/gpt-4o-2024-11-20",
    "Local Translator": "local/translator",
}

ModelProviderApiLookup = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "local": "LOCAL_MODEL_API_KEY"
}

class AIClientUsage(Enum):
    TRANSCRIPTION = 0
    TRANSLATION = 1
