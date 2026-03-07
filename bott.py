import asyncio
import io
from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
from telethon.errors.rpcerrorlist import UserIdInvalidError
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# ===== AYARLAR =====
api_id = 32778223
api_hash = "ff44a946dbb1dcfd979409f41a69afc9"
BOT_TOKEN = "8660964425:AAHgRUJWp866CJ-noKKivpd00VukNnjtWuU"
TARGET_BOT = "inzegosorgubot"
ADMINS = {8685981899, 6322020905}

# ===== DURUM =====
banned_users = set()
pending_messages = {}  # user_id -> mesaj bekleniyor

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

async def send_to_user(user_id, file_bytes=None, filename=None, text=None):
    try:
        entity = await userbot.get_input_entity(user_id)
    except UserIdInvalidError:
        print(f"[ERROR] Kullanıcı {user_id} bulunamadı.")
        return
    except Exception as e:
        print(f"[ERROR] Entity alınamadı kullanıcı {user_id}: {e}")
        return

    try:
        if file_bytes:
            file_obj = io.BytesIO(file_bytes)
            file_obj.name = filename or "sonuc.txt"
            await userbot.send_file(entity=entity, file=file_obj, caption=text, force_document=True)
        elif text:
            await userbot.send_message(entity=entity, message=text)
    except Exception as e:
        print(f"[ERROR] Gönderme hatası kullanıcı {user_id}: {e}")

@userbot.on(events.NewMessage(from_users=TARGET_BOT))
async def target_bot_handler(event):
    for user_id, waiting in pending_messages.items():
        if waiting:
            pending_messages[user_id] = False
            try:
                if event.message.file:
                    buffer = io.BytesIO()
                    await event.download_media(file=buffer)
                    buffer.seek(0)
                    await send_to_user(user_id, file_bytes=buffer.read(), filename=event.message.file.name, text=event.raw_text)
                elif event.raw_text:
                    await send_to_user(user_id, text=event.raw_text)
            except Exception as e:
                print(f"[ERROR] Gönderme hatası kullanıcı {user_id}: {e}")
            break

@userbot.on(events.CallbackQuery)
async def callback_handler(event):
    try:
        response = await userbot(GetBotCallbackAnswerRequest(
            peer=TARGET_BOT,
            msg_id=event.message.id,
            data=event.data
        ))
        if response.message:
            await send_to_user(event.sender_id, text=response.message)
        else:
            await event.answer("✅ İşlem tamamlandı", alert=True)
    except Exception as e:
        await send_to_user(event.sender_id, text=f"Callback hatası: {e}")

# ===== TELEGRAM BOT =====
async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    text = update.message.text

    if user_id in banned_users:
        await update.message.reply_text("🚫 Bu botu kullanmanız yasaklandı.")
        return
    if is_blocked(text):
        await update.message.reply_text("🚫 Bu sorgu engellendi.")
        return

    pending_messages[user_id] = True
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
