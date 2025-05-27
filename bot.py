from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters

CHANNEL_USERNAME = "@Mobile_Legend_Persian"

PRICES = {
    'Supreme': 1500000,
    'Grand': 500000,
    'Exquisite': 300000
}

EXPLANATIONS = {
    'Supreme': "این دسته شامل اسکین‌های **لجند** می‌باشد.\nچندتا اسکین از این دسته داری؟",
    'Grand': "این دسته شامل اسکین‌های **کوف، جوجوتسو، سوپر هیرو، استاروارز، ناروتو، ابیس و...** هستن.\nتو کالکشن، قسمت **گرند** می‌تونید چک کنید.\nچندتا اسکین از این دسته داری؟",
    'Exquisite': "این دسته شامل اسکین‌های **کالکتور، لاکی باکس** و **کلادز** می‌باشد.\nچندتا اسکین از این دسته داری؟",
    'Deluxe': "این دسته شامل زودیاک، لایتبورن، اپیک شاپ و... می‌باشد.\nچندتا اسکین از این دسته داری؟"
}

CHOOSE_SKIN, CONFIRM_END = range(2)

async def check_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

async def check_membership_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if await check_membership(user_id, context):
        await query.edit_message_text(
            "✅ عضویت شما تایید شد! حالا می‌تونی از ربات استفاده کنی.\n"
            "توجه: اسکین‌های رایگان مثل **کوف کارینا** و... رو حساب نکنید چون ارزش خاصی ندارن.\n\n"
            "بعد از مطالعه، دکمه /start رو بزن و ادامه بده."
        )
    else:
        keyboard = [
            [InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("عضوشدم | فعال‌سازی", callback_data="check_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"⛔️ هنوز عضو کانال نشدی!\n\nلطفاً روی دکمه زیر کلیک کن و بعد دوباره دکمه 'عضوشدم | فعال‌سازی' رو بزن.",
            reply_markup=reply_markup
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(user_id, context):
        keyboard = [
            [InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("عضوشدم | فعال‌سازی", callback_data="check_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "برای استفاده از ربات لطفاً عضو کانال زیر شوید:",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    context.user_data['skins'] = {}

    keyboard = [
        [KeyboardButton("Supreme")],
        [KeyboardButton("Grand")],
        [KeyboardButton("Exquisite")],
        [KeyboardButton("Deluxe")],
        [KeyboardButton("پایان")]
    ]

    await update.message.reply_text(
        "سلام! لطفاً نوع اسکینت رو انتخاب کن.",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
    )
    return CHOOSE_SKIN

async def choose_skin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == 'پایان':
        return await show_summary(update, context)

    if text not in EXPLANATIONS:
        await update.message.reply_text("لطفاً یکی از اسکین‌های موجود یا گزینه 'پایان' رو انتخاب کن.")
        return CHOOSE_SKIN

    context.user_data['current_skin'] = text
    await update.message.reply_text(EXPLANATIONS[text])
    return CONFIRM_END

async def confirm_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        skin = context.user_data['current_skin']

        if skin == "Deluxe":
            if count < 20:
                price = count * 25000
            elif 20 <= count <= 40:
                price = 500000
            else:
                price = 700000
        else:
            price = PRICES[skin] * count

        if 'skins' not in context.user_data:
            context.user_data['skins'] = {}

        context.user_data['skins'][skin] = context.user_data['skins'].get(skin, 0) + count

        if 'prices' not in context.user_data:
            context.user_data['prices'] = {}

        context.user_data['prices'][skin] = context.user_data['prices'].get(skin, 0) + price

        await update.message.reply_text(
            f"اسکین {skin} با تعداد {count} اضافه شد! برای ادامه انتخاب کن یا 'پایان' رو بزن."
        )

        keyboard = [
            [KeyboardButton("Supreme")],
            [KeyboardButton("Grand")],
            [KeyboardButton("Exquisite")],
            [KeyboardButton("Deluxe")],
            [KeyboardButton("پایان")]
        ]

        await update.message.reply_text(
            "یک اسکین دیگه انتخاب کن یا 'پایان' رو بزن:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
        )

        return CHOOSE_SKIN
    except:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کن.")
        return CONFIRM_END

async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    skins = context.user_data.get('skins', {})
    prices = context.user_data.get('prices', {})
    if not skins:
        await update.message.reply_text("هنوز هیچ اسکینی انتخاب نکردی!")
        return ConversationHandler.END

    summary = ""
    total_price = 0

    for skin, count in skins.items():
        summary += f"{skin}: {count} عدد\n"
        total_price += prices.get(skin, 0)

    keyboard = [[InlineKeyboardButton("برای آگهی کردن کلیک کنید", url="https://t.me/Tareq_Cesar_Trade")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ اسکین‌هایی که انتخاب کردی:\n{summary}\nقیمت کل: {total_price:,} تومان",
        reply_markup=reply_markup
    )

    await update.message.reply_text("برای شروع دوباره /start رو بزن.")
    return ConversationHandler.END

app = ApplicationBuilder().token("7963209844:AAG03aE50l2ljMAH604M1sT1a3IHU85o3fs").build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSE_SKIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_skin)],
        CONFIRM_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_end)]
    },
    fallbacks=[CommandHandler("start", start)]
)

app.add_handler(conv_handler)
app.add_handler(CallbackQueryHandler(check_membership_button, pattern="check_membership"))

app.run_polling()
