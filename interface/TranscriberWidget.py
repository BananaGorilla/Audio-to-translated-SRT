import os
from PyQt6.QtWidgets import QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QWidget, QLabel, QFileDialog, QComboBox, QCheckBox
from workers.AudioTranscribe import AudioTranscribeWorker
from PyQt6.QtCore import QThread
from pathlib import Path
import logging
from workers.SaveFileWorker import SaveFileWorker

# Create a logger for the MainWindow class
logger = logging.getLogger(__name__)

class TranscriberWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        # UI setup
        layout = QVBoxLayout(self)

        # Status label to show progress updates
        status_layout = QHBoxLayout()
        status_title = QLabel("Status: ")
        self.status_label = QLabel("Ready")
        
        status_layout.addWidget(status_title)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()  # Push the status to the left

        # UI layout for audio file path display
        self.audio_file_path = None
        
        self.filename_edit = QLineEdit()
        audio_file_path_layout = QHBoxLayout()
        file_browse_button = QPushButton("Browse")
        
        file_browse_button.clicked.connect(self.on_file_dialog_open_file)
        
        audio_file_path_layout.addWidget(QLabel("Audio File:"))
        audio_file_path_layout.addWidget(self.filename_edit)
        audio_file_path_layout.addWidget(file_browse_button)

        # Language selection layout
        transcription_setting_layout = QHBoxLayout()
        language_label = QLabel("Original Audio Language:")
        self.language_dropdown = QComboBox()
        self.language_dropdown.addItems(["English", "Chinese", "Thai", "Cantonese", "Bahasa Indonesia", "Malay"])
        self.selected_language = "English"
        self.language_dropdown.currentTextChanged.connect(self.on_language_changed)
        
        self.timestamp_checkbox = QCheckBox("Generate timestamp")
        self.timestamp_checkbox.setChecked(True)

        transcription_setting_layout.addWidget(language_label)
        transcription_setting_layout.addWidget(self.language_dropdown)
        transcription_setting_layout.addSpacing(30)
        transcription_setting_layout.addWidget(self.timestamp_checkbox)
        transcription_setting_layout.addStretch()

        # Transcribe button
        self.transcribe_button = QPushButton("Transcribe")
        self.transcribe_button.clicked.connect(self.on_transcribe)

        # Text edit for displaying and editing the SRT content
        self.text_edit = QTextEdit()

        # Save button
        self.save_button = QPushButton("Save as...")
        self.save_button.clicked.connect(self.save_output_file)

        layout.addLayout(status_layout)
        layout.addLayout(audio_file_path_layout)
        layout.addLayout(transcription_setting_layout)
        layout.addWidget(self.transcribe_button)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.save_button)

        logger.info("TranscriberWidget initialized successfully.")

    def save_output_file(self):
        logger.info("Saving changes to file.")
        content = self.text_edit.toPlainText()
        SaveFile = SaveFileWorker(content = content)
        SaveFile.save_file()
        self.status_label.setText("File saved successfully!")
        logger.info(f"Saved changes to file successfully")

    def on_transcribe(self):
        logger.info("Transcription process started.")
        print(f"{self.timestamp_checkbox.isChecked()}")
        # Spawn worker
        self.transcribe_worker = AudioTranscribeWorker(audio_file_path=self.audio_file_path, source_language=self.selected_language, timestamp_needed=self.timestamp_checkbox.isChecked())
        self.transcribe_thread = QThread()

        self.transcribe_worker.moveToThread(self.transcribe_thread)

        # Connect signals
        self.transcribe_thread.started.connect(self.transcribe_worker.run)
        self.transcribe_worker.progress_updated.connect(self.on_transcribe_update_label)

        self.transcribe_worker.transcribe_complete.connect(self.on_transcribe_done)
        self.transcribe_worker.transcribe_complete.connect(self.transcribe_worker.deleteLater)
        self.transcribe_worker.transcribe_complete.connect(self.transcribe_thread.deleteLater)

        self.transcribe_thread.start()
        self.transcribe_button.setEnabled(False)
        self.transcribe_thread.finished.connect(lambda: self.transcribe_button.setEnabled(True))
    
    def on_transcribe_done(self, text):
        self.text_edit.setText(text)
        self.status_label.setText("Transcription complete")
        self.transcribe_thread.quit()

    def on_file_dialog_open_file(self):
        filename, ok = QFileDialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.mp3 *.wav)")
        if filename:
            self.audio_file_path = Path(filename)
            self.filename_edit.setText(str(self.audio_file_path))

    def on_transcribe_update_label(self, text):
        self.status_label.setText(text)

    def on_language_changed(self, language):
        self.selected_language = language
        logger.info(f"Selected language changed to: {language}")