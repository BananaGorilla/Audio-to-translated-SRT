from google import genai
from datetime import datetime

class AudioTranslator:
    def __init__(self, api_key_file_path="./GOOGLE_GENAI_API_KEY.txt", model_id="gemini-2.5-flash", output_file_name=None):
        self.api_key_file_path = api_key_file_path
        self.model_id = model_id
        # if no output filename provided, create one with timestamp: translation_YYYYmmdd_HHMMSS.txt
        if output_file_name:
            self.output_file_name = output_file_name
        else:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_file_name = f"translation_{ts}.txt"

        key = None
        try:
            with open(self.api_key_file_path, 'r') as file:
                key = file.read().strip()
        except FileNotFoundError:
            print(f"Error: The file at {self.api_key_file_path} was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

        if key:
            self.client = genai.Client(api_key=key)
        else:
            self.client = None

        with open(self.output_file_name, "w", encoding="utf-8") as f:
            f.write("---Start translation---\n\n")

        self.system_prompt = """
            You are a specialized Thai-to-English translator.
            FOUNDATIONAL RULES:
            1. If the Thai audio is ambiguous, provide the most culturally relevant translation with bracket.
            2. Please keep it Pali words as it is and do not translate it.
            3. Do not include Thai words in the translation output.
            4. Please make it friendly readable by breaking into sentences and paragraphs, and add punctuation if necessary.
            """

    def process_long_audio(self, file_path):
        if not self.client:
            raise RuntimeError("No API client available (missing API key).")

        uploaded_file = self.client.files.upload(file=file_path)

        # Generate Output (e.g., Translation)
        # Save into the file immediately
        print("--generate output--")
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=[
                self.system_prompt,
                uploaded_file
            ]
        )

        translated_text = getattr(response, "text", "")
        with open(self.output_file_name, "a", encoding="utf-8") as f:
            f.write(translated_text)
            f.write("\n\n")
