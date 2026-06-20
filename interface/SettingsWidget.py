# settings_tab.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton, QFormLayout, QComboBox
from PyQt6.QtCore import QSettings
from dotenv import set_key
import config
from pathlib import Path
import os
import config

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("MyApp", "AIToolbox")  # persists to OS settings store
        self.env_path = Path(__file__).resolve().parents[1] / ".env"
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Transcription provider settings
        transcription_provider_column = QVBoxLayout()
        transcription_provider_label = QLabel("Transcription Provider")
        transcription_provider_font = transcription_provider_label.font()
        transcription_provider_font.setPointSize(transcription_provider_font.pointSize() + 5)
        transcription_provider_font.setBold(True)
        transcription_provider_label.setFont(transcription_provider_font)

        transcription_content_row = QHBoxLayout()
        transcription_model_label = QLabel("Model")
        self.transcription_model_dropdown = QComboBox()
        for model_name, model_value in config.TranscriptionModelLookup.items():
            self.transcription_model_dropdown.addItem(model_name, model_value)

        saved_model = self.settings.value("transcription_selected_model", next(iter(config.TranscriptionModelLookup.values())))
        saved_model_index = self.transcription_model_dropdown.findData(saved_model)
        if saved_model_index >= 0:
            self.transcription_model_dropdown.setCurrentIndex(saved_model_index)

        transcription_content_row.addWidget(transcription_model_label)
        transcription_content_row.addWidget(self.transcription_model_dropdown)

        transcription_api_label = QLabel("API key")
        self.transcription_api_key = QLineEdit()
        self.transcription_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.transcription_api_key.setText(self.settings.value("transcription_api_key", ""))

        transcription_content_row.addWidget(transcription_api_label)
        transcription_content_row.addWidget(self.transcription_api_key)

        transcription_provider_column.addWidget(transcription_provider_label)
        transcription_provider_column.addLayout(transcription_content_row)

        # Translation provider settings would go here (similar structure to transcription provider)
        translation_provider_column = QVBoxLayout()
        translation_provider_label = QLabel("Translation Provider")
        translation_provider_font = translation_provider_label.font()
        translation_provider_font.setPointSize(translation_provider_font.pointSize() + 5)
        translation_provider_font.setBold(True)
        translation_provider_label.setFont(translation_provider_font)

        translation_content_row = QHBoxLayout()
        translation_model_label = QLabel("Model")
        self.translation_model_dropdown = QComboBox()
        for model_name, model_value in config.TranslationModelLookup.items():
            self.translation_model_dropdown.addItem(model_name, model_value)

        saved_model = self.settings.value("translation_selected_model", next(iter(config.TranslationModelLookup.values())))
        saved_model_index = self.translation_model_dropdown.findData(saved_model)
        if saved_model_index >= 0:
            self.translation_model_dropdown.setCurrentIndex(saved_model_index)

        translation_content_row.addWidget(translation_model_label)
        translation_content_row.addWidget(self.translation_model_dropdown)

        translation_api_label = QLabel("API key")
        self.translation_api_key = QLineEdit()
        self.translation_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.translation_api_key.setText(self.settings.value("translation_api_key", ""))

        translation_content_row.addWidget(translation_api_label)
        translation_content_row.addWidget(self.translation_api_key)

        translation_provider_column.addWidget(translation_provider_label)
        translation_provider_column.addLayout(translation_content_row)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)

        save_label_row = QHBoxLayout()
        save_title_label = QLabel("Status")
        self.save_status_label = QLabel("Not saved")
        save_label_row.addWidget(save_title_label)
        save_label_row.addWidget(self.save_status_label)
        save_label_row.addStretch()

        layout.addLayout(transcription_provider_column)
        layout.addLayout(translation_provider_column)
        layout.addWidget(save_btn)
        layout.addLayout(save_label_row)
        layout.addStretch()

    def save_settings(self):
        transcription_selected_model = self.transcription_model_dropdown.currentData()
        transcription_api_key = self.transcription_api_key.text()

        translation_selected_model = self.translation_model_dropdown.currentData()
        translation_api_key = self.translation_api_key.text()

        self.settings.setValue("transcription_selected_model", transcription_selected_model)
        self.settings.setValue("transcription_api_key", transcription_api_key)
        self.settings.setValue("translation_selected_model", translation_selected_model)
        self.settings.setValue("translation_api_key", translation_api_key)

        transcription_provider_name = transcription_selected_model.split("/", 1)[0] if transcription_selected_model else ""
        transcription_provider_env_key = config.ModelProviderApiLookup.get(transcription_provider_name)

        translation_provider_name = translation_selected_model.split("/", 1)[0] if translation_selected_model else ""
        translation_provider_env_key = config.ModelProviderApiLookup.get(translation_provider_name)

        if transcription_provider_env_key:
            self.env_path.touch(exist_ok=True)
            set_key(str(self.env_path), config.SELECTED_TRANSCRIPTION_MODEL, transcription_selected_model)  # Save the selected transcription model name
            set_key(str(self.env_path), transcription_provider_env_key, transcription_api_key)              # Save the transcription model API key
            os.environ[config.SELECTED_TRANSCRIPTION_MODEL] = transcription_selected_model
            os.environ[transcription_provider_env_key] = transcription_api_key
            print(f"{transcription_selected_model} selected for transcription. Saved {transcription_provider_env_key} to .env file and environment variables")
        
        if translation_provider_env_key:
            self.env_path.touch(exist_ok=True)
            set_key(str(self.env_path), config.SELECTED_TRANSLATION_MODEL, translation_selected_model)      # Save the selected translation model name
            set_key(str(self.env_path), translation_provider_env_key, translation_api_key)                  # Save the translation model API key
            os.environ[config.SELECTED_TRANSLATION_MODEL] = translation_selected_model
            os.environ[translation_provider_env_key] = translation_api_key
            print(f"{translation_selected_model} selected for translation. Saved {translation_provider_env_key} to .env file and environment variables.")

        if (transcription_provider_env_key and translation_provider_env_key):
            self.save_status_label.setText("Env set successfully")
        else:
            self.save_status_label.setText("Env set failed")
