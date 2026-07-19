import sqlite3
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, 
    ConversationHandler, ContextTypes, filters
)

# تنظیمات لاگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# تنظیمات اصلی
TOKEN = "8619432233:AAGqMmsjNi3ERpJKENuUxlheyrVZTP82wSw"
ADMIN_ID = 8946707153

NAME, LINK, PRICE = range(3)

# اتصال به دیتابیس
db = sqlite3.connect("channels.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS channels(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    link TEXT,
    price TEXT,
    status TEXT
)
""")
db.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["📤 ثبت کانال برای فروش"]]
    await update.message.reply_text("سلام 👋 به ربات خرید و فروش کانال خوش آمدید.", 
                                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def register_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 نام کانال را وارد کنید:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("🔗 لینک کانال را ارسال کنید:")
    return LINK

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["link"] = update.message.text
    await update.message.reply_text("💰 قیمت فروش را وارد کنید:")
    return PRICE

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_id = update.effective_user.id
    
    cursor.execute("INSERT INTO channels (user_id, name, link, price, status) VALUES (?, ?, ?, ?, ?)",
                   (user_id, user_data["name"], user_data["link"], update.message.text, "pending"))
    channel_id = cursor.lastrowid
    db.commit()

    admin_text = f"📢 درخواست جدید\n\n👤 کاربر: {user_id}\n📌 نام: {user_data['name']}\n🔗 لینک: {user_data['link']}\n💰 قیمت: {update.message.text}"
    
    buttons = [[
        InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{channel_id}_{user_id}"),
        InlineKeyboardButton("❌ رد", callback_data=f"reject_{channel_id}_{user_id}")
    ]]
    
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, reply_markup=InlineKeyboardMarkup(buttons))
    await update.message.reply_text("✅ ثبت شد. منتظر بررسی باشید.")
    return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action, channel_id, user_id = query.data.split("_")
    
    if action == "approve":
        cursor.execute("UPDATE channels SET status = 'approved' WHERE id = ?", (channel_id,))
        db.commit()
        await query.edit_message_text(f"{query.message.text}\n\n✅ وضعیت: تأیید شد")
        await context.bot.send_message(chat_id=user_id, text="تبریک! کانال شما تأیید شد و برای فروش قرار گرفت.")
        
    elif action == "reject":
        cursor.execute("UPDATE channels SET status = 'rejected' WHERE id = ?", (channel_id,))
        db.commit()
        await query.edit_message_text(f"{query.message.text}\n\n❌ وضعیت: رد شد")
        await context.bot.send_message(chat_id=user_id, text="متأسفانه کانال شما توسط مدیریت رد شد.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("📤 ثبت کانال برای فروش"), register_channel)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🤖 ربات روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
