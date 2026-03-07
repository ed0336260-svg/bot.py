import asyncio
import os
import uuid
from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# ===== AYARLAR =====
api_id = 32778223
api_hash = "ff44a946dbb1dcfd979409f41a69afc9"
BOT_TOKEN = "8660964425:AAHgRUJWp866CJ-noKKivpd00VukNnjtWuU"
TARGET_BOT = "inzegosorgubot"
ADMINS = {8685981899, 6322020905}

# ===== DURUM =====
banned_users = set()
pending_users = asyncio.Queue()

# ===== YASAKLI KELİMELER =====
blocked_phrases = [
    "abdurrahman miran karabulak diyarbakır",
    "miray karabulak diyarbakır",
    "erol karabulak diyarbakır",
    "/gsmtc 5337311021"
]

def is_blocked(text: str) -> bool:
    t = text.lower().replace("+", " ")
    return any(b in t for b in blocked_phrases)

# ===== USERBOT =====
userbot = TelegramClient("userbot_session", api_id, api_hash)

@userbot.on(events.NewMessage(from_users=TARGET_BOT))
async def target_bot_handler(event):

    if pending_users.empty():
        return

    user_id = await pending_users.get()

    try:

        # ===== DOSYA GELDİYSE =====
        if event.message.file:

            filename = event.message.file.name or "sonuc.txt"

            temp_path = f"/tmp/{uuid.uuid4()}_{filename}"

            # Dosyayı disk üzerinden indir (RAM kullanmaz)
            await event.download_media(temp_path)

            # Kullanıcıya gönder
            with open(temp_path, "rb") as f:
                await bot_app.bot.send_document(
                    chat_id=user_id,
                    document=f,
                    caption=event.raw_text or "",
                    read_timeout=None,
                    write_timeout=None
                )

            os.remove(temp_path)

        # ===== SADECE MESAJ GELDİYSE =====
        elif event.raw_text:

            await bot_app.bot.send_message(
                chat_id=user_id,
                text=event.raw_text
            )

    except Exception as e:
        print("Gönderme hatası:", e)


@userbot.on(events.CallbackQuery)
async def callback_handler(event):

    try:

        response = await userbot(GetBotCallbackAnswerRequest(
            peer=TARGET_BOT,
            msg_id=event.message.id,
            data=event.data
        ))

        if response.message:
            await bot_app.bot.send_message(event.sender_id, response.message)
        else:
            await event.answer("✅ İşlem tamamlandı", alert=True)

    except Exception as e:
        await bot_app.bot.send_message(event.sender_id, f"Callback hatası: {e}")


# ===== BOT =====

async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
    text = update.message.text

    if user_id in banned_users:
        await update.message.reply_text("🚫 Bu botu kullanmanız yasaklandı.")
        return

    if is_blocked(text):
        await update.message.reply_text("🚫 Bu sorgu engellendi.")
        return

    # Kullanıcıyı sıraya ekle
    await pending_users.put(user_id)

    # Hedef bota gönder
    await userbot.send_message(TARGET_BOT, text)


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id not in ADMINS:
        return

    try:
        uid = int(context.args[0])
        banned_users.add(uid)
        await update.message.reply_text(f"✅ {uid} banlandı.")
    except:
        await update.message.reply_text("Kullanım: /ban kullanıcı_id")


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id not in ADMINS:
        return

    try:
        uid = int(context.args[0])
        banned_users.discard(uid)
        await update.message.reply_text(f"✅ {uid} banı kaldırıldı.")
    except:
        await update.message.reply_text("Kullanım: /unban kullanıcı_id")


async def komutlar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🔎 SORGU KOMUTLARI\n\n"
        "/sorgu mehmet demir İstanbul\n"
        "/sorgu mehmet+akif demir İstanbul\n\n"
        "/gsmtc 5555555555\n"
        "/ipsorgu 1.1.1.1\n"
        "/operator 5555555555\n"
        "/isyeri 11111111110\n"
        "/tcpro 11111111110\n\n"
        "📌 TOPLU\n"
        "/toplu 11111111110\n"
        "/toplu 5555555555"
    )


bot_app = ApplicationBuilder().token(BOT_TOKEN).build()

bot_app.add_handler(CommandHandler("ban", ban))
bot_app.add_handler(CommandHandler("unban", unban))
bot_app.add_handler(CommandHandler("komutlar", komutlar))

bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_message))
bot_app.add_handler(MessageHandler(filters.COMMAND, user_message))


async def main():

    print("🔹 Userbot başlatılıyor")
    await userbot.start()
    print("✅ Userbot aktif")

    print("🔹 Bot başlatılıyor")

    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()

    print("✅ Bot aktif")

    await asyncio.Future()


asyncio.run(main())
