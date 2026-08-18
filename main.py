import sys
import logging
from pathlib import Path

from dotenv import load_dotenv
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication

from app_controller import AppController


def configure_logging():
    """Write launch diagnostics to a location that Finder-launched apps can use."""
    log_directory = Path.home() / "Library" / "Logs" / "AudioSubtitleTool"
    log_directory.mkdir(parents=True, exist_ok=True)
    log_file = log_directory / "AudioSubtitleStudio.log"
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        filemode='a',
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )
    return log_file


def log_uncaught_exception(exception_type, exception, traceback):
    logging.critical(
        "Uncaught exception",
        exc_info=(exception_type, exception, traceback),
    )


def main():
    log_file = configure_logging()
    sys.excepthook = log_uncaught_exception

    logging.info("Starting the Audio Transcription Editor application. Log: %s", log_file)
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
        return 1

    return app.exec()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        logging.exception("Application failed during startup")
        raise
