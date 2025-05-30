from flask import Flask
import threading
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters

# --- اطلاعات مهم ---
BOT_TOKEN = "7933020801:AAHaBEa43nikjSSNj_qKZ0L27r3ooJV6UDI"
CHANNEL_USERNAME = "@Mobile_Legend_ir"
ADMIN_ID = 6697070308  # شناسه عددی تلگرام ادمین
# -------------------

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

# ---------- قیمت‌گذاری اسکین‌ها ----------
PRICES = {
    'Supreme': 1200000,
    'Grand': 500000,
    'Exquisite': 300000
}

EXPLANATIONS = {
    'Supreme': "✅ این دسته شامل اسکین‌های لجند می‌باشد.\n\nچندتا اسکین از این دسته داری؟",
    'Grand': "✅ این دسته شامل اسکین‌های کوف، جوجوتسو، سوپر هیرو، استاروارز، ناروتو، ابیس و... می‌باشد.\n❌ اسکین‌های رایگان مثل کارینا، تاموز، فلورین، راجر و... رو حساب نکنید.\n\nچندتا اسکین از این دسته داری؟",
    'Exquisite': "✅ این دسته شامل اسکین‌های کالکتور، لاکی باکس و کلادز می‌باشد(اسکین‌های پرایم رو هم اینجا وارد کنید).\n❌ اسکین‌های رایگان مثل ناتالیا و... رو حساب نکنید.\n\nچندتا اسکین از این دسته داری؟",
    'Deluxe': "✅ این دسته شامل اسکین‌های زودیاک، لایتبورن، اپیک شاپ و... می‌باشد.\n\nچندتا اسکین از این دسته داری؟"
}

CHOOSE_SKIN, CONFIRM_END, AD_COLLECT, AD_SKINS, AD_DESC, AD_PRICE, AD_VIDEO = range(7)
ads = []

# ---------- عضویت کانال ----------
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
        await query.edit_message_text("✅ عضویت تایید شد. /start رو بزن.")
    else:
        keyboard = [[InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
                    [InlineKeyboardButton("عضو شدم | فعال‌سازی", callback_data="check_membership")]]
        await query.edit_message_text("⛔️ هنوز عضو کانال نشدی!\nعضو شو و دکمه رو بزن.", reply_markup=InlineKeyboardMarkup(keyboard))

# ---------- استارت و قیمت‌گذاری ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(user_id, context):
        keyboard = [[InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
                    [InlineKeyboardButton("عضو شدم | فعال‌سازی", callback_data="check_membership")]]
        await update.message.reply_text("برای استفاده از ربات عضو کانال شو:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

    context.user_data['skins'] = {}
    buttons = [[KeyboardButton(skin)] for skin in ['Supreme', 'Grand', 'Exquisite', 'Deluxe']]
    await update.message.reply_text("نوع اسکینت رو انتخاب کن:", reply_markup=ReplyKeyboardMarkup(buttons + [['پایان']], resize_keyboard=True))
    return CHOOSE_SKIN

async def choose_skin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == 'پایان':
        return await show_summary(update, context)
    if text not in PRICES and text != 'Deluxe':
        await update.message.reply_text("گزینه معتبر بزن.")
        return CHOOSE_SKIN
    context.user_data['current_skin'] = text
    await update.message.reply_text(EXPLANATIONS[text])
    return CONFIRM_END

async def confirm_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        skin = context.user_data['current_skin']
        context.user_data['skins'][skin] = context.user_data['skins'].get(skin, 0) + count
        await update.message.reply_text(f"✅ {count} اسکین {skin} اضافه شد. ادامه بده یا پایان رو بزن.")
        return CHOOSE_SKIN
    except:
        await update.message.reply_text("عدد معتبر بزن.")
        return CONFIRM_END

async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    skins = context.user_data.get('skins', {})
    if not skins:
        await update.message.reply_text("هنوز هیچ اسکینی انتخاب نکردی!")
        return ConversationHandler.END
    summary, total = "", 0
    for skin, count in skins.items():
        if skin == 'Deluxe':
            price = count * 25000 if count < 20 else (500000 if count <= 40 else 700000)
        else:
            price = PRICES[skin] * count
        summary += f"{skin}: {count}\n"
        total += price
    await update.message.reply_text(
        f"✅ اسکین‌ها:\n{summary}\nقیمت کل: {total:,} تومان\n\nقیمت بالا ارزش اکانت شماست\nبرای ثبت آگهی، قیمت فروش رو خودتون تعیین کنید."
    )
    keyboard = [[InlineKeyboardButton("ثبت آگهی جدید", callback_data="new_ad")],
                [InlineKeyboardButton("مشاهده آگهی‌ها", callback_data="view_ads")]]
    await update.message.reply_text("انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

# ---------- آگهی‌ها ----------
async def new_ad_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("نام کالکشن رو وارد کن:")
    return AD_COLLECT

async def ad_collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad'] = {'collection': update.message.text}
    await update.message.reply_text("اسکین‌های مهم رو وارد کن:")
    return AD_SKINS

async def ad_skins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad']['key_skins'] = update.message.text
    await update.message.reply_text("توضیحات اکانت:")
    return AD_DESC

async def ad_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad']['description'] = update.message.text
    await update.message.reply_text("قیمت پیشنهادی:")
    return AD_PRICE

async def ad_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad']['price'] = update.message.text
    await update.message.reply_text("ویدیو اسکین‌هات رو بفرست:")
    return AD_VIDEO

async def ad_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad']['video'] = update.message.video.file_id
    ad = context.user_data['ad']
    ad['user_id'] = update.effective_user.id
    context.bot_data.setdefault('pending_ads', []).append(ad)
    await update.message.reply_text("✅ آگهی ارسال شد. در انتظار تایید ادمین.")
    await context.bot.send_message(ADMIN_ID, f"آگهی جدید:\nکالکشن: {ad['collection']}\nاسکین‌ها: {ad['key_skins']}\nتوضیحات: {ad['description']}\nقیمت: {ad['price']}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید", callback_data=f"approve_{len(context.bot_data['pending_ads'])-1}"), InlineKeyboardButton("رد", callback_data=f"reject_{len(context.bot_data['pending_ads'])-1}")]]))
    await context.bot.send_video(ADMIN_ID, ad['video'])
    return ConversationHandler.END

