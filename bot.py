import asyncio
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import form_fill
import memory
import mesh
import rag
import stt
import tts


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Namaste! Main Scheme Setu hoon — apna situation Hinglish voice note mein bhejo, main best scheme aur documents bataunga."
    )


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.voice or not update.effective_user:
        return

    user_id = update.effective_user.id
    with tempfile.TemporaryDirectory() as temp_dir:
        input_ogg = str(Path(temp_dir) / f"voice_{user_id}.ogg")
        output_mp3 = str(Path(temp_dir) / f"reply_{user_id}.mp3")
        form_png = str(Path(temp_dir) / f"form_{user_id}.png")

        try:
            voice_file = await update.message.voice.get_file()
            await voice_file.download_to_drive(input_ogg)

            transcript = stt.transcribe(input_ogg)
            prior_fields = await memory.get_last_fields(user_id)
            extracted_fields = mesh.extract_fields(transcript, prior_fields)

            matched_schemes = rag.find_best_match(extracted_fields)
            response_text = mesh.reason_eligibility(extracted_fields, matched_schemes)

            await memory.save_turn(user_id, transcript, extracted_fields, response_text)

            tts_path = tts.synthesize(response_text, output_mp3)
            await update.message.reply_text(response_text)
            with open(tts_path, "rb") as audio_file:
                await update.message.reply_voice(voice=audio_file)

            best_scheme = matched_schemes[0] if matched_schemes else {
                "name": "No confident match",
                "category": extracted_fields.get("category") or "Any",
                "documents_required": [],
            }
            user_data = {
                "full_name": update.effective_user.full_name or "Applicant",
                "aadhaar_number": "0000-0000-0000",
                "category": extracted_fields.get("category"),
                "income_lakh": extracted_fields.get("income_lakh"),
                "state": extracted_fields.get("state"),
            }
            screenshot_path = form_fill.fill_form(user_data, best_scheme, form_png)
            with open(screenshot_path, "rb") as image_file:
                await update.message.reply_photo(
                    photo=image_file,
                    caption="Yaha ek sample filled form hai — apna asli application isi tarah bharna hoga.",
                )

        except Exception as exc:
            print(f"[Pipeline error] {exc}")
            await update.message.reply_text(
                "Sorry, abhi processing mein problem aa gayi. Thoda clear details ke saath dobara voice note bhejiye."
            )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"[Telegram error] {context.error}")


def main() -> None:
    load_dotenv()
    token = _require_env("TELEGRAM_BOT_TOKEN")

    asyncio.run(memory.init_db())

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.add_error_handler(error_handler)

    print("Scheme Setu bot running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()