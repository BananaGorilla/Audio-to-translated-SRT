# Offline-capable audio transcription & translation pipeline
This tool calls AI model from the cloud to transcribe and translate audio into `.srt` file that can insert in YouTube video.

This tool also allows you utilize local model: Whisper.cpp (transcription) and Llama.cpp (translation) for token-free usage.

# How to use it?
## Run via Python locally
Strongly encourage you to run this python script and play around with it! Nothing beats than you hands-on and try it out yourself.

It contains 2 main functions: Transcription and Translation. This tool calls the AI model in the cloud to do them. 

If you want to run this python code, make sure you have install python3.11 or above. Then run these lines in your command prompt (Windows) or terminal (macOS).
> python3 -m venv venv \
> python3 -m pip install -r requirements.txt \
> python3 main.py

After that, the Qt Quick desktop application will open.

## User interface
The desktop interface uses PySide6 and Qt Quick/QML. It provides guided
workspaces for transcription, subtitle translation, model settings, output
editing, and saving. Live translation and video voice-over are represented in
the workspace as planned workflows so they can be added without restructuring
the application navigation.

## Run via exec file
This software contains the `.spec` file which allows user to generate as software and run directly on computer without installing python.

To build the software,
> pyinstaller Transcription_And_Translation_Tool.spec

It will build the exec file and you can run it directly.

# Setting
This tab allows you to setup the AI model you want for each tasks. You may insert your API key there and save it for the task.

### Transcription models
Models that we support currently:
1. Google Gemini-2.5 Flash
2. OpenAI whisper-1 model
3. Local Whisper.cpp

We also support running whisper.cpp locally if your device supports. Please make sure you install whisper.cpp and download `large-v3-turbo.en` model. (Currently we do not support other local model yet).

### Translation models
Models that we support currently:
1. Google Gemini-2.5 Flash 
2. OpenAI GPT-4o
3. Antrophic Claude-Sonnet-4-20250514
4. Local Llama.cpp GGUF model

# Transcription
Upload your audio file (.wav or .mp3) and select the language of this audio clip. Then you can click the "Transcribe" button to start the transcription. 

The transcription will be shown in the text editor where you can check and edit the output. Once you have done, click "Save" to save the file and it will be in the same folder, named "output_transcribe.srt"

# Translation
Upload your `.srt` file and select the original language and target translation language. Click the "Translate" button and it will start the translation.

The output will be shown in the text editor. User can cross check and edit the output before save the file.
