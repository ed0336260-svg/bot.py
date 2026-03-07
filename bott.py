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
user_queues = {}  # user_id -> asyncio.Queue()

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

async def ensure_user_queue(user_id: int):
    if user_id not in user_queues:
        user_queues[user_id] = asyncio.Queue()

@userbot.on(events.NewMessage(from_users=TARGET_BOT))
async def target_bot_handler(event):
    """
    Hedef bottan gelen mesaj ve dosyaları kullanıcıya gönderir.
    Dosya varsa diskten alıp gönderir ve siler.
    """
    target_user = None
    for user_id, queue in user_queues.items():
        if not queue.empty():
            target_user = user_id
            await queue.get()
            break

    if not target_user:
        return

    try:
        # ===== DOSYA VARSA =====
        if event.message.file:
            filename = event.message.file.name or "sonuc.txt"
            filepath = f"temp_{uuid.uuid4()}_{filename}"

            print(f"[INFO] Dosya indiriliyor: {filename}")
            await event.download_media(file=filepath)
            print(f"[INFO] Dosya indirildi, kullanıcıya gönderiliyor: {target_user}")

            # Kullanıcıya gönder
            await userbot.send_file(
                entity=target_user,
                file=filepath,
                caption=event.raw_text or "",
                force_document=True
            )

            os.remove(filepath)
            print(f"[INFO] Dosya gönderildi ve silindi: {filename}")

        # ===== SADECE MESAJ VARSA =====
        elif event.raw_text:
            await userbot.send_message(target_user, event.raw_text)

    except Exception as e:
        print(f"[ERROR] Gönderme hatası kullanıcı {target_user}: {e}")

@userbot.on(events.CallbackQuery)
async def callback_handler(event):
    """
    Hedef bottaki inline button callbacklarını işler
    """
    try:
        response = await userbot(GetBotCallbackAnswerRequest(
            peer=TARGET_BOT,
            msg_id=event.message.id,
            data=event.data
        ))

        if response.message:
            await userbot.send_message(event.sender_id, response.message)
        else:
            await event.answer("✅ İşlem tamamlandı", alert=True)

    except Exception as e:
        await userbot.send_message(event.sender_id, f"Callback hatası: {e}")

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

    await ensure_user_queue(user_id)
    await user_queues[user_id].put(text)

    # Hedef botta mesaj gönder
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
