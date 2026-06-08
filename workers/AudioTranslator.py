from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from workers.common_tools import create_ai_client
import config
import logging

logger = logging.getLogger(__name__)

class AudioTranslatorWorker(QObject):
    # Signals that UI listens to
    translation_complete = pyqtSignal(str)
    progress_updated = pyqtSignal(str)

    def __init__(self, input_file_name=None, source_language="English", target_language="Chinese"):
        super().__init__()

        self.client = create_ai_client()
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

        self.source_language = source_language
        self.target_language = target_language

        self.system_prompt = f"""
            Translate this {source_language} SRT content into {target_language}.
            If it has Pali language, please translate the Pali too and bracket the original Pali text.
            Make it friendly readable. Keep the SRT format, and translate the text content.
            """

    @pyqtSlot()
    def run_on_cloud(self):
        logger.info("AudioTranslatorWorker started running.")
        self.progress_updated.emit("Reading input SRT file...")
        try:
            with open(self.input_file_name, "r", encoding="utf-8") as f:
                srt_content = f.read()
        except Exception as e:
            logger.error(f"Failed to read input file: {e}")
            self.progress_updated.emit(f"Failed to read input file: {e}")
            return

        self.progress_updated.emit("Prompting the AI model for translation...")
        try:
            response = self.client.models.generate_content(
                model=config.MODEL_ID,
                contents=[
                    self.system_prompt,
                    srt_content
                ]
            )
            translation_result = response.text
            self.translation_complete.emit(translation_result)
        except Exception as e:
            logger.error(f"Failed to generate translation: {e}")
            self.progress_updated.emit(f"Failed to generate translation: {e}")
