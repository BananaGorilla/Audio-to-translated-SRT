from PyQt6.QtWidgets import QMainWindow, QTabWidget
import logging
from interface.TranscriberWidget import TranscriberWidget
from interface.TranslatorWidget import TranslatorWidget
from interface.SettingsWidget import SettingsTab
from dotenv import load_dotenv

# Create a logger for the MainWindow class
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("Initialize main class");
        self.setWindowTitle("Audio subtitle editor")
        load_dotenv()
        self._build_ui()

    def _build_ui(self):
        # Create tab container to hold different sections of the application
        self.tabs = QTabWidget()
        
        # Create the Transcriber tab and add it to the tab widget
        self.tabs.addTab(TranscriberWidget(), "Transcriber")
        self.tabs.addTab(TranslatorWidget(), "Translator")
        self.tabs.addTab(SettingsTab(), "Settings")

        self.setCentralWidget(self.tabs)