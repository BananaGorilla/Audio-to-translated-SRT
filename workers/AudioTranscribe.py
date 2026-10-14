from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot
import logging
import re
from workers.common_tools import create_ai_client
from workers.MediaDownload import find_ffmpeg_executable
from prompt.loader import load_transcription_prompt
import config
import subprocess
import os
import tempfile
from workers.TranscriptionDataclass import StartTimeTranscribeSentence

logger = logging.getLogger(__name__)

OPENAI_WHISPER_AUDIO_SIZE = 25.00
AUDIO_PAUSE_SECONDS = 1.5

class AudioTranscribeWorker(QObject):
    # Signals that UI listens to
    transcribe_complete = Signal(object)
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

        self.transcribe_prompt = load_transcription_prompt(
            source_language=self.source_language,
            timestamp_needed=self.timestamp_needed,
        )
    
    @Slot()
    def run(self):
        try:
            prompt = self.transcribe_prompt

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
        temporary_audio_path = None

        # Check if the file size is more than 25MB
        # Call ffmpeg to lower the bitrate to 32k
        audio_file_size = Path(self.audio_file_path).stat().st_size
        audio_file_size = audio_file_size / (1024 * 1024)

        try:
            if(audio_file_size > OPENAI_WHISPER_AUDIO_SIZE):
                logger.info("The audio file size is more than 25MB. It exceeds OpenAI Whisper file size limit.")

                ffmpeg_executable = find_ffmpeg_executable()
                if not ffmpeg_executable:
                    raise RuntimeError(
                        "FFmpeg was not found. Install FFmpeg or set FFMPEG_BINARY "
                        "to its executable path."
                    )

                # A packaged macOS app may start with a read-only working
                # directory (for example, when launched from a mounted DMG).
                # Always put generated audio in the OS-managed writable temp
                # directory instead of using a path relative to the process.
                with tempfile.NamedTemporaryFile(
                    prefix="audio_subtitle_studio_",
                    suffix=".mp3",
                    delete=False,
                ) as temporary_audio:
                    temporary_audio_path = Path(temporary_audio.name)

                try:
                    subprocess.run([
                        ffmpeg_executable,
                        "-y",
                        "-nostdin",
                        "-i", self.audio_file_path,
                        "-codec:a",
                        "libmp3lame",
                        "-b:a",
                        "32k",
                        str(temporary_audio_path),
                    ], check=True, capture_output=True, text=True)
                except subprocess.CalledProcessError as error:
                    details = (error.stderr or error.stdout or "").strip()
                    message = "FFmpeg could not reduce the audio file size."
                    if details:
                        message += f"\n\n{details}"
                    raise RuntimeError(message) from error

                upload_file = str(temporary_audio_path)

                logger.info("Using ffmpeg to lower to 32k bitrate audio")

            with open(upload_file, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=config.OPENAI_WHISPER_MODEL,
                    file=audio_file,
                    prompt=prompt,
                    response_format="verbose_json" if self.timestamp_needed else "text",
                    timestamp_granularities=["word", "segment"],
                    temperature=0,
                )
        finally:
            if temporary_audio_path is not None:
                temporary_audio_path.unlink(missing_ok=True)

        logger.info("Transcription completed successfully.")

        if(self.timestamp_needed):
            transcribed_items = []
            for sentence in self.compile_whisper_with_timestamp_and_start_time(
                words=response.words,
                segments=response.segments,
            ):
                transcribed_items.append(StartTimeTranscribeSentence(
                    start_time=sentence['start'],
                    text=sentence['text']
                ))

            transcribed_text = "\n".join(
                f"[{item.start_time:.2f}] {item.text}"
                for item in transcribed_items
            )
        else:
            transcribed_text = (response if isinstance(response, str) else getattr(response, "text", str(response)))

        print(transcribed_text)
        self.transcribe_complete.emit(transcribed_text)

    def compile_whisper_with_timestamp_and_start_time(
        self, words, segments, pause_seconds=AUDIO_PAUSE_SECONDS
    ):
        """Group words by pauses and retain punctuation from segment text.

        The words and segments must contain the same words in the same order.
        """
        source = " ".join(segment.text.strip() for segment in segments)
        sentences = []
        cursor = 0
        sentence_start = 0
        start_time = None
        trailing_punctuation = re.compile(r"""[,.!?;:，。！？；：、…"'”’)\]}]*""")

        for i, word in enumerate(words):
            match = re.compile(
                re.escape(word.word.strip()), re.IGNORECASE
            ).search(source, cursor)
            if match is None:
                raise ValueError(f"Cannot align word: {word.word!r}")

            if start_time is None:
                start_time = word.start

            cursor = trailing_punctuation.match(source, match.end()).end()

            next_word = words[i + 1] if i + 1 < len(words) else None
            long_pause = (
                next_word is not None
                and next_word.start - word.end >= pause_seconds
            )

            if long_pause or next_word is None:
                end = len(source) if next_word is None else cursor
                sentences.append({
                    "start": start_time,
                    "text": source[sentence_start:end].strip(),
                })
                sentence_start = end
                start_time = None

        return sentences

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
