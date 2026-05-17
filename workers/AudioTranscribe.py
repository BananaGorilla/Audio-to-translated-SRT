from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import logging

from workers.common_tools import create_ai_client
import config

logger = logging.getLogger(__name__)

class AudioTranscribeWorker(QObject):
    # Signals that UI listens to
    transcribe_complete = pyqtSignal(str)
    progress_updated = pyqtSignal(str)

    def __init__(self, audio_file_path=None, output_file_name=None):
        super().__init__()

        self.client = create_ai_client()
        # Error handling for missing AI API key
        if not self.client:
            logger.error("No AI client available.")
            self.progress_updated.emit("No AI client available")
            raise ValueError("No AI client available.")

        self.audio_file_path = audio_file_path
        self.output_file_name = output_file_name
        # Error handling for missing audio file path
        if not self.audio_file_path:
            logger.error("Audio file path is required for transcription.")
            self.progress_updated.emit("No audio file path provided")
            raise ValueError("Audio file path is required for transcription.")

        self.transcribe_prompt = """
            Transcribe this English audio.
            If it has Pali language, please transcribe the Pali part as well, but keep the Pali text in its original script without romanization.
            Return ONLY valid SRT format with timestamps.
            Keep each subtitle block to 10 words max.
            Example format:
            1
            00:00:00,000 --> 00:00:05,200
            Transcribe sentence here.
            Do not repeat the same end timestamp to the next start timstamp. Add 1 millisecond to the next start timestamp if they are the same.
            """
    
    @pyqtSlot()
    def run(self):
        logger.info("AudioTranscribeWorker started running.")

        self.progress_updated.emit("Uploading audio file...")
        uploaded_file = self.client.files.upload(file=self.audio_file_path)
        logger.info("Audio file uploaded successfully.")

        # Generate Output (e.g., Translation)
        # Save into the file immediately
        self.progress_updated.emit("Prompting the AI model for transcription...")
        response = self.client.models.generate_content(
            model=config.MODEL_ID,
            contents=[
                self.transcribe_prompt,
                uploaded_file
            ]
        )
        logger.info("Transcription completed successfully.")

        transcribed_text = getattr(response, "text", "")
        with open(self.output_file_name, "a", encoding="utf-8") as f:
            f.write(transcribed_text)
        
        self.transcribe_complete.emit("Done")
        logger.info("Transcribed content saved to file and signal emitted.")

        