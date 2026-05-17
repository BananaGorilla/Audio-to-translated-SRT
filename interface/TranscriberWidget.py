import os
from PyQt6.QtWidgets import QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QWidget, QLabel, QFileDialog
from workers.AudioTranscribe import AudioTranscribeWorker
from PyQt6.QtCore import QThread
from pathlib import Path
import logging

# Create a logger for the MainWindow class
logger = logging.getLogger(__name__)

class TranscriberWidget(QWidget):
    def __init__(self, parent=None, transcribed_file_path="./output_transcribe.srt"):
        super().__init__(parent)
        self.transcribed_file_path = transcribed_file_path
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
        layout.addLayout(status_layout)

        # UI layout for audio file path display
        self.audio_file_path = None
        
        self.filename_edit = QLineEdit()
        audio_file_path_layout = QHBoxLayout()
        file_browse_button = QPushButton("Browse")
        
        file_browse_button.clicked.connect(self.on_file_dialog_open_file)
        
        audio_file_path_layout.addWidget(QLabel("Audio File:"))
        audio_file_path_layout.addWidget(self.filename_edit)
        audio_file_path_layout.addWidget(file_browse_button)
        layout.addLayout(audio_file_path_layout)

        # Transcribe button
        self.transcribe_button = QPushButton("Transcribe")
        self.transcribe_button.clicked.connect(self.on_transcribe)
        
        layout.addWidget(self.transcribe_button)

        # Text edit for displaying and editing the SRT content
        self.text_edit = QTextEdit()
        
        layout.addWidget(self.text_edit)

        # Save button
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_output_file)
        
        layout.addWidget(self.save_button)

        logger.info("TranscriberWidget initialized successfully.")

    def load_output_file(self):
        logger.info(f"Loading transcribed file: {self.transcribed_file_path}")
        if os.path.exists(self.transcribed_file_path):
            with open(self.transcribed_file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.text_edit.setText(content)
                logger.info(f"Loaded transcribed file successfully")
        else:
            self.text_edit.setText("File not found. Please check the path.")
            logger.warning(f"Loaded transcribed file failed")

    def save_output_file(self):
        logger.info("Saving changes to file.")
        content = self.text_edit.toPlainText()
        with open(self.transcribed_file_path, "w", encoding="utf-8") as f:
            f.write(content)
        self.status_label.setText("File saved successfully!")
        logger.info(f"Saved changes to file successfully")

    def on_transcribe(self):
        logger.info("Transcription process started.")
        # Spawn worker
        self.transcribe_worker = AudioTranscribeWorker(audio_file_path=self.audio_file_path, output_file_name=f"output_transcribe.srt")
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
    
    def on_transcribe_done(self):
        self.load_output_file()
        self.transcribe_thread.quit()

    def on_file_dialog_open_file(self):
        filename, ok = QFileDialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.mp3 *.wav)")
        if filename:
            self.audio_file_path = Path(filename)
            self.filename_edit.setText(str(self.audio_file_path))

    def on_transcribe_update_label(self, text):
        self.status_label.setText(text)