import asyncio
import io
import os
from collections import defaultdict
from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# ===== AYARLAR =====
api_id = 32778223
api_hash = "ff44a946dbb1dcfd979409f41a69afc9"
BOT_TOKEN = "8660964425:AAHgRUJWp866CJ-noKKivpd00VukNnjtWuU"
TARGET_BOT = "inzegosorgubot"
ADMINS = {8685981899, 6322020905}

# ===== DURUM YÖNETİMİ =====
banned_users = set()
pending_users = defaultdict(list)  # {user_id: [text veya {'file_path': ..., 'caption': ...}]}

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

async def process_pending_messages(user_id):
    """Kuyruktaki mesajları sırayla gönderir"""
    while pending_users[user_id]:
        item = pending_users[user_id][0]
        try:
            if isinstance(item, dict) and 'file_path' in item:
                await bot_app.bot.send_document(
                    chat_id=user_id,
                    document=InputFile(item['file_path']),
                    caption=item.get('caption', '')
                )
                # Gönderildikten sonra geçici dosyayı sil
                os.remove(item['file_path'])
            else:
                await bot_app.bot.send_message(chat_id=user_id, text=item)
        except Exception as e:
            print(f"Mesaj gönderilemedi ({user_id}): {e}")
        pending_users[user_id].pop(0)
        await asyncio.sleep(0.3)  # Telegram rate limit önleme
    if not pending_users[user_id]:
        pending_users.pop(user_id, None)

@userbot.on(events.NewMessage(from_users=TARGET_BOT))
async def target_bot_handler(event):
    """Hedef bottan gelen mesajları kullanıcılara iletir"""
    for user_id in list(pending_users.keys()):
        queue = pending_users[user_id]
        if not queue:
            continue

        if event.file:
            filename = event.file.name or "sonuc.txt"
            file_path = f"/tmp/{filename}"
            await event.download_media(file=file_path)
            queue[0] = {'file_path': file_path, 'caption': event.raw_text or ""}
        else:
            queue[0] = event.raw_text or ""

        asyncio.create_task(process_pending_messages(user_id))

@userbot.on(events.CallbackQuery)
async def callback_handler(event):
    """Hedef bottaki inline callback'leri işler"""
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

    pending_users[user_id].append(text)
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

# ===== BOT UYGULAMA =====
bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
bot_app.add_handler(CommandHandler("ban", ban))
bot_app.add_handler(CommandHandler("unban", unban))
bot_app.add_handler(CommandHandler("komutlar", komutlar))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_message))
bot_app.add_handler(MessageHandler(filters.COMMAND, user_message))

# ===== ASYNCIO İLE HEM USERBOT HEM BOT =====
async def main():
    print("🔹 Userbot başlatılıyor")
    await userbot.start()
    print("✅ Userbot aktif")

    print("🔹 Bot başlatılıyor")
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    print("✅ Bot aktif")

    await asyncio.Future()  # Sonsuz bekleme

asyncio.run(main())