async def approve_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    idx = int(query.data.split("_")[1])
    ad = context.bot_data['pending_ads'].pop(idx)
    ads.append(ad)
    await query.message.reply_text("✅ آگهی تایید شد.")
    await context.bot.send_message(ad['user_id'], "✅ آگهی شما تایید شد و داخل ربات منتشر شد.")

async def reject_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    idx = int(query.data.split("_")[1])
    ad = context.bot_data['pending_ads'].pop(idx)
    await query.message.reply_text("❌ آگهی رد شد.")
    await context.bot.send_message(ad['user_id'], "❌ آگهی شما رد شد.")

async def view_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not ads:
        await query.message.reply_text("هیچ آگهی تاییدشده‌ای وجود نداره.")
    else:
        for ad in ads:
            await context.bot.send_message(query.message.chat_id, f"کالکشن: {ad['collection']}\nاسکین‌ها: {ad['key_skins']}\nتوضیحات: {ad['description']}\nقیمت: {ad['price']}")
            await context.bot.send_video(query.message.chat_id, ad['video'])

# ---------- هندلرها ----------
app = ApplicationBuilder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSE_SKIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_skin)],
        CONFIRM_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_end)],
        AD_COLLECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ad_collect)],
        AD_SKINS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ad_skins)],
        AD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, ad_desc)],
        AD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ad_price)],
        AD_VIDEO: [MessageHandler(filters.VIDEO, ad_video)],
    },
    fallbacks=[CommandHandler("start", start)]
)

app.add_handler(conv_handler)
app.add_handler(CallbackQueryHandler(check_membership_button, pattern="check_membership"))
app.add_handler(CallbackQueryHandler(new_ad_callback, pattern="new_ad"))
app.add_handler(CallbackQueryHandler(view_ads, pattern="view_ads"))
app.add_handler(CallbackQueryHandler(approve_ad, pattern="approve_"))
app.add_handler(CallbackQueryHandler(reject_ad, pattern="reject_"))

app.run_polling()
