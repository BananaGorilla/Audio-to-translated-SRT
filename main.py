import os
import argparse
import config
from workers.AudioSegmenter import AudioSegmenter
from workers.AudioTranslator import AudioTranslator
from workers.AudioDownloader import AudioDownloader

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Translate audio from file or YouTube link")
    parser.add_argument("--youtube-link", "-y", help="YouTube video URL to download audio from")
    args = parser.parse_args()

    # Download audio from YouTube if a link was provided
    if args.youtube_link:
        audio_downloader = AudioDownloader(output_dir='downloads', audio_format='mp3')
        audio_downloader.download(args.youtube_link)

    if args.youtube_link:
        audio_src = 'downloads/download.mp3'  # default name for downloaded audio
    else:
        audio_src = 'downloads/default_audio.mp3'  # fallback to default audio for testing

    # audio_segmenter = AudioSegmenter()
    # audio_translator = AudioTranslator(output_file_name=None)

    # audio_segmenter.split_fixed(file_path=audio_src, interval_seconds=config.DEFAULT_INTERVAL)

    # segmented_audio_files = [f for f in os.listdir("segmented_audio") if f.lower().endswith(config.AUDIO_EXTENSIONS)]

    # for segmented_audio in sorted(segmented_audio_files):
    #     print(f"\n--- Processing {segmented_audio} ---")
    #     audio_translator.process_long_audio(file_path=os.path.join("segmented_audio", segmented_audio))
    
    # # Clear segmented audio files after processing
    # audio_segmenter.clear_segments()
    # # Clear the download file after processing
    # if args.youtube_link:
    #     audio_downloader.remove_download()
