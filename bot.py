from telethon import TelegramClient, events
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
import asyncio
import io

# ===== AYARLAR =====
api_id = 32778223
api_hash = "ff44a946dbb1dcfd979409f41a69afc9"
BOT_TOKEN = "8660964425:AAHgRUJWp866CJ-noKKivpd00VukNnjtWuU"

TARGET_BOT = "inzegosorgubot"

ADMINS = {8685981899, 6322020905}
banned_users = set()
active_users = set()

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

# ===== BOT =====
app = ApplicationBuilder().token(BOT_TOKEN).build()


# ===== HEDEF BOTTAN GELEN MESAJ =====
@userbot.on(events.NewMessage(from_users=TARGET_BOT))
async def target_bot_handler(event):

    for user_id in list(active_users):
        try:

            if event.file:

                filename = "sonuc.txt"

                buffer = io.BytesIO()
                await event.download_media(file=buffer)
                buffer.seek(0)

                input_file = InputFile(buffer, filename=filename)

                await app.bot.send_document(
                    chat_id=user_id,
                    document=input_file,
                    caption=event.raw_text if event.raw_text else ""
                )

            else:

                if event.raw_text:
                    await app.bot.send_message(
                        chat_id=user_id,
                        text=event.raw_text
                    )

        except Exception as e:
            print(f"Mesaj gönderilemedi ({user_id}): {e}")


# ===== BOT HANDLER =====
async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
    text = update.message.text

    if user_id in banned_users:
        await update.message.reply_text("🚫 Bu botu kullanmanız yasaklandı.")
        return

    if is_blocked(text):
        await update.message.reply_text("🚫 Bu sorgu engellendi.")
        return

    active_users.add(user_id)

    try:
        await userbot.send_message(TARGET_BOT, text)
    except Exception as e:
        print("Gönderme hatası:", e)
        await update.message.reply_text("❌ Mesaj hedef bota gönderilemedi.")


# ===== ADMIN KOMUTLARI =====
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id not in ADMINS:
        return

    try:
        uid = int(context.args[0])
        banned_users.add(uid)
        active_users.discard(uid)

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


# ===== MAIN =====
async def main():

    print("🔹 Userbot başlatılıyor")
    await userbot.start()
    print("✅ Userbot aktif")

    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("komutlar", komutlar))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_message))
    app.add_handler(MessageHandler(filters.COMMAND, user_message))

    print("🔹 Bot başlatılıyor")

    await app.initialize()
    await app.start()
    await app.bot.initialize()

    print("✅ Bot aktif")

    await asyncio.Future()


asyncio.run(main())
