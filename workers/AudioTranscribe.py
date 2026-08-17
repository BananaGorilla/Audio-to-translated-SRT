from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot
import logging
from workers.common_tools import create_ai_client
import config
import subprocess
import os

logger = logging.getLogger(__name__)

OPENAI_WHISPER_AUDIO_SIZE = 25.00
LOWER_BITRATE_AUDIO_FILE_PATH = "./low_bitrate_audio.mp3"

class AudioTranscribeWorker(QObject):
    # Signals that UI listens to
    transcribe_complete = Signal(str)
    progress_updated = Signal(str)
    failed = Signal(str)

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
    
    @Slot()
    def run(self):
        try:
            prompt = self.transcribe_prompt
            if self.timestamp_needed:
                prompt += self.transcribe_timestamp

            selected_model = os.getenv(config.SELECTED_TRANSCRIPTION_MODEL)
            if selected_model == config.TranscriptionModelLookup["Gemini Flash"]:
                self.run_gemini_cloud(prompt)
            elif selected_model == config.TranscriptionModelLookup["OpenAI Whisper"]:
                self.run_whisper_cloud(prompt)
            elif selected_model == config.TranscriptionModelLookup["Local Whisper"]:
                self.run_local()
            else:
                raise ValueError("Select and save a transcription model in Settings first.")
        except Exception as error:
            logger.exception("Transcription failed")
            self.failed.emit(str(error))

    @Slot()
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

    @Slot()
    def run_whisper_cloud(self, prompt):
        logger.info("AudioTranscribeWorker started running. Using OpenAI Whisper for transcription.")

        self.progress_updated.emit("Uploading audio file to OpenAI Whisper...")

        upload_file = self.audio_file_path

        # Check if the file size is more than 25MB
        # Call ffmpeg to lower the bitrate to 32k
        audio_file_size = Path(self.audio_file_path).stat().st_size
        audio_file_size = audio_file_size / (1024 * 1024)

        if(audio_file_size > OPENAI_WHISPER_AUDIO_SIZE):
            logger.info("The audio file size is more than 25MB. It exceeds OpenAI Whisper file size limit.")

            subprocess.run([
                "ffmpeg",
                "-i", self.audio_file_path,
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "32k",
                LOWER_BITRATE_AUDIO_FILE_PATH
            ])

            upload_file = LOWER_BITRATE_AUDIO_FILE_PATH

            logger.info("Using ffmpeg to lower to 32k bitrate audio")

        with open(upload_file, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model=config.OPENAI_WHISPER_MODEL,
                file=audio_file,
                response_format="srt",
                prompt=prompt,
            )

        logger.info("Transcription completed successfully.")

        # Remove the lower bitrate file if any
        file_to_be_deleted = Path(LOWER_BITRATE_AUDIO_FILE_PATH)
        file_to_be_deleted.unlink(missing_ok=True)

        transcribed_text = response if isinstance(response, str) else getattr(response, "text", str(response))
        self.transcribe_complete.emit(transcribed_text)

    @Slot()
    def run_local(self):
        logger.info("AudioTranscribeWorker started running in local mode.")

        cli_path = os.getenv(config.LOCAL_WHISPER_CLI_PATH, "").strip()
        model_path = os.getenv(config.LOCAL_WHISPER_MODEL_PATH, "").strip()
        if not cli_path or not model_path:
            raise ValueError("Configure the local Whisper executable and model paths first.")

        if not Path(cli_path).is_file():
            raise ValueError("The local Whisper CLI path does not point to a file.")
        if not os.access(cli_path, os.X_OK):
            raise ValueError("The local Whisper CLI path is not executable.")
        if not Path(model_path).is_file():
            raise ValueError("The local Whisper model path does not point to a file.")

        cmd = [
            cli_path,
            "-m", model_path,
            "-f", self.audio_file_path,
            "-otxt",
            "-ml", "56"
        ]
        print(cmd)
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

        with open(srt_path, "r", encoding="utf-8") as f:
            transcribed_text = f.read()
            self.transcribe_complete.emit(transcribed_text)
