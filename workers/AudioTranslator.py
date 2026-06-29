from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from workers.common_tools import create_ai_client
import config
import logging
from litellm import completion
import os

logger = logging.getLogger(__name__)

class AudioTranslatorWorker(QObject):
    # Signals that UI listens to
    translation_complete = pyqtSignal(str)
    progress_updated = pyqtSignal(str)

    def __init__(self, input_file_name=None, source_language="English", target_language="Simplified Chinese"):
        super().__init__()

        self.client = create_ai_client(config.AIClientUsage.TRANSLATION.value)
        # Error handling for missing AI API key
        if not self.client:
            logger.error("No AI client available.")
            self.progress_updated.emit("No AI client available")
            raise ValueError("No AI client available.")
        
        # Error handling for missing input file name
        if input_file_name:
            self.input_file_name = input_file_name
        else:
            logger.error("Input file name is required for translation.")
            self.progress_updated.emit("No input file name provided")
            raise ValueError("Input file name is required for translation.")

        with open(self.input_file_name, "r", encoding="utf-8") as f:
            srt_content = f.read()

        self.system_prompt = f"""
            You are a professional translator specializing in translating subtitles and Buddhism context across different lineages. 
            If it has Pali language, please translate the Pali too and bracket the original Pali text. 
            Make it friendly readable, but do not change the timestamps. Keep the same format, and just reply the outcome.
            """
        
        self.user_prompt = f"""
            Translate this {source_language} SRT content into {target_language}:\n\n
            {srt_content}
            """

    @pyqtSlot()
    def run(self):
        self.progress_updated.emit("Prompting the AI model for translation...")
        response = completion(
            model=os.getenv(config.SELECTED_TRANSLATION_MODEL),
            messages=[
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": self.user_prompt
                }
            ]
        )
        translation_result = response.choices[0].message.content
        self.translation_complete.emit(translation_result)