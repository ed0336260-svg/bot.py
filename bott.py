import asyncio
import io
from telethon import TelegramClient, events
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# ===== AYARLAR =====
api_id = 32778223
api_hash = "ff44a946dbb1dcfd979409f41a69afc9"
BOT_TOKEN = "8626559225:AAGMk6hd0uDkUuGC30dv05ADoY-fMp_gJhY"
TARGET_BOT = "inzegosorgubot"
ADMINS = {8685981899, 6322020905}

# ===== DURUM =====
banned_users = set()
user_mapping = {}  # message_id -> user_id eşlemesi

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

async def send_to_user(user_id, text=None, file_bytes=None, filename=None):
    try:
        entity = await userbot.get_input_entity(user_id)
        if file_bytes:
            buffer = io.BytesIO(file_bytes)
            buffer.name = filename or "sonuc.txt"
            await userbot.send_file(entity, buffer, caption=text or "", force_document=True)
        elif text:
            await userbot.send_message(entity, text)
    except Exception as e:
        print(f"[ERROR] Kullanıcıya gönderilemedi {user_id}: {e}")

# ===== HEDEF BOT MESAJLARI =====
@userbot.on(events.NewMessage(from_users=TARGET_BOT))
async def target_bot_handler(event):
    reply_to = event.message.reply_to_msg_id
    if not reply_to:
        return

    user_id = user_mapping.get(reply_to)
    if not user_id:
        return

    try:
        if event.message.file:
            buffer = io.BytesIO()
            await event.download_media(buffer)
            buffer.seek(0)
            await send_to_user(user_id, file_bytes=buffer.read(), filename=event.message.file.name, text=event.raw_text)
        elif event.raw_text:
            await send_to_user(user_id, text=event.raw_text)
    except Exception as e:
        print(f"[ERROR] Hedef bottan kullanıcıya iletme hatası: {e}")

# ===== TELEGRAM BOT MESAJLARI =====
async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    text = update.message.text

    if user_id in banned_users:
        await update.message.reply_text("🚫 Bu botu kullanmanız yasaklandı.")
        return

    if is_blocked(text):
        await update.message.reply_text("🚫 Bu sorgu engellendi.")
        return

    sent = await userbot.send_message(TARGET_BOT, text)
    user_mapping[sent.id] = user_id  # Hangi kullanıcı için gönderildiğini kaydet

# ===== ADMIN KOMUTLARI =====
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

# ===== BOT AYARLARI =====
bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
bot_app.add_handler(CommandHandler("ban", ban))
bot_app.add_handler(CommandHandler("unban", unban))
bot_app.add_handler(CommandHandler("komutlar", komutlar))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_message))

# ===== MAIN =====
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
