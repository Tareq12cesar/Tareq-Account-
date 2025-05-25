import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# مقادیر
CHANNEL_USERNAME = "@Mobile_Legend_Persian"  # آیدی کانالت رو اینجا بذار
PRICES = {
    'لجند': 1200000,
    'کوف': 500000,
    'انیمه ایی': 500000,
    'کالکتور': 300000
}

# وضعیت گفتگو
CHOOSE_SKIN, ENTER_QUANTITY = range(2)

# ذخیره موقتی اطلاعات کاربر
user_data = {}

# بررسی عضویت کاربر در کانال
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
        await update.message.reply_text(
            f"لطفاً برای استفاده از ربات اول عضو کانال Mobile_Legend_Persian بشو و بعد دکمه /start رو بزن."
        )
        return ConversationHandler.END

    keyboard = [[KeyboardButton(skin)] for skin in PRICES.keys()]
    await update.message.reply_text(
        "سلام! لطفاً نوع اسکینت رو انتخاب کن:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSE_SKIN

# انتخاب نوع اسکین
async def choose_skin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    skin = update.message.text
    if skin not in PRICES:
        await update.message.reply_text("لطفاً یکی از گزینه‌ها رو انتخاب کن.")
        return CHOOSE_SKIN

    context.user_data['skin'] = skin
    await update.message.reply_text(f"چند تا اسکین {skin} داری؟")
    return ENTER_QUANTITY

# وارد کردن تعداد اسکین
async def enter_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        skin = context.user_data['skin']
        price = PRICES[skin] * count
        await update.message.reply_text(f"جمع کل شما: {price:,} تومان\nبرای محاسبه جدید، /start رو بزن.")
    except:
        await update.message.reply_text("لطفاً عدد معتبر وارد کن.")
        return ENTER_QUANTITY

    return ConversationHandler.END

# هندلرهای خطا
async def error(update, context):
    logging.warning(f'Update {update} caused error {context.error}')

# اجرای ربات
async def main():
    TOKEN = " 7878818515:AAG5YA_Yu4oEMNLdwZ_nHEGTb-KOPe82NyM "
    app = ApplicationBuilder().token("7878818515:AAG5YA_Yu4oEMNLdwZ_nHEGTb-KOPe82NyM").build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_SKIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_skin)],
            ENTER_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_quantity)]
        },
        fallbacks=[CommandHandler('start', start)],
    )

    app.add_handler(conv_handler)
    app.add_error_handler(error)

    print("ربات آماده اجراست...")
    await app.run_polling()

import asyncio

if __name__ == "__main__":
    asyncio.run(main())
