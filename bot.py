from flask import Flask
import threading
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

CHANNEL_USERNAME = "@Mobile_Legend_ir"
ADMIN_ID = 6697070308
ads = []

PRICES = {
    'Supreme': 1200000,
    'Grand': 500000,
    'Exquisite': 300000
}

EXPLANATIONS = {
    'Supreme': "✅ این دسته شامل اسکین‌های لجند می‌باشد.\n\nچندتا اسکین از این دسته داری؟",
    'Grand': "✅ این دسته شامل اسکین‌های کوف، جوجوتسو، سوپر هیرو، استاروارز، ناروتو، ابیس و... می‌باشد.(از اسکین های پرایم فقط راجر رو اینجا وارد کنید و بقیه رو در قسمت Exquisite وارد کنید)\n\n❌ توجه داشته باشید اسکین‌های رایگان این دسته مثل کارینا، تاموز، فلورین، راجر و... رو حساب نکنید.\n\nچندتا اسکین از این دسته داری؟",
    'Exquisite': "✅ این دسته شامل اسکین‌های کالکتور، لاکی باکس و کلادز می‌باشد(اسکین های پرایم در این قسمت وارد کنید).\n\n❌ توجه داشته باشید اسکین‌های رایگان این دسته مثل ناتالیا و... رو حساب نکنید.\n\nچندتا اسکین از این دسته داری؟",
    'Deluxe': "✅ این دسته شامل اسکین‌های زودیاک، لایتبورن، اپیک شاپ و... می‌باشد.\n\nچندتا اسکین از این دسته داری؟"
}

CHOOSE_SKIN, CONFIRM_END, COLLECT_NAME, KEY_SKINS, DESCRIPTION, PRICE, VIDEO = range(7)

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
        await query.edit_message_text("✅ عضویت شما تایید شد! حالا می‌تونی از ربات استفاده کنی.\n\n/start رو بزن و شروع کن!")
    else:
        keyboard = [
            [InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("عضوشدم | فعال‌سازی", callback_data="check_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("⛔️ هنوز عضو کانال نشدی!\n\nروی دکمه زیر کلیک کن و بعد دوباره دکمه 'عضوشدم | فعال‌سازی' رو بزن.", reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(user_id, context):
        keyboard = [
            [InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("عضوشدم | فعال‌سازی", callback_data="check_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("برای استفاده از ربات لطفاً عضو کانال زیر شوید:", reply_markup=reply_markup)
        return

    keyboard = [
        [KeyboardButton("قیمت‌یاب"), KeyboardButton("ثبت آگهی"), KeyboardButton("مشاهده آگهی‌ها")]
    ]
    await update.message.reply_text("سلام! یکی از گزینه‌ها رو انتخاب کن:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "قیمت‌یاب":
        context.user_data['skins'] = {}
        keyboard = [[KeyboardButton(skin)] for skin in ['Supreme', 'Grand', 'Exquisite', 'Deluxe']]
        await update.message.reply_text("نوع اسکینت رو انتخاب کن:", reply_markup=ReplyKeyboardMarkup(keyboard + [['پایان']], resize_keyboard=True))
        return CHOOSE_SKIN
    elif text == "ثبت آگهی":
        await update.message.reply_text("نام کالکشن رو وارد کن:")
        return COLLECT_NAME
    elif text == "مشاهده آگهی‌ها":
        if not ads:
            await update.message.reply_text("هیچ آگهی تایید شده‌ای وجود ندارد.")
        else:
            for ad in ads:
                await update.message.reply_text(ad)
        return

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

async def confirm_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        skin = context.user_data['current_skin']
        context.user_data['skins'][skin] = context.user_data['skins'].get(skin, 0) + count
        await update.message.reply_text(f"✅ اسکین {skin} با تعداد {count} اضافه شد! ادامه بده یا 'پایان' رو بزن.")
        keyboard = [[KeyboardButton(skin)] for skin in ['Supreme', 'Grand', 'Exquisite', 'Deluxe']]
        await update.message.reply_text("یک اسکین دیگه انتخاب کن یا 'پایان' رو بزن:", reply_markup=ReplyKeyboardMarkup(keyboard + [['پایان']], resize_keyboard=True))
        return CHOOSE_SKIN
    except:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کن.")
        return CONFIRM_END

async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    skins = context.user_data.get('skins', {})
    if not skins:
        await update.message.reply_text("هنوز هیچ اسکینی انتخاب نکردی!")
        return
    summary = ""
    total_price = 0
    for skin, count in skins.items():
        if skin == 'Deluxe':
            if count < 20:
                price = count * 25000
            elif 20 <= count <= 40:
                price = 500000
            else:
                price = 700000
        else:
            price = PRICES[skin] * count
        summary += f"{skin}: {count}\n"
        total_price += price
    await update.message.reply_text(f"✅ اسکین‌هایی که انتخاب کردی:\n{summary}\nقیمت کل: {total_price:,} تومان\n\nقیمت بالا ارزش اکانت شماست\nبرای ثبت آگهی تو کانال، قیمت فروش رو خودتون تعیین می‌کنید")
    await update.message.reply_text("برای شروع دوباره /start رو بزن.")

async def collect_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad'] = {'name': update.message.text}
    await update.message.reply_text("اسکین‌های مهم رو وارد کن:")
    return KEY_SKINS

async def key_skins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad']['key_skins'] = update.message.text
    await update.message.reply_text("توضیحات مختصر یا توضیحات اکانت رو وارد کن:")
    return DESCRIPTION

async def description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad']['description'] = update.message.text
    await update.message.reply_text("قیمت پیشنهادی رو وارد کن (تومان):")
    return PRICE

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad']['price'] = update.message.text
    await update.message.reply_text("ویدیوی اسکین‌ها رو آپلود کن:")
    return VIDEO

async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = update.message.video.file_id
    context.user_data['ad']['video'] = file_id
    ad_text = f"📢 آگهی جدید:\n\n🔹 نام کالکشن: {context.user_data['ad']['name']}\n🔹 اسکین‌های مهم: {context.user_data['ad']['key_skins']}\n🔹 توضیحات: {context.user_data['ad']['description']}\n🔹 قیمت پیشنهادی: {context.user_data['ad']['price']} تومان"
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"🛡 آگهی جدید نیاز به تایید دارد:\n\n{ad_text}")
    await context.bot.send_video(chat_id=ADMIN_ID, video=file_id, caption="ویدیوی اسکین‌ها")
    await update.message.reply_text("✅ آگهی شما برای تایید ارسال شد. بعد از تایید، در بخش 'مشاهده آگهی‌ها' نمایش داده خواهد شد.")
    return ConversationHandler.END

app = ApplicationBuilder().token("7933020801:AAHaBEa43nikjSSNj_qKZ0L27r3ooJV6UDI").build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
    states={
        CHOOSE_SKIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_skin)],
        CONFIRM_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_end)],
        COLLECT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_name)],
        KEY_SKINS: [MessageHandler(filters.TEXT & ~filters.COMMAND, key_skins)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
        PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price)],
        VIDEO: [MessageHandler(filters.VIDEO, video)]
    },
    fallbacks=[CommandHandler("start", start)]
)

app.add_handler(conv_handler)
app.add_handler(CallbackQueryHandler(check_membership_button, pattern="check_membership"))
app.run_polling()
