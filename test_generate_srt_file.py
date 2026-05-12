import sys
from PySide6.QtWidgets import QApplication
from MainWindow import MainWindow

import logging

if __name__ == "__main__":
    logging.basicConfig(
        filename='Audio_transcribe_app.log', 
        level=logging.INFO,
        filemode='a')

    logging.info("Starting the Audio Transcription Editor application.")
    app = QApplication(sys.argv)
    windows = MainWindow()  # Load the transcribed SRT file for editing
    windows.show()
    sys.exit(app.exec())

