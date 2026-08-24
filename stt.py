import mimetypes
import os

import httpx


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def transcribe(audio_file_path: str) -> str:
    base_url = _required_env("VOXTRAL_BASE_URL").rstrip("/")
    api_key = _required_env("VOXTRAL_API_KEY")

    endpoint = f"{base_url}/v1/audio/transcriptions"
    mime_type = mimetypes.guess_type(audio_file_path)[0] or "application/octet-stream"
    with open(audio_file_path, "rb") as audio_file:
        files = {"file": (os.path.basename(audio_file_path), audio_file, mime_type)}
        data = {"model": "voxtral"}
        headers = {"Authorization": f"******"}
        with httpx.Client(timeout=60.0) as client:
            response = client.post(endpoint, headers=headers, files=files, data=data)

    if response.status_code != 200:
        raise RuntimeError(
            f"Voxtral transcription failed with status {response.status_code}: {response.text}"
        )

    payload = response.json()
    transcript = payload.get("text") or payload.get("transcript")
    if not transcript:
        raise RuntimeError(f"Voxtral response missing transcript text: {payload}")
    return transcript
