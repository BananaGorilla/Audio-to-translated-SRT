"""Transcript values shared by the worker and the editor (no UI dependencies)."""

from dataclasses import dataclass, field
import re
from uuid import uuid4


@dataclass
class TranscribedWord:
    text: str
    start: float | None
    end: float | None
    separator_before: str = " "
    word_id: str = field(default_factory=lambda: uuid4().hex)


@dataclass
class StartTimeTranscribeSentence:
    start_time: float
    text: str
    end_time: float | None = None
    words: list[TranscribedWord] = field(default_factory=list)
    row_id: str = field(default_factory=lambda: uuid4().hex)


def compile_whisper_rows(words, segments, pause_seconds=1):
    """Align timed words to punctuated segment text, then group by pauses.

    Keep original separators even across row boundaries: moving a Chinese word
    must not introduce a space, while moving an English word usually needs one.
    """
    source = " ".join(segment.text.strip() for segment in segments)
    trailing_punctuation = re.compile(r"""[,.!?;:，。！？；：、…"'”’)\]}]*""")
    rows = []
    row_words = []
    cursor = 0

    for index, word in enumerate(words):
        match = re.compile(re.escape(word.word.strip()), re.IGNORECASE).search(source, cursor)
        if match is None:
            raise ValueError(f"Cannot align word: {word.word!r}")
        end = trailing_punctuation.match(source, match.end()).end()
        gap = source[cursor:match.start()]
        # Leading quotation marks belong to the following word.
        separator = gap[:len(gap) - len(gap.lstrip())]
        prefix = gap[len(separator):]
        token_text = prefix + source[match.start():end]
        if index == len(words) - 1:
            token_text += source[end:]
        row_words.append(TranscribedWord(
            text=token_text, start=float(word.start), end=float(word.end),
            separator_before=separator,
        ))
        cursor = end
        next_word = words[index + 1] if index + 1 < len(words) else None
        if next_word is None or next_word.start - word.end >= pause_seconds:
            text = "".join(token.separator_before + token.text for token in row_words).strip()
            rows.append(StartTimeTranscribeSentence(
                start_time=row_words[0].start, end_time=row_words[-1].end,
                text=text, words=row_words,
            ))
            row_words = []
    return rows
