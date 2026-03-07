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

active_users = {}  # user_id : True

# ===== YASAKLI KELİMELER =====
blocked_phrases = [
    "abdurrahman miran karabulak diyarbakır",
    "miray karabulak diyarbakır",
    "erol karabulak diyarbakır",
    "/gsmtc 5337311021"
]

def is_blocked(text):
    t = text.lower().replace("+", " ")
    return any(b in t for b in blocked_phrases)

# ===== USERBOT =====
userbot = TelegramClient("userbot_session", api_id, api_hash)

# HEDEF BOTTAN GELEN MESAJ
@userbot.on(events.NewMessage(from_users=TARGET_BOT))
async def target_bot_handler(event):

    for user_id in list(active_users.keys()):
        try:

            if event.file:
                buffer = io.BytesIO()
                await event.download_media(file=buffer)
                buffer.seek(0)

                await app.bot.send_document(
                    chat_id=user_id,
                    document=InputFile(buffer, filename="sonuc.txt"),
                    caption=event.raw_text if event.raw_text else ""
                )

            else:
                await app.bot.send_message(
                    chat_id=user_id,
                    text=event.raw_text
                )

        except Exception as e:
            print("Gönderme hatası:", e)


# ===== KULLANICI MESAJI =====
async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    text = update.message.text

    if user_id in banned_users:
        await update.message.reply_text("🚫 Yasaklandınız.")
        return

    if is_blocked(text):
        await update.message.reply_text("🚫 Bu sorgu engellendi.")
        return

    active_users[user_id] = True

    try:
        await userbot.send_message(TARGET_BOT, text)
    except Exception as e:
        print("Gönderme hatası:", e)
        await update.message.reply_text("❌ Hedef bota mesaj gönderilemedi.")


# ===== ADMIN =====
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id not in ADMINS:
        return

    try:
        uid = int(context.args[0])
        banned_users.add(uid)
        active_users.pop(uid, None)

        await update.message.reply_text(f"✅ {uid} banlandı")

    except:
        await update.message.reply_text("Kullanım: /ban id")


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id not in ADMINS:
        return

    try:
        uid = int(context.args[0])
        banned_users.discard(uid)

        await update.message.reply_text(f"✅ {uid} ban kaldırıldı")

    except:
        await update.message.reply_text("Kullanım: /unban id")


async def komutlar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
"""🔎 SORGU KOMUTLARI

/sorgu mehmet demir İstanbul
/sorgu mehmet+akif demir İstanbul

/gsmtc 5555555555
/ipsorgu 1.1.1.1
/operator 5555555555
/isyeri 11111111110
/tcpro 11111111110

📌 TOPLU
/toplu 11111111110
/toplu 5555555555
"""
)

# ===== MAIN =====
async def main():

    global app

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("komutlar", komutlar))

    app.add_handler(MessageHandler(filters.TEXT, user_message))

    print("Userbot başlatılıyor...")
    await userbot.start()
    print("Userbot aktif")

    print("Bot başlatılıyor...")
    await app.initialize()
    await app.start()
    await app.bot.initialize()

    print("Bot aktif")

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
