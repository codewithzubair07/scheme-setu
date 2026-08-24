import asyncio
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import memory
import pipeline
import stt


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

    user_id = str(update.effective_user.id)
    with tempfile.TemporaryDirectory() as temp_dir:
        input_ogg = str(Path(temp_dir) / f"voice_{user_id}.ogg")

        try:
            voice_file = await update.message.voice.get_file()
            await voice_file.download_to_drive(input_ogg)

            transcript = stt.transcribe(input_ogg)
            result = await pipeline.run_turn(user_id, transcript)

            await update.message.reply_text(result["reply_text"])
            with open(result["reply_audio_path"], "rb") as audio_file:
                await update.message.reply_voice(voice=audio_file)
            with open(result["form_html_path"], "rb") as form_file:
                await update.message.reply_document(
                    document=form_file,
                    filename="scheme_setu_form.html",
                    caption="Yaha mock filled form hai — browser mein khol kar check karein.",
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
