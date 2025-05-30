from flask import Flask
import threading
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters

# ===================== Flask Webhook ============================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

# =================== Telegram Bot Logic ==========================
TOKEN = "7933020801:AAHaBEa43nikjSSNj_qKZ0L27r3ooJV6UDI"
CHANNEL_USERNAME = "@Mobile_Legend_IR"
ADMIN_ID = 6697070308  # 👈 آیدی عددی ادمین رو اینجا بذار

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

CHOOSE_SKIN, CONFIRM_END, COLLECT_NAME, COLLECT_KEY_SKINS, COLLECT_DESC, COLLECT_PRICE, COLLECT_VIDEO = range(7)

ads = []  # آگهی‌های تاییدشده اینجا ذخیره میشن

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
        await query.edit_message_text("✅ عضویت شما تایید شد! حالا می‌تونی از ربات استفاده کنی.\nبرای شروع /start رو بزن.")
    else:
        keyboard = [
            [InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("عضوشدم | فعال‌سازی", callback_data="check_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("⛔️ هنوز عضو کانال نشدی!\nروی دکمه زیر بزن و دوباره تلاش کن.", reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(user_id, context):
        keyboard = [
            [InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("عضوشدم | فعال‌سازی", callback_data="check_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("برای استفاده از ربات لطفاً عضو کانال زیر شوید:", reply_markup=reply_markup)
        return ConversationHandler.END

    buttons = [
        [KeyboardButton("💎 محاسبه قیمت اسکین")],
        [KeyboardButton("➕ ثبت آگهی")],
        [KeyboardButton("📋 مشاهده آگهی‌ها")]
    ]
    await update.message.reply_text("سلام! یکی از گزینه‌ها رو انتخاب کن:", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return ConversationHandler.END

# ===================== محاسبه قیمت =======================
async def price_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['skins'] = {}
    keyboard = [[KeyboardButton(skin)] for skin in ['Supreme', 'Grand', 'Exquisite', 'Deluxe']]
    await update.message.reply_text("نوع اسکین رو انتخاب کن:", reply_markup=ReplyKeyboardMarkup(keyboard + [['پایان']], resize_keyboard=True))
    return CHOOSE_SKIN

async def choose_skin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == 'پایان':
        return await show_summary(update, context)
    if text not in PRICES and text != 'Deluxe':
        await update.message.reply_text("لطفاً یکی از اسکین‌ها یا 'پایان' رو انتخاب کن.")
        return CHOOSE_SKIN
    context.user_data['current_skin'] = text
    await update.message.reply_text(EXPLANATIONS[text])
    return CONFIRM_END

async def confirm_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        skin = context.user_data['current_skin']
        context.user_data['skins'][skin] = context.user_data['skins'].get(skin, 0) + count
        await update.message.reply_text(f"✅ اسکین {skin} با تعداد {count} ثبت شد.")
        return await price_entry(update, context)
    except:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کن.")
        return CONFIRM_END

async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    skins = context.user_data.get('skins', {})
    if not skins:
        await update.message.reply_text("هیچ اسکینی انتخاب نکردی!")
        return ConversationHandler.END

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

    await update.message.reply_text(f"✅ اسکین‌هایی که انتخاب کردی:\n{summary}\nقیمت کل: {total_price:,} تومان\n\nقیمت بالا ارزش اکانت شماست\nبرای ثبت آگهی تو کانال، قیمت فروش رو خودتون تعیین می‌کنید.")
    return ConversationHandler.END

# ===================== آگهی‌ها ===========================
async def submit_ad_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("نام کالکشن رو وارد کن:")
    return COLLECT_NAME

async def collect_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad'] = {'user_id': update.effective_user.id}
    context.user_data['ad']['collection_name'] = update.message.text
    await update.message.reply_text("اسکین‌های کلیدی رو وارد کن:")
    return COLLECT_KEY_SKINS

async def collect_key_skins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad']['key_skins'] = update.message.text
    await update.message.reply_text("توضیحات اکانت رو بنویس:")
    return COLLECT_DESC

async def collect_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad']['description'] = update.message.text
    await update.message.reply_text("قیمت پیشنهادی فروش رو بنویس:")
    return COLLECT_PRICE

async def collect_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad']['price'] = update.message.text
    await update.message.reply_text("ویدیوی اسکین‌ها رو ارسال کن (تا ۲۰ مگابایت):")
    return COLLECT_VIDEO

async def collect_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video
    if not video:
        await update.message.reply_text("لطفاً ویدیو بفرست.")
        return COLLECT_VIDEO
    context.user_data['ad']['video_file_id'] = video.file_id
    ad = context.user_data['ad']
    context.user_data.pop('ad', None)
    await context.bot.send_video(
        chat_id=ADMIN_ID,
        video=ad['video_file_id'],
        caption=f"📢 آگهی جدید برای تایید\n\n👤 یوزر: {ad['user_id']}\n\nکالکشن: {ad['collection_name']}\nاسکین‌های کلیدی: {ad['key_skins']}\nتوضیحات: {ad['description']}\nقیمت: {ad['price']}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ تایید", callback_data=f"approve|{ad['user_id']}|{ad['collection_name']}|{ad['key_skins']}|{ad['description']}|{ad['price']}|{ad['video_file_id']}")]
        ])
    )
    await update.message.reply_text("✅ آگهی برای تایید ادمین ارسال شد.")
    return ConversationHandler.END

async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split('|')
    _, user_id, collection_name, key_skins, description, price, video_id = data
    ads.append({
        'collection_name': collection_name,
        'key_skins': key_skins,
        'description': description,
        'price': price,
        'video_file_id': video_id
    })
    await context.bot.send_message(chat_id=user_id, text="✅ آگهی شما تایید شد و در لیست قرار گرفت.")
    await query.edit_message_caption(caption="✅ آگهی تایید شد و به لیست اضافه شد.")

async def view_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ads:
        await update.message.reply_text("❌ هنوز آگهی‌ای ثبت نشده.")
        return
    for ad in ads:
        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=ad['video_file_id'],
            caption=f"کالکشن: {ad['collection_name']}\nاسکین‌های کلیدی: {ad['key_skins']}\nتوضیحات: {ad['description']}\nقیمت: {ad['price']}"
        )

# ==================== Application ==========================
app = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()

app.add_handler(CallbackQueryHandler(check_membership_button, pattern="check_membership"))
app.add_handler(CallbackQueryHandler(handle_approval, pattern="approve"))
app.add_handler(ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSE_SKIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_skin)],
        CONFIRM_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_end)]
    },
    fallbacks=[CommandHandler("start", start)]
))
app.add_handler(MessageHandler(filters.Regex("💎 محاسبه قیمت اسکین"), price_entry))
app.add_handler(MessageHandler(filters.Regex("➕ ثبت آگهی"), submit_ad_start))
app.add_handler(MessageHandler(filters.Regex("📋 مشاهده آگهی‌ها"), view_ads))
app.add_handler(ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("➕ ثبت آگهی"), submit_ad_start)],
    states={
        COLLECT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_name)],
        COLLECT_KEY_SKINS: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_key_skins)],
        COLLECT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_desc)],
        COLLECT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_price)],
        COLLECT_VIDEO: [MessageHandler(filters.VIDEO, collect_video)]
    },
    fallbacks=[CommandHandler("start", start)]
))

app.run_polling()
