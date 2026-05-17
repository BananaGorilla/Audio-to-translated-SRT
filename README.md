# Thai translate to English
This python script calls Google Gemini APIs to:
1. Transcribe the audio to SRT format (Currently only support English)
2. Translate the English SRT file into Chinese

## Pre-requisites
1. As this project tests with Google Gemini API, currently please make sure you have the API key and include it locally with file name `GOOGLE_GENAI_API_KEY.txt`.
2. Install FFMPEG in your local computer
3. Python 3.11 or above

## (Outdated - Please ignore for now)
### How to run it?
1. Copy the target youtube link
2. Call this command in your terminal `python main.py -y <youtube_link>`

### Script flow
1. It downloads the youtube video's audio file
2. Segment the audio files with certain timeout (default 5 mins)
3. Upload the audio file through the API and send prompt to translate
4. Print the response into an output file

## To do list
1. Change the AI calling API to general so we can experiment with different AI model esp local LLM