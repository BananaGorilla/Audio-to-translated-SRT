"""Load and render packaged Markdown prompts."""

from importlib.resources import files
from string import Template


_SYSTEM_MARKER = "<!-- role: system -->"
_USER_MARKER = "<!-- role: user -->"
_TRANSCRIPTION_MARKER = "<!-- prompt: transcription -->"
_TRANSCRIPTION_TIMESTAMP_MARKER = "<!-- prompt: timestamps -->"


def _read_prompt(name: str) -> str:
    return files("prompt").joinpath(
        f"templates/{name}.md"
    ).read_text(encoding="utf-8")


def load_translation_prompt(
    source_language: str,
    target_language: str,
    srt_content: str,
) -> list[dict[str, str]]:
    """Return the translation prompt as provider-neutral chat messages."""
    markdown = _read_prompt("translation")

    if _SYSTEM_MARKER not in markdown or _USER_MARKER not in markdown:
        raise ValueError(
            "The translation prompt must contain system and user role markers."
        )

    system_section, user_section = markdown.split(_USER_MARKER, maxsplit=1)
    system_prompt = system_section.split(_SYSTEM_MARKER, maxsplit=1)[1].strip()
    user_prompt = user_section.strip()

    variables = {
        "source_language": source_language,
        "target_language": target_language,
        "srt_content": srt_content,
    }

    return [
        {
            "role": "system",
            "content": Template(system_prompt).substitute(variables),
        },
        {
            "role": "user",
            "content": Template(user_prompt).substitute(variables),
        },
    ]


def messages_to_local_prompt(messages: list[dict[str, str]]) -> str:
    """Convert chat messages to a readable single prompt for local LLMs."""
    return "\n\n".join(
        f"<{message['role']}>\n{message['content']}\n</{message['role']}>"
        for message in messages
    )


def load_transcription_prompt(
    source_language: str,
    timestamp_needed: bool,
) -> str:
    """Render the transcription prompt for Gemini or OpenAI Whisper."""
    markdown = _read_prompt("transcription")

    if _TRANSCRIPTION_MARKER not in markdown:
        raise ValueError(
            "The transcription prompt must contain a transcription marker."
        )

    prompt_sections = markdown.split(_TRANSCRIPTION_MARKER, maxsplit=1)[1]
    if _TRANSCRIPTION_TIMESTAMP_MARKER in prompt_sections:
        base_prompt, timestamp_prompt = prompt_sections.split(
            _TRANSCRIPTION_TIMESTAMP_MARKER,
            maxsplit=1,
        )
    else:
        base_prompt = prompt_sections
        timestamp_prompt = ""

    variables = {"source_language": source_language}
    rendered_prompt = Template(base_prompt.strip()).substitute(variables)

    if timestamp_needed:
        rendered_prompt += "\n\n" + Template(
            timestamp_prompt.strip()
        ).substitute(variables)

    return rendered_prompt
