from pathlib import Path
from yt_dlp import YoutubeDL

class AudioDownloader:
    """Simple YouTube audio downloader using yt-dlp.

    Features:
    - Download single video audio and extract to `audio_format` (default mp3).
    - Download multiple URLs from a text file (one URL per line).
    - Basic progress output and error handling.
    """

    def __init__(self, output_dir="downloads", audio_format="mp3", audio_quality="192"):
        self.output_dir = Path(output_dir)
        self.audio_format = audio_format
        self.audio_quality = audio_quality
        self._last_video_title = None
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _progress_hook(self, d):
        status = d.get('status')
        if status == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                pct = downloaded / float(total) * 100
                print(f"Downloading: {pct:6.2f}% ({downloaded}/{total})", end='\r')
            else:
                print(f"Downloading: {downloaded} bytes", end='\r')
        elif status == 'finished':
            print("\nDownload complete — processing audio...")

    def _build_opts(self, filename=None):
        if filename:
            outtmpl = str(self.output_dir / filename)
        else:
            # Default to a fixed filename so the downloaded audio is named
            # `download.<ext>` (after postprocessing it will become `download.mp3`)
            outtmpl = str(self.output_dir / 'download.%(ext)s')

        opts = {
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'noplaylist': True,
            'quiet': False,
            'no_warnings': True,
            'progress_hooks': [self._progress_hook],
            'cachedir': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.audio_format,
                'preferredquality': str(self.audio_quality),
            }],
        }
        return opts

    def download(self, url, filename=None):
        """Download and extract audio from a single URL.

        Args:
            url (str): Video URL or playlist URL (playlists are disabled by default).
            filename (str|None): Optional output filename template (e.g. 'myfile.%(ext)s').
        Returns:
            int: yt-dlp return code (0 on success).
        """
        opts = self._build_opts(filename)
        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info and isinstance(info, dict):
                    # store title for later retrieval
                    self._last_video_title = info.get('title') or info.get('alt_title')
                return 0
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return 1

    def download_from_file(self, list_file_path):
        """Read a file of URLs (one per line) and download them sequentially.

        Lines starting with '#' are ignored.
        """
        p = Path(list_file_path)
        if not p.exists():
            raise FileNotFoundError(f"URL list file not found: {list_file_path}")

        with p.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                print(f"\nStarting: {line}")
                self.download(line)

    def remove_download(self, filename='download.mp3'):
        """Remove the downloaded file (default: 'download.mp3') from the output directory.

        Returns True if the file was removed, False if it didn't exist or removal failed.
        """
        target = self.output_dir / filename
        if not target.exists():
            print(f"[Info] No file to remove: {target}")
            return False
        try:
            target.unlink()
            print(f"[Info] Removed file: {target}")
            return True
        except Exception as e:
            print(f"[Warning] Could not remove {target}: {e}")
            return False

    def get_last_video_title(self):
        """Return the last downloaded video's title (or None if not set)."""
        return self._last_video_title.encode('utf-8', 'ignore').decode('utf-8') if self._last_video_title else None
