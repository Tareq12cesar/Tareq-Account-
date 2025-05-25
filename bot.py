from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters

CHANNEL_USERNAME = "@Mobile_Legend_Persian"

PRICES = {
    'لجند': 1200000,
    'کوف': 500000,
    'ایونتی': 500000,
    'کالکتور': 300000,
    'لاکی باکس': 300000
}

CHOOSE_SKIN, CONFIRM_END = range(2)

# بررسی عضویت کاربر
async def check_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(user_id, context):
        await update.message.reply_text(f"اول عضو کانال {CHANNEL_USERNAME} شو و بعد دکمه /start رو بزن.")
        return ConversationHandler.END

    context.user_data['skins'] = {}

    keyboard = [[KeyboardButton(skin)] for skin in PRICES.keys()]
    await update.message.reply_text(
        "سلام! لطفاً نوع اسکینت رو انتخاب کن.",
        reply_markup=ReplyKeyboardMarkup(keyboard + [['پایان']], one_time_keyboard=False, resize_keyboard=True)
    )
    return CHOOSE_SKIN

# انتخاب اسکین‌ها
async def choose_skin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == 'پایان':
        return await show_summary(update, context)

    if text not in PRICES:
        await update.message.reply_text("لطفاً یکی از اسکین‌های موجود یا گزینه 'پایان' رو انتخاب کن.")
        return CHOOSE_SKIN

    context.user_data['current_skin'] = text
    await update.message.reply_text(f"چند تا از اسکین {text} داری؟")
    return CONFIRM_END

# گرفتن تعداد
async def confirm_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        skin = context.user_data['current_skin']

        if skin in context.user_data['skins']:
            context.user_data['skins'][skin] += count
        else:
            context.user_data['skins'][skin] = count

        await update.message.reply_text(
            f"اسکین {skin} با تعداد {count} اضافه شد! برای ادامه انتخاب کن یا 'پایان' رو بزن."
        )

        keyboard = [[KeyboardButton(skin)] for skin in PRICES.keys()]
        await update.message.reply_text(
            "یک اسکین دیگه انتخاب کن یا 'پایان' رو بزن:",
            reply_markup=ReplyKeyboardMarkup(keyboard + [['پایان']], one_time_keyboard=False, resize_keyboard=True)
        )

        return CHOOSE_SKIN
    except:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کن.")
        return CONFIRM_END

# نمایش خلاصه
async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    skins = context.user_data.get('skins', {})
    if not skins:
        await update.message.reply_text("هنوز هیچ اسکینی انتخاب نکردی!")
        return ConversationHandler.END

    summary = ""
    total_price = 0

    for skin, count in skins.items():
        price = PRICES[skin] * count
        summary += f"{skin} {count}\n"
        total_price += price

    await update.message.reply_text(
        f"✅ اسکین‌هایی که انتخاب کردی:\n{summary}\nقیمت کل: {total_price:,} تومان\n\nبرای شروع دوباره /start رو بزن."
    )

    return ConversationHandler.END

# تنظیم هندلرها
app = ApplicationBuilder().token("7963209844:AAE2WtF6Gdo2vJkj96erXmN7CItDK4dmS4c").build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSE_SKIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_skin)],
        CONFIRM_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_end)]
    },
    fallbacks=[CommandHandler("start", start)]
)

app.add_handler(conv_handler)

app.run_polling()
