"""Split numbered SRT cues into translation requests."""

import re


_TIMESTAMP_RE = re.compile(
    r"^\s*\d{1,3}:\d{2}:\d{2}(?:[,.]\d{1,3})?\s*--?>\s*"
    r"\d{1,3}:\d{2}:\d{2}(?:[,.]\d{1,3})?"
)


def translation_batches(content: str, max_cues: int = 300):
    """Yield batches of up to ``max_cues`` complete numbered subtitles."""
    if max_cues < 1:
        raise ValueError("max_cues must be positive")

    lines = content.splitlines(keepends=True)
    cue_starts = [
        index
        for index in range(len(lines) - 1)
        if lines[index].strip().lstrip("\ufeff").isdigit()
        and _TIMESTAMP_RE.match(lines[index + 1])
    ]

    if not cue_starts:
        if content:
            yield content
        return

    for offset in range(0, len(cue_starts), max_cues):
        start = 0 if offset == 0 else cue_starts[offset]
        end = (
            cue_starts[offset + max_cues]
            if offset + max_cues < len(cue_starts)
            else len(lines)
        )
        yield "".join(lines[start:end])
