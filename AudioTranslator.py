from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import logging

from datetime import datetime
from common_tools import create_ai_client
import config

logger = logging.getLogger(__name__)

class AudioTranslatorWorker(QObject):
    # Signals that UI listens to
    translation_complete = pyqtSignal(str)
    progress_updated = pyqtSignal(str)

    def __init__(self, input_srt_file_name=None, output_file_name=None, target_language="Chinese"):
        super().__init__()
        
        self.input_srt_file_name = input_srt_file_name
        # Error handling for missing input SRT file name
        if not self.input_srt_file_name:
            logger.error("Input SRT file name is required for translation.")
            self.progress_updated.emit("No input SRT file name provided")
            raise ValueError("Input SRT file name is required for translation.")
        
        # if no output filename provided, create one with timestamp: translation_YYYYmmdd_HHMMSS.txt
        if output_file_name:
            self.output_file_name = output_file_name
        else:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_file_name = f"translation_to_{target_language}_{ts}.txt"

        self.client = create_ai_client()
        # Error handling for client fail initialization
        if not self.client:
            logger.error("No AI client available.")
            self.progress_updated.emit("No AI client available")
            raise ValueError("No AI client available.")

        self.translate_prompt = f"""
            Translate this English SRT content into {target_language}.
            If it has Pali language, please translate the Pali too and bracket the original Pali text.
            Make it friendly readable. Do not keep the SRT format, just translate the text content and save it into a text file.
            """
        # ykdebug: not using them at this moment
        # with open(self.output_file_name, "w", encoding="utf-8") as f:
        #     f.write("---Start translation---\n\n")

        # self.system_prompt = """
        #     You are a specialized Thai-to-English translator.
        #     FOUNDATIONAL RULES:
        #     1. If the Thai audio is ambiguous, provide the most culturally relevant translation with bracket.
        #     2. Please keep it Pali words as it is and do not translate it.
        #     3. Do not include Thai words in the translation output.
        #     4. Please make it friendly readable by breaking into sentences and paragraphs, and add punctuation if necessary.
        #     """


    # ykdebug: do not run this function until it is ready
    # def process_long_audio(self, file_path):
    #     if not self.client:
    #         raise RuntimeError("No API client available (missing API key).")

    #     uploaded_file = self.client.files.upload(file=file_path)

    #     # Generate Output (e.g., Translation)
    #     # Save into the file immediately
    #     print("--generate output--")
    #     response = self.client.models.generate_content(
    #         model=self.model_id,
    #         contents=[
    #             self.system_prompt,
    #             uploaded_file
    #         ]
    #     )

    #     translated_text = getattr(response, "text", "")
    #     with open(self.output_file_name, "a", encoding="utf-8") as f:
    #         f.write(translated_text)
    #         f.write("\n\n")

    # This part is uploading the SRT file and ask the model to translate it, then save the translation into a text file.
    @pyqtSlot()
    def run(self):
        logger.info("AudioTranslatorWorker started running.")

        # Upload the SRT file
        self.progress_updated.emit("Uploading SRT file...")
        uploaded_file = self.client.files.upload(file=self.input_srt_file_name)
        logger.info("SRT file uploaded successfully.")

        # Calling API to ask the model to translate the SRT content
        self.progress_updated.emit("Prompting the AI model for translation...")
        response = self.client.models.generate_content(
            model=config.MODEL_ID,
            contents=[
                self.translate_prompt,
                uploaded_file
            ]
        )
        logger.info("Translation completed successfully.")

        # Save the translation into a text file
        translated_text = getattr(response, "text", "")
        with open(self.output_file_name, "a", encoding="utf-8") as f:
            f.write(translated_text)

        self.translation_complete.emit("Done")
        logger.info("Translation content saved to file and signal emitted.")
