from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters

# اطلاعات اسکین‌ها و قیمت‌ها
CHANNEL_USERNAME = "@Mobile_Legend_Persian"
PRICES = {
    'لجند': 1200000,
    'کوف': 500000,
    'ایوونتی': 500000,
    'کالکتور': 300000,
    'لاکی باکس': 300000
}

CHOOSE_SKIN, ENTER_QUANTITY = range(2)

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
        await update.message.reply_text(f"لطفاً اول عضو کانال {CHANNEL_USERNAME} شو و بعد دکمه رو بزن.")
        return ConversationHandler.END

    context.user_data['skins'] = {}

    keyboard = [[KeyboardButton(skin)] for skin in PRICES.keys()]
    await update.message.reply_text(
        "سلام! لطفاً نوع اسکینت رو انتخاب کن:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSE_SKIN

# انتخاب نوع اسکین
async def choose_skin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    skin = update.message.text
    if skin in PRICES:
        context.user_data['current_skin'] = skin
        await update.message.reply_text(f"چند تا {skin} داری؟")
        return ENTER_QUANTITY
    else:
        await update.message.reply_text("لطفاً یکی از گزینه‌ها رو انتخاب کن.")
        return CHOOSE_SKIN

# وارد کردن تعداد اسکین
async def enter_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        quantity = int(update.message.text)
        skin = context.user_data['current_skin']
        context.user_data['skins'][skin] = quantity

        keyboard = [[KeyboardButton(skin)] for skin in PRICES.keys()] + [[KeyboardButton("پایان")]]
        await update.message.reply_text(
            "نوع اسکین بعدی رو انتخاب کن یا پایان رو بزن:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return CHOOSE_SKIN
    except:
        await update.message.reply_text("لطفاً عدد معتبر وارد کن.")
        return ENTER_QUANTITY

# نمایش نتیجه نهایی
async def end_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    skins = context.user_data.get('skins', {})
    if not skins:
        await update.message.reply_text("هیچ اسکینی انتخاب نکردی!")
        return ConversationHandler.END

    total_price = 0
    details = ""
    for skin, count in skins.items():
        price = PRICES[skin] * count
        total_price += price
        details += f"{skin}: {count}\n"

    await update.message.reply_text(
        f"✅ خلاصه انتخاب‌ها:\n\n{details}\nجمع کل: {total_price:,} تومان"
    )
    return ConversationHandler.END

# ست کردن هندلرها
app = ApplicationBuilder().token("7963209844:AAE2WtF6Gdo2vJkj96erXmN7CItDK4dmS4c").build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSE_SKIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_skin)],
        ENTER_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_quantity)],
    },
    fallbacks=[MessageHandler(filters.Regex('^پایان$'), end_selection)]
)

app.add_handler(conv_handler)

app.run_polling()
