---
name: audio-transcription
version: 1.0.0
---

<!-- prompt: transcription -->

Transcribe this $source_language audio.

1. If Pali is spoken, transcribe the Pali in its original script without
romanization.
2. Filter out the filler words.
3. If the pronounciation of the word is similar to "Bud-to", transcribe it to "Buddho".

<!-- prompt: timestamps -->

Return ONLY valid SRT format with timestamps.

Keep each subtitle block to 10 words maximum.

Example format:

```srt
1
00:00:00,000 --> 00:00:05,200
Transcribe sentence here.
```

Do not repeat the same end timestamp as the next start timestamp. If they are
the same, add 1 millisecond to the next start timestamp.

