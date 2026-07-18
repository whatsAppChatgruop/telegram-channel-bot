import sqlite3
import logging

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)


logging.basicConfig(
    level=logging.INFO
)


TOKEN = "8619432233:AAGqMmsjNi3ERpJKENuUxlheyrVZTP82wSw"
ADMIN_ID = 9846707153


NAME, LINK, PRICE = range(3)


db = sqlite3.connect(
    "channels.db",
    check_same_thread=False
)

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

    keyboard = [
        ["📤 ثبت کانال برای فروش"]
    ]

    await update.message.reply_text(
        "سلام 👋\n"
        "به ربات خرید و فروش کانال خوش آمدید.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def register_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📌 نام کانال را وارد کنید:"
    )

    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["name"] = update.message.text

    await update.message.reply_text(
        "🔗 لینک اصلی کانال را ارسال کنید:"
    )

    return LINK


async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["link"] = update.message.text

    await update.message.reply_text(
        "💰 قیمت فروش کانال را وارد کنید:"
    )

    return PRICE


async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["price"] = update.message.text

    name = context.user_data["name"]
    link = context.user_data["link"]
    price = context.user_data["price"]

    user_id = update.effective_user.id

    cursor.execute(
        """
        INSERT INTO channels
        (user_id, name, link, price, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            name,
            link,
            price,
            "در انتظار بررسی"
        )
    )

    db.commit()




    db.commit()


    admin_text = f"""
📢 درخواست جدید فروش کانال

👤 آیدی کاربر:
{user_id}

📌 نام کانال:
{name}

🔗 لینک:
{link}

💰 قیمت:
{price}

⏳ وضعیت:
در انتظار بررسی
"""


    buttons = [
        [
            InlineKeyboardButton(
                "✅ تأیید",
                callback_data="approve"
            ),
            InlineKeyboardButton(
                "❌ رد",
                callback_data="reject"
            )
        ]
    ]


    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


    await update.message.reply_text(
        "✅ اطلاعات کانال ثبت شد.\n"
        "منتظر بررسی مدیریت باشید."
    )


    return ConversationHandler.END


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    if query.data == "approve":

        await query.edit_message_text(
            query.message.text +
            "\n\n✅ وضعیت: تأیید شد"
        )

    elif query.data == "reject":

        await query.edit_message_text(
            query.message.text +
            "\n\n❌ وضعیت: رد شد"
        )



async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "❌ عملیات لغو شد."
    )

    return ConversationHandler.END
def main():

    app = Application.builder().token(TOKEN).build()


    conversation = ConversationHandler(

        entry_points=[
            MessageHandler(
                filters.Regex("📤 ثبت کانال برای فروش"),
                register_channel
            )
        ],

        states={

            NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_name
                )
            ],

            LINK: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_link
                )
            ],

            PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_price
                )
            ]
        },

        fallbacks=[
            CommandHandler(
                "cancel",
                cancel
            )
        ]
    )


    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    app.add_handler(
        conversation
    )


    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )


    print("🤖 ربات فعال است...")


    app.run_polling()



if __name__ == "__main__":
    main()