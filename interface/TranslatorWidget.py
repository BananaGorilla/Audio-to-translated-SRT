from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QFileDialog
from PyQt6.QtCore import QThread
import logging
from workers.AudioTranslator import AudioTranslatorWorker

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
        self.filename_path.setReadOnly(True)  # Make the file path display read-only

        file_browse_button = QPushButton("Browse")
        file_browse_button.clicked.connect(self.on_file_browse)

        file_browse_layer.addWidget(file_browse_title)
        file_browse_layer.addWidget(self.filename_path)
        file_browse_layer.addWidget(file_browse_button)

        # Start translation layer
        start_translation_button_layer = QHBoxLayout()
        self.start_translation_button = QPushButton("Start translation")
        self.start_translation_button.clicked.connect(self.on_translation) # to be done

        start_translation_button_layer.addWidget(self.start_translation_button)

        # Edit layer to show the translated SRT file
        edit_layer = QHBoxLayout()
        self.original_language_edit_panel = QTextEdit()
        self.translated_edit_panel = QTextEdit()

        edit_layer.addWidget(self.original_language_edit_panel)
        edit_layer.addWidget(self.translated_edit_panel)

        # Save file layer
        save_file_layer = QHBoxLayout()
        # save_file_title = QLabel("Save as:")
        # save_file_path = QLineEdit()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_output_file)

        # save_file_layer.addWidget(save_file_title)
        # save_file_layer.addWidget(save_file_path)
        save_file_layer.addWidget(save_button)

        layout.addLayout(file_browse_layer)
        layout.addLayout(start_translation_button_layer)
        layout.addLayout(edit_layer)
        layout.addLayout(save_file_layer)

        logger.info("TranslatorWidget initialized succesfully")

    def on_file_browse(self):
        logger.info("File browse button clicked.")
        # Implement file browsing logic here (e.g., using QFileDialog)
        # After selecting a file, set the file path to self.filename_path
        filepath, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Transcribed SRT File",              # Dialog title
            "",                                         # Initial directory              
            "SRT Files (*.srt);;All Files (*)"
        )

        if filepath:
            self.filename_path.setText(filepath)
    
        self._load_transcribed_file()

    def _load_transcribed_file(self):
        logger.info("Open transcribed file dialog triggered.")

        try:
            with open(self.filename_path.text(), "r", encoding="utf-8") as f:
                content = f.read()
                self.original_language_edit_panel.setPlainText(content)
                logger.info(f"Transcribed file loaded successfully from {self.filename_path.text()}.")
        except Exception as e:
            logger.error(f"Failed to load transcribed file: {e}")

    def on_translation(self):
        logger.info("Start translation button clicked.")
        self.translated_edit_panel.setPlainText("Translating... Please wait.")
        # Implement translation logic here (e.g., calling the translation worker)
        self.translation_worker = AudioTranslatorWorker(
            input_file_name=self.filename_path.text(),
        )
        self.translation_thread = QThread()

        self.translation_worker.moveToThread(self.translation_thread)

        self.translation_thread.started.connect(self.translation_worker.run)
        self.translation_worker.progress_updated.connect(self.on_translation_update_label)

        self.translation_worker.translation_complete.connect(self.on_translation_complete)
        self.translation_worker.translation_complete.connect(self.translation_worker.deleteLater)
        self.translation_worker.translation_complete.connect(self.translation_thread.deleteLater)

        self.translation_thread.start()
        self.start_translation_button.setEnabled(False)
        self.translation_thread.finished.connect(lambda: self.start_translation_button.setEnabled(True))

    def on_translation_complete(self, translation_result):
        logger.info(f"Translation completed.")
        # Load the translated content into the translated_edit_panel
        self.translated_edit_panel.setPlainText(translation_result)
        
        self.translation_thread.quit()

    def on_translation_update_label(self, message):
        logger.info(f"Translation progress update: {message}")
        # Update the UI with the progress message (e.g., using a QLabel or status bar)
        self.translated_edit_panel.setPlainText(message)

    def save_output_file(self):
        logger.info("Saving changes to file.")
        content = self.translated_edit_panel.toPlainText()
        with open("translated_output.srt", "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Saved changes to file successfully")
