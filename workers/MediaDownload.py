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
            # YouTube's media URLs are short-lived.  Retrying a transient
            # connection failure here is safe and avoids failing an otherwise
            # valid download after the stream has started.
            "retries": 3,
            "fragment_retries": 3,
            "file_access_retries": 3,
            "socket_timeout": 30,
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

        # Some video CDNs reject Python's default TLS fingerprint with a 403.
        # Browser impersonation is optional: yt-dlp only exposes it when its
        # installed curl_cffi version is compatible.  Do not force "chrome"
        # merely because curl_cffi imports successfully; newer incompatible
        # releases otherwise make every download fail before it starts.
        try:
            from yt_dlp.networking.impersonate import ImpersonateTarget

            chrome_target = ImpersonateTarget("chrome")
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as probe:
                chrome_available = probe._impersonate_target_available(
                    chrome_target
                )
        except Exception as error:
            logger.debug("Could not check yt-dlp impersonation support: %s", error)
            chrome_available = False
        if chrome_available:
            # This yt-dlp release validates the option before normalizing
            # strings, so it must receive an ImpersonateTarget instance.
            options["impersonate"] = chrome_target

        # An opt-in Netscape cookie file lets users download videos that
        # require their signed-in YouTube session without the app reading a
        # browser profile or credentials itself.
        cookie_file = os.getenv("YTDLP_COOKIEFILE", "").strip()
        if cookie_file:
            cookie_path = Path(cookie_file).expanduser()
            if not cookie_path.is_file():
                raise RuntimeError(
                    "YTDLP_COOKIEFILE points to a file that does not exist: "
                    f"{cookie_path}"
                )
            options["cookiefile"] = str(cookie_path)

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
        if "http error 403" in lowered:
            return (
                "YouTube refused the media request (HTTP 403). Update the app's "
                "yt-dlp dependencies and try again without a VPN or proxy. If the "
                "video needs an account, set YTDLP_COOKIEFILE to an exported "
                "Netscape-format cookie file from the same browser and network."
            )
        return message
