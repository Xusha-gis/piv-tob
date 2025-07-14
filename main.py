
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from datetime import datetime, timedelta
import sqlite3
from config import BOT_TOKEN, ADMIN_ID, CHANNEL_LINK

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, end_date TEXT)")
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    c.execute("INSERT OR REPLACE INTO users (user_id, end_date) VALUES (?, ?)", (user_id, end_date))
    conn.commit()
    conn.close()

def get_end_date(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT end_date FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    end_date = get_end_date(user_id)

    if end_date and datetime.strptime(end_date, "%Y-%m-%d") > datetime.now():
        keyboard = [[InlineKeyboardButton("🔗 Kanalga kirish", url=CHANNEL_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "✅ Obunangiz faol. Premium kanalga kirish uchun quyidagi havolani bosing:",
            reply_markup=reply_markup
        )
    else:
        keyboard = [[InlineKeyboardButton("✅ To'lovni amalga oshirdim", callback_data="confirm_payment")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "👋 Salom! Premium kanalga kirish uchun to‘lov qilishingiz kerak.\n\n"
            "💳 Narx: 20 000 so‘m\n"
            "💰 To‘lov uchun Click ID: 8800 4112 2224 9762\n\n"
            "✅ To‘lov qilgan bo‘lsangiz, quyidagi tugmani bosing:",
            reply_markup=reply_markup
        )

async def handle_confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📤 Iltimos, Click to‘lov chekini rasm yoki PDF shaklida shu yerga yuboring.")

async def handle_photo_or_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if update.message.photo or update.message.document:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📥 Yangi to‘lov cheki keldi\n👤 User ID: {user.id}\n👤 Ismi: {user.full_name}"
        )
        await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=user.id, message_id=update.message.message_id)
        await update.message.reply_text("✅ Chek yuborildi. Admin tekshiradi. Kuting...")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Sizda ruxsat yo'q.")
        return
    if context.args:
        user_id = int(context.args[0])
        add_user(user_id)
        await update.message.reply_text(f"{user_id} tasdiqlandi va obunasi faollashtirildi.")
        await context.bot.send_message(chat_id=user_id, text=f"✅ To'lov tasdiqlandi. Kirish: {CHANNEL_LINK}")
    else:
        await update.message.reply_text("Foydalanuvchi ID kiritilmadi.")

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT user_id, end_date FROM users")
    rows = c.fetchall()
    conn.close()
    msg = "\n".join([f"{row[0]} – tugash: {row[1]}" for row in rows])
    await update.message.reply_text(f"Obunachilar:\n{msg}")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if context.args:
        user_id = int(context.args[0])
        end_date = get_end_date(user_id)
        if end_date:
            await update.message.reply_text(f"{user_id} – obuna tugash sanasi: {end_date}")
        else:
            await update.message.reply_text("Foydalanuvchi topilmadi.")
    else:
        await update.message.reply_text("Foydalanuvchi ID kiritilmadi.")

if __name__ == "__main__":
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("users", users))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CallbackQueryHandler(handle_confirm_payment, pattern="confirm_payment"))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_photo_or_file))
    app.run_polling()
