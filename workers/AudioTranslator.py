from PySide6.QtCore import QObject, Signal, Slot
from workers.common_tools import create_ai_client
from prompt.loader import load_translation_prompt, messages_to_local_prompt
import config
import logging
from litellm import completion
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class AudioTranslatorWorker(QObject):
    # Signals that UI listens to
    translation_complete = Signal(str)
    progress_updated = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        input_file_name=None,
        source_language="English",
        target_language="Simplified Chinese",
        input_content=None,
    ):
        super().__init__()

        self.client = create_ai_client(config.AIClientUsage.TRANSLATION.value)
        # Error handling for missing AI API key
        if not self.client:
            logger.error("No AI client available.")
            self.progress_updated.emit("No AI client available")
            raise ValueError("No AI client available.")
        
        if input_content is not None:
            srt_content = input_content
            self.input_file_name = input_file_name
        elif input_file_name:
            self.input_file_name = input_file_name
            with open(self.input_file_name, "r", encoding="utf-8") as f:
                srt_content = f.read()
        else:
            logger.error("Input file name is required for translation.")
            self.progress_updated.emit("No input file name provided")
            raise ValueError("Choose a subtitle file or enter subtitle text first.")

        if not srt_content.strip():
            raise ValueError("There is no subtitle text to translate.")

        self.messages = load_translation_prompt(
            source_language=source_language,
            target_language=target_language,
            srt_content=srt_content,
        )

    @Slot()
    def run(self):
        try:
            if os.getenv(config.SELECTED_TRANSLATION_MODEL) == config.TranslationModelLookup["Local Translator"]:
                translation_result = self.run_local()
            else:
                translation_result = self.run_cloud()

            self.translation_complete.emit(translation_result)
        except Exception as error:
            logger.exception("Translation failed")
            self.failed.emit(str(error))

    @Slot()
    def run_local(self) -> str:
        model_path = os.getenv(config.LOCAL_LLM_GGUF_FILE_PATH, "").strip()
        if not model_path:
            raise ValueError("Configure a local GGUF model path first.")
        if not Path(model_path).is_file():
            raise ValueError("The local translator model path does not point to a file.")

        from llama_cpp import Llama

        llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1,
            n_ctx=4096
        )
        translation_result = llm(
            messages_to_local_prompt(self.messages),
            max_tokens=4096,
        )
        return translation_result["choices"][0]["text"]

    @Slot()
    def run_cloud(self) -> str:
        self.progress_updated.emit("Prompting the AI model for translation...")
        response = completion(
            model=os.getenv(config.SELECTED_TRANSLATION_MODEL),
            messages=self.messages,
        )
        return response.choices[0].message.content
