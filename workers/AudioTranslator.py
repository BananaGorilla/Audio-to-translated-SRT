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

    def __init__(self, input_file_name=None, output_file_name=None):
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

        # if no output filename provided, create one with timestamp: translation_YYYYmmdd_HHMMSS.txt
        if output_file_name:
            self.output_file_name = output_file_name
        else:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_file_name = f"translation_{ts}.txt"

        self.system_prompt = """
            Translate this English SRT content into Chinese.
            If it has Pali language, please translate the Pali too and bracket the original Pali text.
            Make it friendly readable. Do not keep the SRT format, just translate the text content.
            """

    @pyqtSlot()
    def run(self):
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
            with open(self.output_file_name, "w", encoding="utf-8") as f:
                f.write(translation_result)
            logger.info("Translation completed and saved successfully.")
            self.translation_complete.emit(self.output_file_name)
        except Exception as e:
            logger.error(f"Failed to generate translation: {e}")
            self.progress_updated.emit(f"Failed to generate translation: {e}")
