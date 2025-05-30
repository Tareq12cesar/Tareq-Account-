from flask import Flask
import threading

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters

# تنظیمات اولیه
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

# تلگرام و داده‌ها
CHANNEL_USERNAME = "@Mobile_Legend_ir"
ADMIN_ID = 123456789  # آیدی عددی ادمین رو اینجا بزن

PRICES = {
    'Supreme': 1200000,
    'Grand': 500000,
    'Exquisite': 300000
}

EXPLANATIONS = {
    'Supreme': "✅ این دسته شامل اسکین‌های لجند می‌باشد.\n\nچندتا اسکین از این دسته داری؟",
    'Grand': "✅ این دسته شامل اسکین‌های کوف، جوجوتسو، سوپر هیرو، استاروارز، ناروتو، ابیس و... می‌باشد.\n\n❌ توجه: اسکین‌های رایگان مثل کارینا، تاموز، فلورین و راجر رو حساب نکنید.\n\nچندتا اسکین از این دسته داری؟",
    'Exquisite': "✅ این دسته شامل اسکین‌های کالکتور، لاکی باکس و کلادز می‌باشد.\n\n❌ توجه: اسکین‌های رایگان مثل ناتالیا رو حساب نکنید.\n\nچندتا اسکین از این دسته داری؟",
    'Deluxe': "✅ این دسته شامل اسکین‌های زودیاک، لایتبورن، اپیک شاپ و... می‌باشد.\n\nچندتا اسکین از این دسته داری؟"
}

CHOOSE_SKIN, CONFIRM_END, ASK_AD, ASK_COLLECTION, ASK_IMPORTANT, ASK_DESCRIPTION, ASK_PRICE, ASK_VIDEO = range(8)

