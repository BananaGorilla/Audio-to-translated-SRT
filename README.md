# Thai translate to English
This python script calls Google Gemini APIs to translate the Thai to English.

## Pre-requisites
1. As this project tests with Google Gemini API, currently please make sure you have the API key and include it locally with file name `GOOGLE_GENAI_API_KEY.txt`.
2. Install FFMPEG in your local computer
3. Python 3.11 or above

## How to run it?
1. Copy the target youtube link
2. Call this command in your terminal `python main.py -y <youtube_link>`

## Script flow
1. It downloads the youtube video's audio file
2. Segment the audio files with certain timeout (default 5 mins)
3. Upload the audio file through the API and send prompt to translate
4. Print the response into an output file

## To do list
1. Change the architecture not download, but stream the audio and translate at the same time
2. Create GUI
3. Include timestamp into the translated text
