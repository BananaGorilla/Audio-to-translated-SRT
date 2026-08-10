import logging
import os
from pathlib import Path
import shutil
import sys
from urllib.parse import urlparse

from PySide6.QtCore import QObject, Signal, Slot


logger = logging.getLogger(__name__)

# Qt Multimedia on some systems (including macOS devices without AV1 hardware
# decoding) cannot render AV1/VP9 even when those streams are inside an MP4.
# Prefer an H.264 MP4 + AAC combination so saved videos also work in Preview.
_PREVIEW_COMPATIBLE_VIDEO_FORMAT = (
    "bv[vcodec^=avc1][ext=mp4]+ba[ext=m4a]/"
    "b[vcodec^=avc1][ext=mp4]/"
    "bv[vcodec^=h264]+ba[ext=m4a]/"
    "bv[vcodec^=h264]+ba/"
    "b[vcodec^=h264][ext=mp4]"
)


def find_ffmpeg_location():
    """Return an FFmpeg executable directory that yt-dlp can use."""
    configured_path = os.getenv("FFMPEG_BINARY", "").strip()
    candidates = []
    if configured_path:
        candidates.append(Path(configured_path).expanduser())

    bundled_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    candidates.extend(
        [
            bundled_root / "bin" / "ffmpeg",
            bundled_root / "bin" / "ffmpeg.exe",
            Path("/opt/homebrew/bin/ffmpeg"),
            Path("/usr/local/bin/ffmpeg"),
            Path("/usr/bin/ffmpeg"),
        ]
    )

    path_executable = shutil.which("ffmpeg")
    if path_executable:
        candidates.insert(0, Path(path_executable))

    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate.parent)
    return None


class MediaDownloadWorker(QObject):
    progress_updated = Signal(int, str)
    download_complete = Signal(str, str)
    failed = Signal(str)

    def __init__(self, video_url, output_directory, audio_format, keep_video=True):
        super().__init__()
        self.video_url = video_url.strip()
        self.output_directory = Path(output_directory).expanduser()
        self.audio_format = audio_format.lower()
        self.keep_video = keep_video

    @Slot()
    def run(self):
        try:
            self._run_download()
        except Exception as error:
            logger.exception("Video download or audio extraction failed")
            self.failed.emit(self._friendly_error(error))

    def _run_download(self):
        parsed_url = urlparse(self.video_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError("Enter a valid http:// or https:// video URL.")
        if self.audio_format not in {"mp3", "wav", "m4a"}:
            raise ValueError(f"Unsupported audio format: {self.audio_format}")

        ffmpeg_location = find_ffmpeg_location()
        if not ffmpeg_location:
            raise RuntimeError(
                "FFmpeg was not found. Install FFmpeg or set FFMPEG_BINARY to its executable path."
            )

        try:
            import yt_dlp
        except ImportError as error:
            raise RuntimeError(
                "yt-dlp is not installed. Run: python -m pip install yt-dlp"
            ) from error

        self.output_directory.mkdir(parents=True, exist_ok=True)
        output_template = str(
            self.output_directory / "%(title).180B [%(id)s].%(ext)s"
        )
        options = {
            # Audio-only jobs should never download a video stream. yt-dlp will
            # remove the source audio container after FFmpeg creates the target
            # format unless keepvideo was explicitly requested.
            "format": (
                _PREVIEW_COMPATIBLE_VIDEO_FORMAT
                if self.keep_video
                else "bestaudio/best"
            ),
            "outtmpl": output_template,
            "noplaylist": True,
            "keepvideo": self.keep_video,
            "ffmpeg_location": ffmpeg_location,
            "merge_output_format": "mp4",
            "progress_hooks": [self._progress_hook],
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": self.audio_format,
                    "preferredquality": "192" if self.audio_format == "mp3" else "0",
                }
            ],
            "quiet": True,
            "noprogress": True,
            "no_warnings": True,
        }

        self.progress_updated.emit(0, "Reading video information…")
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(self.video_url, download=True)
            original_path = Path(downloader.prepare_filename(info))

        audio_path = original_path.with_suffix(f".{self.audio_format}")
        video_path = self._find_video_path(info, original_path) if self.keep_video else None
        if not audio_path.exists():
            raise RuntimeError("The download finished, but the extracted audio file was not found.")

        self.progress_updated.emit(100, "Download and audio extraction complete")
        self.download_complete.emit(
            str(video_path) if video_path and video_path.exists() else "",
            str(audio_path),
        )

    def _progress_hook(self, progress):
        status = progress.get("status")
        if status == "downloading":
            downloaded = progress.get("downloaded_bytes") or 0
            total = progress.get("total_bytes") or progress.get("total_bytes_estimate") or 0
            percent = int(downloaded * 100 / total) if total else 0
            speed = progress.get("_speed_str", "").strip()
            eta = progress.get("_eta_str", "").strip()
            detail = f"Downloading… {percent}%"
            if speed:
                detail += f" at {speed}"
            if eta:
                detail += f" · ETA {eta}"
            self.progress_updated.emit(percent, detail)
        elif status == "finished":
            self.progress_updated.emit(100, "Download complete — extracting audio…")

    @staticmethod
    def _find_video_path(info, original_path):
        candidates = [original_path]
        requested_downloads = info.get("requested_downloads") or []
        candidates.extend(
            Path(item["filepath"])
            for item in requested_downloads
            if item.get("filepath")
        )
        candidates.append(original_path.with_suffix(".mp4"))
        for candidate in candidates:
            if candidate.exists() and candidate.suffix.lower() not in {".mp3", ".wav", ".m4a"}:
                return candidate
        return None

    @staticmethod
    def _friendly_error(error):
        message = str(error).strip() or error.__class__.__name__
        lowered = message.lower()
        if "unsupported url" in lowered:
            return "This site or URL is not supported by yt-dlp."
        if "requested format is not available" in lowered and "format" in lowered:
            return (
                "This video has no H.264 version compatible with the Preview player. "
                "Try downloading audio only."
            )
        if "ffmpeg" in lowered and "not found" in lowered:
            return message
        return message
