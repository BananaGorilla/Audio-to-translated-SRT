from pydub import AudioSegment
import math
import os

class AudioSegmenter:
    def __init__(self, output_folder="segmented_audio"):
        """
        Initializes the segmenter with a target output directory.
        """
        self.output_folder = output_folder
        self._ensure_dir()

    def _ensure_dir(self):
        """Private helper to create the directory if it doesn't exist."""
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            print(f"[Info] Created directory: {self.output_folder}")

    def split_fixed(self, file_path, interval_seconds=30):
        """
        Splits an audio file into fixed intervals and saves them to the output folder.
        """
        # Convert seconds to milliseconds for pydub
        interval_ms = interval_seconds * 1000
        
        # Load audio and get base filename without extension
        audio = AudioSegment.from_file(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        total_ms = len(audio)
        num_segments = math.ceil(total_ms / interval_ms)
        
        print(f"[Processing] '{file_path}' -> {num_segments} segments.")

        for i in range(num_segments):
            start = i * interval_ms
            end = min((i + 1) * interval_ms, total_ms)
            
            segment = audio[start:end]
            
            # Construct the filename: e.g., "song_part_1.mp3"
            file_name = f"{base_name}_part_{i+1}.mp3"
            export_path = os.path.join(self.output_folder, file_name)
            
            segment.export(export_path, format="mp3")
            print(f"  > Exported: {file_name}")

        print("[Done] All segments saved successfully.\n")

    def clear_segments(self):
        """Remove all files inside the segment output folder.

        Only files are removed; subdirectories are left untouched. Prints a summary
        of how many files were removed and any warnings for failures.
        """
        if not os.path.isdir(self.output_folder):
            print(f"[Info] No segmented folder found: {self.output_folder}")
            return

        removed = 0
        for name in os.listdir(self.output_folder):
            path = os.path.join(self.output_folder, name)
            if os.path.isfile(path):
                try:
                    os.remove(path)
                    removed += 1
                except Exception as e:
                    print(f"[Warning] Could not remove {path}: {e}")

        print(f"[Info] Removed {removed} files from: {self.output_folder}")