# بررسی عضویت
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
        await query.edit_message_text("✅ عضویت شما تایید شد! حالا می‌تونی از ربات استفاده کنی.\n\n/start رو بزن و ادامه بده.")
    else:
        keyboard = [
            [InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("عضوشدم | فعال‌سازی", callback_data="check_membership")]
        ]
        await query.edit_message_text(
            "⛔️ هنوز عضو کانال نشدی! لطفاً روی دکمه زیر کلیک کن و بعد دکمه 'عضوشدم | فعال‌سازی' رو بزن.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(user_id, context):
        keyboard = [
            [InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("عضوشدم | فعال‌سازی", callback_data="check_membership")]
        ]
        await update.message.reply_text("برای استفاده از ربات لطفاً عضو کانال شوید:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

    context.user_data.clear()
    context.user_data['skins'] = {}

    keyboard = [[KeyboardButton(skin)] for skin in ['Supreme', 'Grand', 'Exquisite', 'Deluxe']]
    await update.message.reply_text(
        "سلام! نوع اسکینت رو انتخاب کن:",
        reply_markup=ReplyKeyboardMarkup(keyboard + [['پایان']], resize_keyboard=True)
    )
    return CHOOSE_SKIN

# انتخاب اسکین
async def choose_skin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == 'پایان':
        return await show_summary(update, context)

    if text not in PRICES and text != 'Deluxe':
        await update.message.reply_text("لطفاً یکی از اسکین‌های موجود یا گزینه 'پایان' رو انتخاب کن.")
        return CHOOSE_SKIN

    context.user_data['current_skin'] = text
    await update.message.reply_text(EXPLANATIONS[text])
    return CONFIRM_END

# گرفتن تعداد اسکین
async def confirm_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        skin = context.user_data['current_skin']
        context.user_data['skins'][skin] = context.user_data['skins'].get(skin, 0) + count

        await update.message.reply_text(
            f"✅ {count} اسکین به دسته {skin} اضافه شد! انتخاب بعدی یا 'پایان' رو بزن."
        )

        keyboard = [[KeyboardButton(skin)] for skin in ['Supreme', 'Grand', 'Exquisite', 'Deluxe']]
        await update.message.reply_text(
            "نوع اسکین بعدی رو انتخاب کن یا 'پایان' رو بزن:",
            reply_markup=ReplyKeyboardMarkup(keyboard + [['پایان']], resize_keyboard=True)
        )
        return CHOOSE_SKIN
    except:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کن.")
        return CONFIRM_END

# نمایش خلاصه و پرسیدن ثبت آگهی
async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    skins = context.user_data['skins']
    if not skins:
        await update.message.reply_text("هنوز اسکینی انتخاب نکردی!")
        return ConversationHandler.END

    summary = ""
    total_price = 0
    for skin, count in skins.items():
        price = PRICES[skin] * count if skin != 'Deluxe' else (count * 25000 if count < 20 else (500000 if count <= 40 else 700000))
        summary += f"{skin}: {count}\n"
        total_price += price

    context.user_data['total_price'] = total_price

    await update.message.reply_text(
        f"✅ خلاصه انتخاب‌ها:\n{summary}\nقیمت کل: {total_price:,} تومان\n\nقیمت بالا ارزش اکانت شماست.\nبرای ثبت آگهی، روی بله بزنید.",
        reply_markup=ReplyKeyboardMarkup([['بله', 'خیر']], resize_keyboard=True, one_time_keyboard=True)
    )
    return ASK_AD

# مراحل ثبت آگهی
async def ask_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == 'بله':
        await update.message.reply_text("✅ کالکشن اکانتت رو بنویس:")
        return ASK_COLLECTION
    else:
        await update.message.reply_text("باشه! برای شروع دوباره /start رو بزن.")
        return ConversationHandler.END

async def ask_collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['collection'] = update.message.text
    await update.message.reply_text("✅ تعداد اسکین‌ها و اسکین‌های مهمت رو بنویس:")
    return ASK_IMPORTANT

async def ask_important(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['important'] = update.message.text
    await update.message.reply_text("✅ توضیحات کوتاه (مثلاً اسم قهرمان‌ها، مدال‌ها و...) رو بنویس:")
    return ASK_DESCRIPTION

async def ask_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    await update.message.reply_text("✅ قیمت فروش اکانتت رو به تومان بنویس:")
    return ASK_PRICE

async def ask_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['sale_price'] = update.message.text
    await update.message.reply_text("✅ فیلم اسکین‌ها رو آپلود کن:")
    return ASK_VIDEO

async def ask_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.video:
        context.user_data['video_file_id'] = update.message.video.file_id

        ad_text = (
            f"📢 درخواست ثبت آگهی جدید:\n\n"
            f"👤 کاربر: {update.effective_user.first_name} ({update.effective_user.id})\n"
            f"💎 کالکشن: {context.user_data['collection']}\n"
            f"🎮 اسکین‌ها: {context.user_data['important']}\n"
            f"📝 توضیحات: {context.user_data['description']}\n"
            f"💰 قیمت فروش: {context.user_data['sale_price']} تومان\n"
            f"💸 قیمت تخمینی: {context.user_data['total_price']:,} تومان"
        )

        keyboard = [
            [InlineKeyboardButton("✅ تایید آگهی", callback_data=f"approve_{update.effective_user.id}"),
             InlineKeyboardButton("❌ رد آگهی", callback_data=f"reject_{update.effective_user.id}")]
        ]

        await context.bot.send_message(chat_id=ADMIN_ID, text=ad_text, reply_markup=InlineKeyboardMarkup(keyboard))
        await context.bot.send_video(chat_id=ADMIN_ID, video=context.user_data['video_file_id'])

        await update.message.reply_text("✅ درخواست ثبت آگهی شما برای تایید ارسال شد.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("لطفاً یک ویدئو آپلود کن.")
        return ASK_VIDEO

# بررسی تایید یا رد ادمین
async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = int(data.split('_')[1])

    if data.startswith('approve_'):
        await query.edit_message_text("✅ آگهی تایید شد و ذخیره شد.")
        await context.bot.send_message(chat_id=user_id, text="✅ آگهی شما تایید شد و در سیستم ثبت گردید.")
    elif data.startswith('reject_'):
        await query.edit_message_text("❌ آگهی رد شد.")
        await context.bot.send_message(chat_id=user_id, text="❌ آگهی شما رد شد. لطفاً دوباره اطلاعات رو وارد کن.")

# هندلرها
app_telegram = ApplicationBuilder().token("7933020801:AAHaBEa43nikjSSNj_qKZ0L27r3ooJV6UDI").build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSE_SKIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_skin)],
        CONFIRM_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_end)],
        ASK_AD: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_ad)],
        ASK_COLLECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_collection)],
        ASK_IMPORTANT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_important)],
        ASK_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_description)],
        ASK_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_price)],
        ASK_VIDEO: [MessageHandler(filters.VIDEO, ask_video)]
    },
    fallbacks=[CommandHandler("start", start)]
)

app_telegram.add_handler(conv_handler)
app_telegram.add_handler(CallbackQueryHandler(check_membership_button, pattern="check_membership"))
app_telegram.add_handler(CallbackQueryHandler(admin_decision, pattern="^(approve_|reject_).*"))

app_telegram.run_polling()
