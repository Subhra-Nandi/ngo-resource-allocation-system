import os
import tempfile
from app.agents.client import client


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """
    Transcribes audio using OpenAI Whisper API via GitHub Models endpoint.
    No local model needed — sends audio to the API.
    """
    try:
        suffix = os.path.splitext(filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )

        os.unlink(tmp_path)
        return transcript.text.strip()

    except Exception as e:
        print(f"STT error: {e}")
        return ""