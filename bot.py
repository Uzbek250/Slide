"""
Telegram bot. Foydalanuvchi bilan suhbat oqimi:
1. /start yoki har qanday matn -> mavzuni so'raydi
2. Mavzu kelganda -> sahifa sonini so'raydi
3. Son kelganda -> backend /generate ni chaqiradi -> .pptx yuboradi

Bot va backend alohida servis sifatida ishlaydi (HTTP orqali gaplashadi),
shuning uchun backend'ni keyinchalik boshqa mijozlar (web, Flutter) ham
ishlata oladi.
"""
import os
import logging
import httpx
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

TOPIC, SLIDE_COUNT = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Salom! Men sizga prezentatsiya (.pptx) tayyorlab beraman.\n\n"
        "Avval mavzuni yozing (masalan: \"O'zbekiston iqtisodiyoti\" yoki "
        "\"Fotosintez jarayoni\")."
    )
    return TOPIC


async def receive_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    topic = update.message.text.strip()
    if len(topic) < 3:
        await update.message.reply_text("Mavzu juda qisqa, yana urinib ko'ring.")
        return TOPIC

    context.user_data["topic"] = topic
    await update.message.reply_text(
        f"Mavzu: \"{topic}\"\n\nNechta slayd kerak? (3 dan 20 gacha son yozing)"
    )
    return SLIDE_COUNT


async def receive_slide_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not text.isdigit() or not (3 <= int(text) <= 20):
        await update.message.reply_text("Iltimos, 3 dan 20 gacha son kiriting.")
        return SLIDE_COUNT

    slide_count = int(text)
    topic = context.user_data["topic"]

    status_msg = await update.message.reply_text(
        "Tayyorlanmoqda, biroz kuting (bu 30-90 soniya davom etishi mumkin)..."
    )

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                f"{BACKEND_URL}/generate",
                json={"topic": topic, "slide_count": slide_count},
            )
            resp.raise_for_status()
            file_id = resp.json()["file_id"]

            file_resp = await client.get(f"{BACKEND_URL}/download/{file_id}")
            file_resp.raise_for_status()

        await status_msg.edit_text("Tayyor! Yuborilmoqda...")
        await update.message.reply_document(
            document=file_resp.content,
            filename=f"{topic[:40]}.pptx",
            caption=f"\"{topic}\" — {slide_count} slayd",
        )
    except Exception as e:
        logger.exception("Generation failed")
        await status_msg.edit_text(
            f"Xatolik yuz berdi, qaytadan urinib ko'ring.\n\nTafsilot: {e}"
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Bekor qilindi. Qayta boshlash uchun /start yozing.")
    return ConversationHandler.END


def build_app() -> Application:
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN muhit o'zgaruvchisi topilmadi")

    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_topic)],
            SLIDE_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_slide_count)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    return application


if __name__ == "__main__":
    app = build_app()
    app.run_polling()
