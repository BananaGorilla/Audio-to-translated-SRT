"""Word-boundary editing independent of QML event handling.

All mutations pass through this model, including keyboard actions and drops.
Rows have stable IDs; stale drag events can never address a different row.
"""

from copy import deepcopy
from difflib import SequenceMatcher
import logging
import math
import re

from PySide6.QtCore import QAbstractListModel, QModelIndex, Property, Qt, Signal, Slot

from workers.TranscriptionDataclass import StartTimeTranscribeSentence, TranscribedWord


logger = logging.getLogger(__name__)


def format_timestamp(seconds):
    milliseconds = round(seconds * 1000)
    minutes, remainder = divmod(milliseconds, 60000)
    whole_seconds, fraction = divmod(remainder, 1000)
    stamp = f"{minutes}:{whole_seconds:02d}"
    return stamp + (f".{fraction:03d}".rstrip("0") if fraction else "")


class TranscriptEditorModel(QAbstractListModel):
    stateChanged = Signal()
    errorChanged = Signal()
    pendingChanged = Signal()
    timingRequested = Signal()

    _ROLES = {
        Qt.UserRole + 1: b"rowId",
        Qt.UserRole + 2: b"rowText",
        Qt.UserRole + 3: b"timestamp",
        Qt.UserRole + 4: b"startTime",
        Qt.UserRole + 5: b"endTime",
        Qt.UserRole + 6: b"wordTokens",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []
        self._undo = []
        self._redo = []
        self._error = ""
        self._pending = {}

    def roleNames(self):
        return self._ROLES

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        row = self._rows[index.row()]
        values = {
            b"rowId": row.row_id, b"rowText": row.text,
            b"timestamp": format_timestamp(row.start_time),
            b"startTime": row.start_time, b"endTime": row.end_time,
            b"wordTokens": [{"text": word.text,
                             "separator": word.separator_before if i else "",
                             "timingKnown": word.start is not None and word.end is not None}
                            for i, word in enumerate(row.words)],
        }
        return row.text if role == Qt.DisplayRole else values.get(self._ROLES.get(role))

    @Property(int, notify=stateChanged)
    def count(self):
        return len(self._rows)

    @Property(bool, notify=stateChanged)
    def canUndo(self):
        return bool(self._undo)

    @Property(bool, notify=stateChanged)
    def canRedo(self):
        return bool(self._redo)

    @Property(str, notify=stateChanged)
    def exportText(self):
        return "\n".join(f"[{format_timestamp(row.start_time)}] {row.text}"
                         for row in self._rows)

    @Property(str, notify=errorChanged)
    def errorMessage(self):
        return self._error

    @Property("QVariantMap", notify=pendingChanged)
    def pendingTiming(self):
        return self._pending

    def load(self, rows):
        """Install an owned copy of a worker result and start a fresh history."""
        self.beginResetModel()
        self._rows = deepcopy(rows)
        self._undo.clear()
        self._redo.clear()
        self.endResetModel()
        self.cancelTiming()
        self._set_error("")
        self.stateChanged.emit()

    def _find(self, row_id):
        return next((i for i, row in enumerate(self._rows) if row.row_id == row_id), -1)

    @Slot(str, result=str)
    def textForRow(self, row_id):
        index = self._find(row_id)
        return self._rows[index].text if index >= 0 else ""

    def _set_error(self, message):
        self._error = message
        self.errorChanged.emit()
        return False

    def _commit(self, rows):
        self._undo.append(deepcopy(self._rows))
        self._redo.clear()
        self._replace(rows)

    def _replace(self, rows):
        if [row.row_id for row in rows] == [row.row_id for row in self._rows]:
            self._rows = rows
            if rows:
                self.dataChanged.emit(self.index(0, 0), self.index(len(rows) - 1, 0), [])
        else:
            self.beginResetModel()
            self._rows = rows
            self.endResetModel()
        self.cancelTiming()
        self._set_error("")
        self.stateChanged.emit()

    @Slot()
    def undo(self):
        if self._undo:
            self._redo.append(deepcopy(self._rows))
            self._replace(self._undo.pop())

    @Slot()
    def redo(self):
        if self._redo:
            self._undo.append(deepcopy(self._rows))
            self._replace(self._redo.pop())

    @staticmethod
    def _text(words):
        return "".join((word.separator_before if i else "") + word.text
                       for i, word in enumerate(words)).strip()

    @staticmethod
    def _spans(words):
        offset = 0
        for i, word in enumerate(words):
            offset += len(word.separator_before) if i else 0
            yield offset, offset + len(word.text), word
            offset += len(word.text)

    @classmethod
    def _edited_words(cls, row, text):
        """Keep timing only for entire unchanged word spans, including repeats.

        A character diff preserves Whisper's own word segmentation for scripts
        without spaces. Newly typed spans have explicitly unknown timing.
        """
        blocks = SequenceMatcher(None, row.text, text, autojunk=False).get_matching_blocks()
        anchors = []
        for start, end, word in cls._spans(row.words):
            for block in blocks:
                if block.a <= start and end <= block.a + block.size:
                    new_start = block.b + start - block.a
                    anchors.append((new_start, new_start + len(word.text), word))
                    break

        pieces = []
        cursor = 0
        for start, end, word in anchors + [(len(text), len(text), None)]:
            for match in re.finditer(r"\S+", text[cursor:start]):
                pieces.append((cursor + match.start(), cursor + match.end(), None))
            if word is not None:
                pieces.append((start, end, word))
            cursor = end

        result = []
        cursor = 0
        for start, end, original in pieces:
            word = deepcopy(original) if original else TranscribedWord(text[start:end], None, None)
            if result:
                word.separator_before = text[cursor:start]
            else:
                word.separator_before = (original.separator_before if original
                                         else row.words[0].separator_before)
            result.append(word)
            cursor = end
        return result

    @Slot(str, str, result=bool)
    def updateText(self, row_id, text):
        index = self._find(row_id)
        if index < 0:
            return self._set_error("This transcript line no longer exists.")
        text = re.sub(r"[\r\n]+", " ", text).strip()
        if not text:
            return self._set_error("Keep at least one word, or move the remaining word to a neighbor.")
        if text == self._rows[index].text:
            return True
        rows = deepcopy(self._rows)
        row = rows[index]
        row.words = self._edited_words(row, text)
        row.text = text
        if row.words[0].start is not None:
            row.start_time = row.words[0].start
        if row.words[-1].end is not None:
            row.end_time = row.words[-1].end
        self._commit(rows)
        logger.debug("Edited transcript row %s", row_id)
        return True

    @Slot(str, str, str, result=bool)
    def canDrop(self, source_id, edge, target_id):
        source, target = self._find(source_id), self._find(target_id)
        if source < 0 or target < 0:
            return False
        if edge == "both" and len(self._rows[source].words) != 1:
            return False
        return ((edge in ("first", "both") and target == source - 1)
                or (edge in ("last", "both") and target == source + 1))

    def _partition(self, row, cut, action, seconds):
        """Partition at a word boundary, requesting explicit timing if needed."""
        left_words, right_words = row.words[:cut], row.words[cut:]
        left_end, right_start = left_words[-1].end, right_words[0].start
        if left_end is None or right_start is None:
            lower = max([row.start_time] + [word.end for word in left_words if word.end is not None])
            upper = min([row.end_time] + [word.start for word in right_words if word.start is not None])
            if lower > upper:
                self._set_error("These word timings overlap. Correct the text or undo the edit first.")
                return None
            if seconds is None:
                self._pending = dict(action, minimum=lower, maximum=upper)
                self.pendingChanged.emit()
                self.timingRequested.emit()
                return None
            if not math.isfinite(seconds) or not lower <= seconds <= upper:
                self._set_error(f"Enter a time between {format_timestamp(lower)} and {format_timestamp(upper)}.")
                return None
            if left_end is None:
                left_words[-1].end = seconds
                left_end = seconds
            if right_start is None:
                right_words[0].start = seconds
                right_start = seconds
        left = StartTimeTranscribeSentence(row.start_time, self._text(left_words),
                                          left_end, left_words, row.row_id)
        right = StartTimeTranscribeSentence(right_start, self._text(right_words),
                                           row.end_time, right_words)
        return left, right

    @Slot(str, str, str, result=bool)
    def moveBoundaryWord(self, source_id, edge, target_id):
        return self._move(source_id, edge, target_id)

    @Slot(str, result=bool)
    def moveFirstWordUp(self, source_id):
        index = self._find(source_id)
        if index <= 0:
            return self._set_error("There is no previous line.")
        return self._move(source_id, "first", self._rows[index - 1].row_id)

    @Slot(str, result=bool)
    def moveLastWordDown(self, source_id):
        index = self._find(source_id)
        if index < 0 or index >= len(self._rows) - 1:
            return self._set_error("There is no next line.")
        return self._move(source_id, "last", self._rows[index + 1].row_id)

    def _move(self, source_id, edge, target_id, seconds=None):
        if not self.canDrop(source_id, edge, target_id):
            return self._set_error("Move only the first word up or the last word down, to the neighboring line.")
        source_index, target_index = self._find(source_id), self._find(target_id)
        rows = deepcopy(self._rows)
        source, target = rows[source_index], rows[target_index]
        upward = target_index < source_index
        if len(source.words) == 1:
            moving = source
            remainder = None
        else:
            action = dict(kind="move", source=source_id, edge=edge, target=target_id)
            parts = self._partition(source, 1 if upward else len(source.words) - 1,
                                    action, seconds)
            if parts is None:
                return False
            moving, remainder = parts if upward else (parts[1], parts[0])
        if upward:
            target.words.extend(moving.words)
            target.end_time = moving.end_time
        else:
            target.words = moving.words + target.words
            target.start_time = moving.start_time
        target.text = self._text(target.words)
        if remainder is None:
            del rows[source_index]
        else:
            remainder.row_id = source_id
            rows[source_index] = remainder
        self._commit(rows)
        logger.debug("Moved %s word from %s to %s", edge, source_id, target_id)
        return True

    @Slot(str, int, result=bool)
    def splitRow(self, row_id, cursor_position):
        return self._split(row_id, cursor_position)

    @Slot(str, str, int, result=bool)
    def splitEditedRow(self, row_id, text, cursor_position):
        """Commit the draft and translate its cursor through whitespace cleanup."""
        encoded = text.encode("utf-16-le")
        if cursor_position < 0 or cursor_position * 2 > len(encoded):
            return self._set_error("Place the cursor between words inside the line.")
        prefix = encoded[:cursor_position * 2].decode("utf-16-le", errors="ignore")
        prefix = re.sub(r"[\r\n]+", " ", prefix).lstrip()
        position = len(prefix.encode("utf-16-le")) // 2
        return self.updateText(row_id, text) and self._split(row_id, position)

    def _split(self, row_id, cursor_position, seconds=None):
        index = self._find(row_id)
        if index < 0:
            return self._set_error("This transcript line no longer exists.")
        row = self._rows[index]
        # Qt cursor positions count UTF-16 code units, Python counts code points.
        encoded = row.text.encode("utf-16-le")
        if cursor_position < 0 or cursor_position * 2 > len(encoded):
            return self._set_error("Place the cursor between words inside the line.")
        offset = len(encoded[:cursor_position * 2].decode("utf-16-le", errors="ignore"))
        spans = list(self._spans(row.words))
        cut = next((i for i in range(1, len(spans))
                    if spans[i - 1][1] <= offset <= spans[i][0]), None)
        if cut is None:
            return self._set_error("Place the cursor between words inside the line.")
        rows = deepcopy(self._rows)
        parts = self._partition(rows[index], cut,
                                dict(kind="split", source=row_id, cursor=cursor_position), seconds)
        if parts is None:
            return False
        rows[index:index + 1] = parts
        self._commit(rows)
        logger.debug("Split transcript row %s", row_id)
        return True

    @Slot(str, result=bool)
    def resolveTiming(self, value):
        if not self._pending:
            return False
        try:
            fields = value.strip().split(":")
            if not 1 <= len(fields) <= 3:
                raise ValueError
            numbers = [float(part) for part in fields]
            if (any(not math.isfinite(number) or number < 0 for number in numbers)
                    or any(number >= 60 for number in numbers[1:])
                    or any(not number.is_integer() for number in numbers[:-1])):
                raise ValueError
            seconds = sum(number * 60 ** power for power, number in enumerate(reversed(numbers)))
        except ValueError:
            return self._set_error("Enter seconds or a timestamp such as 1:05.250.")
        action = self._pending.copy()
        if action["kind"] == "move":
            return self._move(action["source"], action["edge"], action["target"], seconds)
        return self._split(action["source"], action["cursor"], seconds)

    @Slot()
    def cancelTiming(self):
        self._pending = {}
        self.pendingChanged.emit()
