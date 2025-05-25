import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes,
    ConversationHandler, filters
)

CHANNEL_USERNAME = "@Mobile_Legend_Persian"

PRICES = {
    'لجند': 1200000,
    'کوف': 500000,
    'ایوونتی': 500000,
    'کالکتور': 300000,
    'لاکی باکس': 300000
}

CHOOSE_SKIN, ENTER_QUANTITY, CONFIRM_ANOTHER = range(3)

async def check_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(user_id, context):
        await update.message.reply_text(
            f"لطفاً برای استفاده از ربات، اول عضو کانال {CHANNEL_USERNAME} شو و بعد /start رو بزن."
        )
        return ConversationHandler.END

    context.user_data['skins'] = {}
    keyboard = [[KeyboardButton(skin)] for skin in PRICES.keys()]
    await update.message.reply_text(
        "سلام! لطفاً نوع اسکینت رو انتخاب کن:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSE_SKIN

async def choose_skin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    skin = update.message.text
    if skin not in PRICES:
        await update.message.reply_text("لطفاً یکی از گزینه‌ها رو انتخاب کن.")
        return CHOOSE_SKIN

    context.user_data['current_skin'] = skin
    await update.message.reply_text(f"چند تا اسکین {skin} داری؟")
    return ENTER_QUANTITY

async def enter_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        skin = context.user_data['current_skin']
        context.user_data['skins'][skin] = count
        await update.message.reply_text("میخوای نوع دیگه‌ای از اسکین‌ها رو هم وارد کنی؟ (بله/خیر)")
        return CONFIRM_ANOTHER
    except:
        await update.message.reply_text("لطفاً عدد معتبر وارد کن.")
        return ENTER_QUANTITY

async def confirm_another(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.lower()
    if answer in ['بله', 'آره', 'yes']:
        keyboard = [[KeyboardButton(skin)] for skin in PRICES.keys()]
        await update.message.reply_text(
            "نوع اسکین بعدی رو انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return CHOOSE_SKIN
    else:
        total_price = 0
        details = ""
        for skin, count in context.user_data['skins'].items():
            price = PRICES[skin] * count
            total_price += price
            details += f"{skin} × {count} = {price:,} تومان\n"
        await update.message.reply_text(
            f"خلاصه قیمت‌ها:\n\n{details}\nجمع کل: {total_price:,} تومان\nبرای شروع مجدد /start رو بزن."
        )
        return ConversationHandler.END

async def error(update, context):
    logging.warning(f'Update {update} caused error {context.error}')

async def main():
    TOKEN = "7963209844:AAE2WtF6Gdo2vJkj96erXmN7CItDK4dmS4c"
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_SKIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_skin)],
            ENTER_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_quantity)],
            CONFIRM_ANOTHER: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_another)]
        },
        fallbacks=[CommandHandler('start', start)],
    )

    app.add_handler(conv_handler)
    app.add_error_handler(error)

    print("ربات آماده اجراست...")
    await app.run_polling()

if name == "main":
    main()
