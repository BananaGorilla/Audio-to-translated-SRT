from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import logging
from workers.common_tools import create_ai_client
import config
import subprocess
import os

logger = logging.getLogger(__name__)

class AudioTranscribeWorker(QObject):
    # Signals that UI listens to
    transcribe_complete = pyqtSignal(str)
    progress_updated = pyqtSignal(str)

    def __init__(self, audio_file_path=None, source_language="English", timestamp_needed=False):
        super().__init__()

        self.client = create_ai_client(config.AIClientUsage.TRANSCRIPTION.value)
        # Error handling for missing AI API key
        if not self.client:
            logger.error("No AI client available.")
            self.progress_updated.emit("No AI client available")
            raise ValueError("No AI client available.")

        self.audio_file_path = audio_file_path
        self.source_language = source_language
        self.timestamp_needed = timestamp_needed
        
        # Error handling for missing audio file path
        if not self.audio_file_path:
            logger.error("Audio file path is required for transcription.")
            self.progress_updated.emit("No audio file path provided")
            raise ValueError("Audio file path is required for transcription.")

        self.transcribe_prompt = f"""
            Transcribe this {self.source_language} audio.
            If it has Pali language, please transcribe the Pali part as well, but keep the Pali text in its original script without romanization.
            """
        
        self.transcribe_timestamp = f"""
            
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
        prompt = self.transcribe_prompt
        if self.timestamp_needed:
            prompt += self.transcribe_timestamp

        if os.getenv(config.SELECTED_TRANSCRIPTION_MODEL) == config.TranscriptionModelLookup["Gemini Flash"]:
            self.run_gemini_cloud(prompt)
        elif os.getenv(config.SELECTED_TRANSCRIPTION_MODEL) == config.TranscriptionModelLookup["OpenAI Whisper"]:
            self.run_whisper_cloud(prompt)
        else:
            self.run_local()

    @pyqtSlot()
    def run_gemini_cloud(self, prompt):
        logger.info("AudioTranscribeWorker started running.")

        self.progress_updated.emit("Uploading audio file...")
        uploaded_file = self.client.files.upload(file=self.audio_file_path)
        logger.info("Audio file uploaded successfully.")

        # Generate Output (e.g., Translation)
        # Save into the file immediately
        self.progress_updated.emit("Prompting the AI model for transcription...")
        response = self.client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=[
                prompt,
                uploaded_file
            ]
        )
        logger.info("Transcription completed successfully.")

        transcribed_text = getattr(response, "text", "")
        self.transcribe_complete.emit(transcribed_text)

    @pyqtSlot()
    def run_whisper_cloud(self, prompt):
        logger.info("AudioTranscribeWorker started running. Using OpenAI Whisper for transcription.")

        self.progress_updated.emit("Uploading audio file to OpenAI Whisper...")
        with open(self.audio_file_path, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model=config.OPENAI_WHISPER_MODEL,
                file=audio_file,
                response_format="srt",
                prompt=prompt,
            )

        logger.info("Transcription completed successfully.")

        transcribed_text = response if isinstance(response, str) else getattr(response, "text", str(response))
        self.transcribe_complete.emit(transcribed_text)

    @pyqtSlot()
    def run_local(self):
        logger.info("AudioTranscribeWorker started running in local mode.")

        cmd = [
            config.LOCAL_WHISPER_CLI_PATH,
            "-m", config.LOCAL_WHISPER_MODEL_PATH,
            "-f", self.audio_file_path,
            "-otxt",
            "-ml", "56"
        ]

        if (self.timestamp_needed == True):
            cmd.remove("-otxt")
            cmd.extend(
                ["-osrt", "-sow"]
            )

        # Hardcoded the language code for now
        if(self.source_language.lower() == "chinese"):
            language_code = "zh"
            cmd.extend(
                ["-l", language_code]
            )

        self.progress_updated.emit("LOCAL Whisper Cpp is running...")

        result = subprocess.run(
            cmd,
            capture_output=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"whisper.cpp exited with code {result.returncode}")

        # read the generated .srt file
        if self.timestamp_needed == True:
            srt_path = f"{self.audio_file_path}" + f".srt"
        else:
            srt_path = f"{self.audio_file_path}" + f".txt"

        if srt_path.exists():
            with open(srt_path, "r", encoding="utf-8") as f:
                transcribed_text = f.read()
                self.transcribe_complete.emit(transcribed_text)

