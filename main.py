import sys
import logging
from pathlib import Path

from dotenv import load_dotenv
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication

from app_controller import AppController

if __name__ == "__main__":
    logging.basicConfig(
        filename='Audio_transcribe_app.log', 
        level=logging.INFO,
        filemode='a')

    logging.info("Starting the Audio Transcription Editor application.")
    load_dotenv(Path(__file__).resolve().parent / ".env")

    app = QApplication(sys.argv)
    app.setApplicationName("Audio Subtitle Studio")
    app.setOrganizationName("AudioSubtitleTool")
    QQuickStyle.setStyle("Fusion")

    engine = QQmlApplicationEngine()
    controller = AppController(app)
    engine.rootContext().setContextProperty("appController", controller)

    resource_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    qml_file = resource_root / "ui" / "Main.qml"
    engine.load(qml_file)
    if not engine.rootObjects():
        logging.error("Failed to load the Qt Quick interface from %s", qml_file)
        sys.exit(1)

    sys.exit(app.exec())
