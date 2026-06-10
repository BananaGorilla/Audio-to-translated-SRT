import os
from dotenv import load_dotenv
from google import genai
from openai import OpenAI
import config

def create_ai_client(usage: int = config.AIClientUsage.TRANSCRIPTION.value):
    # Load environment variables from .env file
    load_dotenv()
    client = None

    if(usage == config.AIClientUsage.TRANSCRIPTION.value):
        if os.getenv("TRANSCRIPTION_MODEL") == config.TRANSCRIPTION_MODELS["Gemini Flash"]:
            api_key = os.getenv("GEMINI_API_KEY")
            client = genai.Client(api_key=api_key)
        if os.getenv("TRANSCRIPTION_MODEL", "").startswith("openai/"):
            api_key = os.getenv("OPENAI_API_KEY")
            client = OpenAI(api_key=api_key)
        if os.getenv("TRANSCRIPTION_MODEL") == config.TRANSCRIPTION_MODELS["Local Whisper"]:
            api_key = os.getenv("LOCAL_WHISPER_API_KEY")
            client = "Local Whisper"  # Local Whisper doesn't require an API client, but we return a string to indicate local mode
    elif(usage == config.AIClientUsage.TRANSLATION.value):
        if os.getenv("TRANSLATION_MODEL") == config.TRANSLATION_MODELS["Gemini Flash"]:
            api_key = os.getenv("GEMINI_API_KEY")
            client = genai.Client(api_key=api_key)
        if os.getenv("TRANSLATION_MODEL") == config.TRANSLATION_MODELS["Claude Sonnet"]:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            client = OpenAI(api_key=api_key)
        if os.getenv("TRANSLATION_MODEL") == config.TRANSLATION_MODELS["GPT-4o"]:
            api_key = os.getenv("OPENAI_API_KEY")
            client = OpenAI(api_key=api_key)
    
    return client