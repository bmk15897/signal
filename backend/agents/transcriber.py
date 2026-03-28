"""
transcriber.py — Whisper API transcription node
Converts audio bytes to text. If email, passes text through directly.
"""

import os
import io
from typing import Literal, Optional
from pydantic import BaseModel
import railtracks as rt
from openai import OpenAI

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


class TranscribeInput(BaseModel):
    type: Literal["audio", "email"] = "email"
    content: str  # base64-encoded bytes for audio, raw text for email
    filename: Optional[str] = "audio.mp3"


class TranscribeOutput(BaseModel):
    text: str
    type: str


@rt.function_node
async def transcribe(input: TranscribeInput) -> TranscribeOutput:
    """
    Transcribe audio or pass through email text.
    For audio, content should be a base64-encoded string of the audio bytes.
    For email, content is the raw email body text.
    """
    if input.type == "audio":
        import base64
        client = _get_client()
        audio_bytes = base64.b64decode(input.content)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = input.filename or "audio.mp3"

        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )
        text = response.text
    else:
        text = input.content

    return TranscribeOutput(text=text, type=input.type)


def transcribe_audio_bytes(audio_bytes: bytes, filename: str = "audio.mp3") -> str:
    """Helper to transcribe raw audio bytes directly (bypasses Railtracks node)."""
    client = _get_client()
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename
    response = _get_client().audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
    )
    return response.text
