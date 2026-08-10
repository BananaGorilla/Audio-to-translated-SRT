from bisect import bisect_right
import logging
import os
from pathlib import Path
import re

from dotenv import set_key
from PySide6.QtCore import QObject, Property, QSettings, QThread, QUrl, Signal, Slot
from PySide6.QtWidgets import QFileDialog

import config


logger = logging.getLogger(__name__)

_SRT_TIMESTAMP_RE = re.compile(
    r"^\s*(\d{1,3}):([0-5]\d):([0-5]\d)[,.](\d{1,3})\s*-->\s*"
    r"(\d{1,3}):([0-5]\d):([0-5]\d)[,.](\d{1,3})"
)


class AppController(QObject):
    audioFilePathChanged = Signal()
    subtitleFilePathChanged = Signal()
    originalTextChanged = Signal()
    transcribedTextChanged = Signal()
    translatedTextChanged = Signal()
    transcriptionStatusChanged = Signal()
    translationStatusChanged = Signal()
    transcriptionBusyChanged = Signal()
    translationBusyChanged = Signal()
    selectedTranscriptionModelChanged = Signal()
    selectedTranslationModelChanged = Signal()
    previewAudioFilePathChanged = Signal()
    previewSubtitleFilePathChanged = Signal()
    previewStatusChanged = Signal()
    settingsStatusChanged = Signal()
    downloadFolderPathChanged = Signal()
    mediaDownloadStatusChanged = Signal()
    mediaDownloadBusyChanged = Signal()
    mediaDownloadProgressChanged = Signal()
    mediaDownloadOutputChanged = Signal()
    notificationRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = QSettings("AudioSubtitleTool", "AudioSubtitleTool")
        self._audio_file_path = ""
        self._subtitle_file_path = ""
        self._original_text = ""
        self._transcribed_text = ""
        self._translated_text = ""
        self._transcription_status = "Ready"
        self._translation_status = "Ready"
        self._transcription_busy = False
        self._translation_busy = False
        self._selected_transcription_model = os.getenv(
            config.SELECTED_TRANSCRIPTION_MODEL,
            config.TranscriptionModelLookup["Gemini Flash"],
        )
        self._selected_translation_model = os.getenv(
            config.SELECTED_TRANSLATION_MODEL,
            config.TranslationModelLookup["Gemini Flash"],
        )
        self._preview_audio_file_path = ""
        self._preview_subtitle_file_path = ""
        self._preview_subtitle_cues = []
        self._preview_subtitle_starts = []
        self._preview_status = "Choose an audio file and an SRT file"
        self._settings_status = ""
        default_download_folder = Path.home() / "Downloads"
        self._download_folder_path = str(
            self._settings.value("media_download_folder", str(default_download_folder))
        )
        self._media_download_status = "Ready"
        self._media_download_busy = False
        self._media_download_progress = 0
        self._media_download_output = ""

        self._transcription_thread = None
        self._transcription_worker = None
        self._translation_thread = None
        self._translation_worker = None
        self._media_download_thread = None
        self._media_download_worker = None

        self._env_path = Path(__file__).resolve().parent / ".env"

    @Property("QVariantList", constant=True)
    def transcriptionModels(self):
        return [
            {"label": label, "value": value}
            for label, value in config.TranscriptionModelLookup.items()
        ]

    @Property("QVariantList", constant=True)
    def translationModels(self):
        return [
            {"label": label, "value": value}
            for label, value in config.TranslationModelLookup.items()
        ]

    @Property(str, notify=selectedTranscriptionModelChanged)
    def selectedTranscriptionModel(self):
        return self._selected_transcription_model

    @Property(str, notify=selectedTranslationModelChanged)
    def selectedTranslationModel(self):
        return self._selected_translation_model

    @Property(str, notify=selectedTranscriptionModelChanged)
    def selectedTranscriptionModelLabel(self):
        return self._model_label(
            config.TranscriptionModelLookup,
            self._selected_transcription_model,
        )

    @Property(str, notify=selectedTranslationModelChanged)
    def selectedTranslationModelLabel(self):
        return self._model_label(
            config.TranslationModelLookup,
            self._selected_translation_model,
        )

    @Property(str, notify=previewAudioFilePathChanged)
    def previewAudioFilePath(self):
        return self._preview_audio_file_path

    @Property(str, notify=previewAudioFilePathChanged)
    def previewAudioUrl(self):
        if not self._preview_audio_file_path:
            return ""
        return QUrl.fromLocalFile(self._preview_audio_file_path).toString()

    @Property(str, notify=previewSubtitleFilePathChanged)
    def previewSubtitleFilePath(self):
        return self._preview_subtitle_file_path

    @Property(int, notify=previewSubtitleFilePathChanged)
    def previewSubtitleCount(self):
        return len(self._preview_subtitle_cues)

    @Property(str, notify=previewStatusChanged)
    def previewStatus(self):
        return self._preview_status

    @Property(str, constant=True)
    def transcriptionApiKey(self):
        return str(self._settings.value("transcription_api_key", ""))

    @Property(str, constant=True)
    def translationApiKey(self):
        return str(self._settings.value("translation_api_key", ""))

    @Property(str, notify=audioFilePathChanged)
    def audioFilePath(self):
        return self._audio_file_path

    @Property(str, notify=subtitleFilePathChanged)
    def subtitleFilePath(self):
        return self._subtitle_file_path

    @Property(str, notify=originalTextChanged)
    def originalText(self):
        return self._original_text

    @Property(str, notify=transcribedTextChanged)
    def transcribedText(self):
        return self._transcribed_text

    @Property(str, notify=translatedTextChanged)
    def translatedText(self):
        return self._translated_text

    @Property(str, notify=transcriptionStatusChanged)
    def transcriptionStatus(self):
        return self._transcription_status

    @Property(str, notify=translationStatusChanged)
    def translationStatus(self):
        return self._translation_status

    @Property(bool, notify=transcriptionBusyChanged)
    def transcriptionBusy(self):
        return self._transcription_busy

    @Property(bool, notify=translationBusyChanged)
    def translationBusy(self):
        return self._translation_busy

    @Property(str, notify=settingsStatusChanged)
    def settingsStatus(self):
        return self._settings_status

    @Property(str, notify=downloadFolderPathChanged)
    def downloadFolderPath(self):
        return self._download_folder_path

    @Property(str, notify=mediaDownloadStatusChanged)
    def mediaDownloadStatus(self):
        return self._media_download_status

    @Property(bool, notify=mediaDownloadBusyChanged)
    def mediaDownloadBusy(self):
        return self._media_download_busy

    @Property(int, notify=mediaDownloadProgressChanged)
    def mediaDownloadProgress(self):
        return self._media_download_progress

    @Property(str, notify=mediaDownloadOutputChanged)
    def mediaDownloadOutput(self):
        return self._media_download_output

    def _set_value(self, attribute, value, signal):
        if getattr(self, attribute) == value:
            return
        setattr(self, attribute, value)
        signal.emit()

    @Slot()
    def chooseAudioFile(self):
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select audio file",
            "",
            "Audio Files (*.mp3 *.wav *.m4a *.flac *.aac *.ogg);;All Files (*)",
        )
        if file_path:
            self._set_value("_audio_file_path", file_path, self.audioFilePathChanged)
            self._set_value("_transcription_status", "Audio ready", self.transcriptionStatusChanged)

    @Slot()
    def chooseSubtitleFile(self):
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select subtitle or text file",
            "",
            "Subtitle Files (*.srt);;Text Files (*.txt);;All Files (*)",
        )
        if not file_path:
            return

        try:
            content = Path(file_path).read_text(encoding="utf-8")
        except Exception as error:
            logger.exception("Failed to open subtitle file")
            self._set_value("_translation_status", f"Could not open file: {error}", self.translationStatusChanged)
            return

        self._set_value("_subtitle_file_path", file_path, self.subtitleFilePathChanged)
        self._set_value("_original_text", content, self.originalTextChanged)
        self._set_value("_translation_status", "Subtitle ready", self.translationStatusChanged)

    @Slot()
    def choosePreviewAudioFile(self):
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select audio file for subtitle preview",
            "",
            "Audio Files (*.mp3 *.wav *.m4a *.flac *.aac *.ogg)",
        )
        if not file_path:
            return
        if Path(file_path).suffix.lower() not in config.AUDIO_EXTENSIONS:
            status = "Unsupported file — choose MP3, WAV, M4A, FLAC, AAC, or OGG audio"
            self._set_value("_preview_status", status, self.previewStatusChanged)
            self.notificationRequested.emit(status)
            return

        self._set_value(
            "_preview_audio_file_path",
            file_path,
            self.previewAudioFilePathChanged,
        )
        status = "Ready to play" if self._preview_subtitle_cues else "Audio loaded — choose an SRT file"
        self._set_value("_preview_status", status, self.previewStatusChanged)

    @Slot()
    def choosePreviewSubtitleFile(self):
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select SRT file for subtitle preview",
            "",
            "SRT Subtitle Files (*.srt);;All Files (*)",
        )
        if not file_path:
            return

        try:
            content = Path(file_path).read_text(encoding="utf-8-sig")
            cues = self._parse_srt(content)
        except Exception as error:
            logger.exception("Failed to open preview subtitle file")
            self._set_value(
                "_preview_status",
                f"Could not open SRT file: {error}",
                self.previewStatusChanged,
            )
            return

        self._preview_subtitle_cues = cues
        self._preview_subtitle_starts = [cue[0] for cue in cues]
        if self._preview_subtitle_file_path == file_path:
            self.previewSubtitleFilePathChanged.emit()
        else:
            self._set_value(
                "_preview_subtitle_file_path",
                file_path,
                self.previewSubtitleFilePathChanged,
            )
        if cues:
            status = f"Ready — {len(cues)} subtitle cues loaded"
        else:
            status = "No valid subtitle cues found in this SRT file"
        self._set_value("_preview_status", status, self.previewStatusChanged)
        self.notificationRequested.emit(status)

    @Slot()
    def chooseDownloadFolder(self):
        folder_path = QFileDialog.getExistingDirectory(
            None,
            "Choose download folder",
            self._download_folder_path,
        )
        if not folder_path:
            return
        self._settings.setValue("media_download_folder", folder_path)
        self._set_value(
            "_download_folder_path",
            folder_path,
            self.downloadFolderPathChanged,
        )

    @Slot(str, str, bool)
    def startMediaDownload(self, video_url, audio_format, keep_video):
        if self._media_download_busy:
            return
        if not video_url.strip():
            self._set_value(
                "_media_download_status",
                "Enter a video URL first",
                self.mediaDownloadStatusChanged,
            )
            return

        try:
            from workers.MediaDownload import MediaDownloadWorker

            worker = MediaDownloadWorker(
                video_url=video_url,
                output_directory=self._download_folder_path,
                audio_format=audio_format,
                keep_video=keep_video,
            )
        except Exception as error:
            self._set_value(
                "_media_download_status",
                str(error),
                self.mediaDownloadStatusChanged,
            )
            return

        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress_updated.connect(self._onMediaDownloadProgress)
        worker.download_complete.connect(self._onMediaDownloadComplete)
        worker.failed.connect(self._onMediaDownloadFailed)
        worker.download_complete.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.download_complete.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._onMediaDownloadThreadFinished)

        self._media_download_worker = worker
        self._media_download_thread = thread
        self._set_value("_media_download_busy", True, self.mediaDownloadBusyChanged)
        self._set_value("_media_download_progress", 0, self.mediaDownloadProgressChanged)
        self._set_value("_media_download_output", "", self.mediaDownloadOutputChanged)
        self._set_value(
            "_media_download_status",
            "Starting download…",
            self.mediaDownloadStatusChanged,
        )
        thread.start()

    @Slot(int, str)
    def _onMediaDownloadProgress(self, percent, message):
        self._set_value(
            "_media_download_progress",
            max(0, min(100, percent)),
            self.mediaDownloadProgressChanged,
        )
        self._set_value(
            "_media_download_status",
            message,
            self.mediaDownloadStatusChanged,
        )

    @Slot(str, str)
    def _onMediaDownloadComplete(self, video_path, audio_path):
        outputs = [path for path in (video_path, audio_path) if path]
        output_text = "\n".join(outputs)
        self._set_value(
            "_media_download_output",
            output_text,
            self.mediaDownloadOutputChanged,
        )
        self._set_value(
            "_media_download_status",
            "Download and audio extraction complete",
            self.mediaDownloadStatusChanged,
        )
        self.notificationRequested.emit(f"Saved {Path(audio_path).name}")

    @Slot(str)
    def _onMediaDownloadFailed(self, message):
        self._set_value(
            "_media_download_status",
            f"Download failed: {message}",
            self.mediaDownloadStatusChanged,
        )
        self.notificationRequested.emit("Download failed")

    @Slot()
    def _onMediaDownloadThreadFinished(self):
        self._set_value("_media_download_busy", False, self.mediaDownloadBusyChanged)
        self._media_download_worker = None
        self._media_download_thread = None

    @Slot(int, result=str)
    def previewSubtitleAt(self, position_ms):
        if not self._preview_subtitle_starts:
            return ""

        cue_index = bisect_right(self._preview_subtitle_starts, position_ms) - 1
        if cue_index < 0:
            return ""
        start_ms, end_ms, text = self._preview_subtitle_cues[cue_index]
        if start_ms <= position_ms <= end_ms:
            return text
        return ""

    @Slot(str, bool)
    def startTranscription(self, language, timestamp_needed):
        if self._transcription_busy:
            return
        if not self._audio_file_path:
            self._set_value("_transcription_status", "Choose an audio file first", self.transcriptionStatusChanged)
            return

        try:
            from workers.AudioTranscribe import AudioTranscribeWorker

            worker = AudioTranscribeWorker(
                audio_file_path=self._audio_file_path,
                source_language=language,
                timestamp_needed=timestamp_needed,
            )
        except Exception as error:
            self._set_value("_transcription_status", str(error), self.transcriptionStatusChanged)
            return

        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress_updated.connect(self._onTranscriptionProgress)
        worker.transcribe_complete.connect(self._onTranscriptionComplete)
        worker.failed.connect(self._onTranscriptionFailed)
        worker.transcribe_complete.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.transcribe_complete.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._onTranscriptionThreadFinished)

        self._transcription_worker = worker
        self._transcription_thread = thread
        self._set_value("_transcription_busy", True, self.transcriptionBusyChanged)
        self._set_value("_transcription_status", "Starting transcription…", self.transcriptionStatusChanged)
        thread.start()

    @Slot(str)
    def _onTranscriptionProgress(self, message):
        self._set_value("_transcription_status", message, self.transcriptionStatusChanged)

    @Slot(str)
    def _onTranscriptionComplete(self, text):
        self._set_value("_transcribed_text", text, self.transcribedTextChanged)
        self._set_value("_transcription_status", "Transcription complete", self.transcriptionStatusChanged)
        self.notificationRequested.emit("Transcription complete")

    @Slot(str)
    def _onTranscriptionFailed(self, message):
        self._set_value("_transcription_status", f"Transcription failed: {message}", self.transcriptionStatusChanged)
        self.notificationRequested.emit("Transcription failed")

    @Slot()
    def _onTranscriptionThreadFinished(self):
        self._set_value("_transcription_busy", False, self.transcriptionBusyChanged)
        self._transcription_worker = None
        self._transcription_thread = None

    @Slot(str, str, str)
    def startTranslation(self, source_language, target_language, source_text):
        if self._translation_busy:
            return
        if not source_text.strip():
            self._set_value(
                "_translation_status",
                "There is no subtitle text to translate.",
                self.translationStatusChanged,
            )
            return

        try:
            from workers.AudioTranslator import AudioTranslatorWorker

            worker = AudioTranslatorWorker(
                input_file_name=self._subtitle_file_path or None,
                input_content=source_text,
                source_language=source_language,
                target_language=target_language,
            )
        except Exception as error:
            self._set_value("_translation_status", str(error), self.translationStatusChanged)
            return

        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress_updated.connect(self._onTranslationProgress)
        worker.translation_complete.connect(self._onTranslationComplete)
        worker.failed.connect(self._onTranslationFailed)
        worker.translation_complete.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.translation_complete.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._onTranslationThreadFinished)

        self._translation_worker = worker
        self._translation_thread = thread
        self._set_value("_translation_busy", True, self.translationBusyChanged)
        self._set_value("_translation_status", "Starting translation…", self.translationStatusChanged)
        thread.start()

    @Slot(str)
    def _onTranslationProgress(self, message):
        self._set_value("_translation_status", message, self.translationStatusChanged)

    @Slot(str)
    def _onTranslationComplete(self, text):
        self._set_value("_translated_text", text, self.translatedTextChanged)
        self._set_value("_translation_status", "Translation complete", self.translationStatusChanged)
        self.notificationRequested.emit("Translation complete")

    @Slot(str)
    def _onTranslationFailed(self, message):
        self._set_value("_translation_status", f"Translation failed: {message}", self.translationStatusChanged)
        self.notificationRequested.emit("Translation failed")

    @Slot()
    def _onTranslationThreadFinished(self):
        self._set_value("_translation_busy", False, self.translationBusyChanged)
        self._translation_worker = None
        self._translation_thread = None

    def _save_text(self, title, suggested_name, content):
        file_path, _ = QFileDialog.getSaveFileName(
            None,
            title,
            suggested_name,
            "SRT Files (*.srt);;Text Files (*.txt);;All Files (*)",
        )
        if not file_path:
            return
        try:
            Path(file_path).write_text(content, encoding="utf-8")
            self.notificationRequested.emit(f"Saved {Path(file_path).name}")
        except Exception as error:
            logger.exception("Failed to save output")
            self.notificationRequested.emit(f"Save failed: {error}")

    @Slot(str)
    def saveTranscription(self, content):
        self._save_text("Save transcription", "transcription.srt", content)

    @Slot(str)
    def saveTranslation(self, content):
        self._save_text("Save translation", "translation.srt", content)

    @Slot(str, str, str, str)
    def saveSettings(
        self,
        transcription_model,
        transcription_api_key,
        translation_model,
        translation_api_key,
    ):
        try:
            self._env_path.touch(exist_ok=True)
            self._settings.setValue("transcription_api_key", transcription_api_key)
            self._settings.setValue("translation_api_key", translation_api_key)

            self._save_provider_setting(
                config.SELECTED_TRANSCRIPTION_MODEL,
                transcription_model,
                transcription_api_key,
            )
            self._save_provider_setting(
                config.SELECTED_TRANSLATION_MODEL,
                translation_model,
                translation_api_key,
            )
            self._set_value(
                "_selected_transcription_model",
                transcription_model,
                self.selectedTranscriptionModelChanged,
            )
            self._set_value(
                "_selected_translation_model",
                translation_model,
                self.selectedTranslationModelChanged,
            )
            self._set_value("_settings_status", "Settings saved", self.settingsStatusChanged)
            self.notificationRequested.emit("Settings saved")
        except Exception as error:
            logger.exception("Failed to save settings")
            self._set_value("_settings_status", f"Could not save settings: {error}", self.settingsStatusChanged)

    def _save_provider_setting(self, selected_key, model, api_key):
        provider = model.split("/", 1)[0] if model else ""
        provider_key = config.ModelProviderApiLookup.get(provider)
        if not provider_key:
            raise ValueError(f"Unsupported model provider: {provider or 'unknown'}")

        set_key(str(self._env_path), selected_key, model)
        set_key(str(self._env_path), provider_key, api_key)
        os.environ[selected_key] = model
        os.environ[provider_key] = api_key

    @staticmethod
    def _model_label(model_lookup, selected_model):
        for label, value in model_lookup.items():
            if value == selected_model:
                return label
        return selected_model or "Not selected"

    @staticmethod
    def _parse_srt(content):
        normalized_content = content.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not normalized_content:
            return []

        cues = []
        for block in re.split(r"\n\s*\n", normalized_content):
            lines = block.splitlines()
            timestamp_index = next(
                (index for index, line in enumerate(lines) if _SRT_TIMESTAMP_RE.match(line)),
                None,
            )
            if timestamp_index is None:
                continue

            match = _SRT_TIMESTAMP_RE.match(lines[timestamp_index])
            start_ms = AppController._srt_time_to_milliseconds(match.groups()[:4])
            end_ms = AppController._srt_time_to_milliseconds(match.groups()[4:])
            subtitle_text = "\n".join(lines[timestamp_index + 1:]).strip()
            if subtitle_text and end_ms >= start_ms:
                cues.append((start_ms, end_ms, subtitle_text))

        cues.sort(key=lambda cue: cue[0])
        return cues

    @staticmethod
    def _srt_time_to_milliseconds(time_parts):
        hours, minutes, seconds, milliseconds = time_parts
        milliseconds = int(milliseconds.ljust(3, "0")[:3])
        return (
            int(hours) * 3_600_000
            + int(minutes) * 60_000
            + int(seconds) * 1_000
            + milliseconds
        )
