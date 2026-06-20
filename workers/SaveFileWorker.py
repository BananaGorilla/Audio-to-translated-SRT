import logging
from PyQt6.QtWidgets import QFileDialog, QWidget

logger = logging.getLogger(__name__)

FILE_FILTER = "Text Files (*.txt);;SRT Files (*.srt);;All Files (*)"

class SaveFileWorker():
    def __init__(self, content = ""):
        super().__init__()
        self.content_to_save = content
        
    def save_file(self):
        # 1. Open file system save pop-up
        file_path, selected_filter = QFileDialog.getSaveFileName(
            None,
            "Save as...",
            "",
            FILE_FILTER
        )

        # 2. Check if the user selected a location or cancelled pop-up
        if file_path:
            # Open the file and write the text to the selected path
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.content_to_save)
                    logger.info(f"Succesfully saved to: {file_path}")
            except Exception as error:
                logger.error(f"Failed to save file: {error}")
        else:
            logger.info("Save operation cancelled by user")

