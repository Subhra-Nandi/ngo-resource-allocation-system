import os
import tempfile
import whisper

# Load model once at module import — not on every request
# 'base' is fast and accurate enough for field reports
# Use 'small' for better accuracy if you have more RAM
_model = None


def _get_model():
    global _model
    if _model is None:
        print("Loading Whisper model... (first time only)")
        _model = whisper.load_model("base")
    return _model


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """
    Takes raw audio bytes, returns transcribed text.
    Whisper auto-detects language — works for Bengali, Hindi, English.
    """
    try:
        # Write to temp file — Whisper needs a file path
        suffix = os.path.splitext(filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        model = _get_model()
        result = model.transcribe(tmp_path, language=None)  # auto-detect language

        # Clean up temp file
        os.unlink(tmp_path)

        return result["text"].strip()

    except Exception as e:
        print(f"STT error: {e}")
        return ""