import asyncio
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import memory
import pipeline
import stt


BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BASE_DIR / "generated"
STATIC_DIR = BASE_DIR / "static"


class MessageRequest(BaseModel):
    user_id: str
    text: str


def _to_public_response(result: dict) -> dict:
    audio_name = Path(result["reply_audio_path"]).name
    form_name = Path(result["form_html_path"]).name
    return {
        "reply_text": result["reply_text"],
        "reply_audio_url": f"/generated/{audio_name}",
        "form_html_url": f"/generated/{form_name}",
    }


load_dotenv()
app = FastAPI(title="Scheme Setu Demo API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    GENERATED_DIR.mkdir(exist_ok=True)
    await memory.init_db()


@app.post("/api/message")
async def message_api(payload: MessageRequest) -> dict:
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    result = await pipeline.run_turn(payload.user_id, payload.text)
    return _to_public_response(result)


@app.post("/api/voice")
async def voice_api(user_id: str, file: UploadFile = File(...)) -> dict:
    suffix = Path(file.filename or "voice.ogg").suffix or ".ogg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
        temp_audio.write(await file.read())
        temp_path = temp_audio.name

    try:
        transcript = stt.transcribe(temp_path)
        result = await pipeline.run_turn(user_id, transcript)
        return _to_public_response(result)
    finally:
        Path(temp_path).unlink(missing_ok=True)


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated")
