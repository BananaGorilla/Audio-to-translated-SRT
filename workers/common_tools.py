import os
from dotenv import load_dotenv
from google import genai

def create_ai_client():
    # Load environment variables from .env file
    load_dotenv()
    api_key = os.getenv("API_KEY")

    client = None

    # Initialize the GenAI client if API key is available
    if api_key:
        client = genai.Client(api_key=api_key)
    
    return client