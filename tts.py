import os
import uuid
from pathlib import Path

import httpx


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _safe_output_path() -> Path:
    output_dir = Path(__file__).with_name("generated")
    output_dir.mkdir(exist_ok=True)
    return output_dir / f"reply_{uuid.uuid4().hex}.mp3"


def synthesize(text: str, output_path: str) -> str:
    api_key = _required_env("ELEVENLABS_API_KEY")
    voice_id = _required_env("ELEVENLABS_VOICE_ID")
    endpoint = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    with httpx.Client(timeout=60.0) as client:
        response = client.post(endpoint, headers=headers, json=payload)

    if response.status_code != 200:
        raise RuntimeError(
            f"ElevenLabs TTS failed with status {response.status_code}: {response.text}"
        )

    _ = output_path
    safe_output_path = _safe_output_path()
    with open(safe_output_path, "wb") as output_file:
        output_file.write(response.content)
    return str(safe_output_path)
