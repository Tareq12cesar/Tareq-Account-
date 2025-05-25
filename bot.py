from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters

# اطلاعات اسکین‌ها و قیمت‌ها
CHANNEL_USERNAME = "@Mobile_Legend_Persian"
PRICES = {
    'لجند': 1200000,
    'کوف': 500000,
    'آیتمه ایی': 500000,
    'کالکتور': 300000
}

CHOOSE_SKIN, END_SELECTION = range(2)

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
        await update.message.reply_text(f"اول عضو کانال {CHANNEL_USERNAME} شو و بعد دکمه رو بزن.")
        return ConversationHandler.END

    # خالی کردن انتخاب‌های قبلی
    context.user_data['selected_skins'] = []

    keyboard = [[KeyboardButton(skin)] for skin in PRICES.keys()]
    await update.message.reply_text(
        "سلام! لطفاً نوع اسکینت رو انتخاب کن.",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
    )
    return CHOOSE_SKIN

# انتخاب اسکین‌ها
async def choose_skin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    skin = update.message.text
    if skin in PRICES:
        context.user_data['selected_skins'].append(skin)
        await update.message.reply_text(
            f"اسکین {skin} اضافه شد! میخوای ادامه بدی یا قیمت نهایی رو ببینی؟",
            reply_markup=ReplyKeyboardMarkup([['ادامه', 'پایان']], one_time_keyboard=True, resize_keyboard=True)
        )
        return CHOOSE_SKIN
    elif skin == 'پایان':
        return await end_selection(update, context)
    elif skin == 'ادامه':
        keyboard = [[KeyboardButton(skin)] for skin in PRICES.keys()]
        await update.message.reply_text(
            "یک اسکین دیگه انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
        )
        return CHOOSE_SKIN
    else:
        await update.message.reply_text("لطفاً گزینه معتبر انتخاب کن.")
        return CHOOSE_SKIN

# محاسبه و نمایش قیمت نهایی
async def end_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    skins = context.user_data.get('selected_skins', [])
    if not skins:
        await update.message.reply_text("هنوز هیچ اسکینی انتخاب نکردی!")
        return ConversationHandler.END

    total_price = sum(PRICES.get(s, 0) for s in skins)
    await update.message.reply_text(
        f"✅ اسکین‌هایی که انتخاب کردی:\n" + "\n".join(skins) + f"\n\nجمع کل قیمت: {total_price} سکه"
    )
    return ConversationHandler.END

# ست کردن هندلرها
app = ApplicationBuilder().token("توکن بات").build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSE_SKIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_skin)],
    },
    fallbacks=[CommandHandler("cancel", end_selection)]
)

app.add_handler(conv_handler)

app.run_polling()
