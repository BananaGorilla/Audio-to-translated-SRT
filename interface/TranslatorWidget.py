from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel
from PySide6.QtCore import QThread
import logging

# Create logger for the TranslationWidget class
logger = logging.getLogger(__name__)

class TranslatorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize the UI components for the translation widget
        self._build_ui()

    def _build_ui(self):
        # UI setup for the translation widget
        layout = QVBoxLayout(self)

        # Original transcription file browse layer
        file_browse_layer = QHBoxLayout()
        file_browse_title = QLabel("Transcribed File:")
        self.filename_path = QLineEdit()
        file_browse_button = QPushButton("Browse")
        # file_browse_button.clicked.connect(self.open_transcribed_file) # to be done

        file_browse_layer.addWidget(file_browse_title)
        file_browse_layer.addWidget(self.filename_path)
        file_browse_layer.addWidget(file_browse_button)

        # Start translation layer
        start_translation_button_layer = QHBoxLayout()
        start_translation_button = QPushButton("Start translation")
        # start_translation_button.clicked.connect(self.on_translation) # to be done

        start_translation_button_layer.addWidget(start_translation_button)

        # Edit layer to show the translated SRT file
        edit_layer = QHBoxLayout()
        self.original_language_edit_panel = QTextEdit()
        self.translated_edit_panel = QTextEdit()

        edit_layer.addWidget(self.original_language_edit_panel)
        edit_layer.addWidget(self.translated_edit_panel)

        # Save file layer
        save_file_layer = QHBoxLayout()
        save_file_title = QLabel("Save as:")
        save_file_path = QLineEdit()
        save_button = QPushButton("Save")

        save_file_layer.addWidget(save_file_title)
        save_file_layer.addWidget(save_file_path)
        save_file_layer.addWidget(save_button)

        layout.addLayout(file_browse_layer)
        layout.addLayout(start_translation_button_layer)
        layout.addLayout(edit_layer)
        layout.addLayout(save_file_layer)

        logger.info("TranslatorWidget initialized succesfully")
