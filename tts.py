import os

import httpx


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def synthesize(text: str, output_path: str) -> str:
    api_key = _required_env("ELEVENLABS_API_KEY")
    voice_id = _required_env("ELEVENLABS_VOICE_ID")
    endpoint = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    # Verify request/response shape against current ElevenLabs docs.
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

    with open(output_path, "wb") as output_file:
        output_file.write(response.content)
    return output_path