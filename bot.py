from flask import Flask
import threading

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters

BOT_TOKEN = "7933020801:AAHaBEa43nikjSSNj_qKZ0L27r3ooJV6UDI"
CHANNEL_USERNAME = "@Mobile_Legend_ir"
ADMIN_ID = 6697070308  # آی‌دی عددی ادمین برای تایید آگهی‌ها

app = Flask(__name__)

# برای جلوگیری از بسته شدن برنامه
@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

PRICES = {
    'Supreme': 1200000,
    'Grand': 500000,
    'Exquisite': 300000
}

EXPLANATIONS = {
    'Supreme': "✅ این دسته شامل اسکین‌های لجند می‌باشد.\n\nچندتا اسکین از این دسته داری؟",
    'Grand': "✅ این دسته شامل اسکین‌های کوف، جوجوتسو، سوپر هیرو، استاروارز، ناروتو، ابیس و... می‌باشد.\n\n❌ توجه: اسکین‌های رایگان رو حساب نکنید.\n\nچندتا اسکین از این دسته داری؟",
    'Exquisite': "✅ این دسته شامل اسکین‌های کالکتور، لاکی باکس و کلادز می‌باشد.\n\n❌ توجه: اسکین‌های رایگان رو حساب نکنید.\n\nچندتا اسکین از این دسته داری؟",
    'Deluxe': "✅ این دسته شامل اسکین‌های زودیاک، لایتبورن، اپیک شاپ و... می‌باشد.\n\nچندتا اسکین از این دسته داری؟"
}

ads = []  # ذخیره آگهی‌ها در حافظه

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
        await query.edit_message_text("✅ عضویت شما تایید شد! /start رو بزن.")
    else:
        keyboard = [
            [InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("عضوشدم | فعال‌سازی", callback_data="check_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("⛔️ عضو کانال نیستی! روی دکمه زیر بزن و بعد دوباره تلاش کن.", reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(user_id, context):
        keyboard = [
            [InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("عضوشدم | فعال‌سازی", callback_data="check_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("لطفاً اول عضو کانال بشو:", reply_markup=reply_markup)
        return ConversationHandler.END
    keyboard = [[KeyboardButton("محاسبه قیمت"), KeyboardButton("ثبت آگهی"), KeyboardButton("مشاهده آگهی‌ها")]]
    await update.message.reply_text("سلام! یکی از گزینه‌های زیر رو انتخاب کن:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "محاسبه قیمت":
        context.user_data['skins'] = {}
        keyboard = [[KeyboardButton(skin)] for skin in ['Supreme', 'Grand', 'Exquisite', 'Deluxe']]
        await update.message.reply_text("نوع اسکین رو انتخاب کن:", reply_markup=ReplyKeyboardMarkup(keyboard + [['پایان']], resize_keyboard=True))
        return CHOOSE_SKIN
    elif text == "ثبت آگهی":
        await update.message.reply_text("نام کالکشن رو بفرست:")
        return COLLECT_NAME
    elif text == "مشاهده آگهی‌ها":
        if not ads:
            await update.message.reply_text("❌ هنوز هیچ آگهی‌ای ثبت نشده.")
        else:
            for i, ad in enumerate(ads, 1):
                await update.message.reply_text(f"📢 آگهی شماره {i}\n\n"
                                                f"🏷️ نام کالکشن: {ad['name']}\n"
                                                f"🔑 اسکین‌های مهم: {ad['key_skins']}\n"
                                                f"📝 توضیحات: {ad['description']}\n"
                                                f"💰 قیمت: {ad['price']}\n"
                                                f"📹 ویدیو:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("مشاهده ویدیو", url=ad['video_url'])]]))
    else:
        await update.message.reply_text("لطفاً یکی از گزینه‌ها رو انتخاب کن.")

async def choose_skin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == 'پایان':
        return await show_summary(update, context)
    if text not in PRICES and text != 'Deluxe':
        await update.message.reply_text("لطفاً نوع اسکین معتبر رو انتخاب کن.")
        return CHOOSE_SKIN
    context.user_data['current_skin'] = text
    await update.message.reply_text(EXPLANATIONS[text])
    return CONFIRM_END

async def confirm_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        skin = context.user_data['current_skin']
        context.user_data['skins'][skin] = context.user_data['skins'].get(skin, 0) + count
        await update.message.reply_text(f"✅ اسکین {skin} با تعداد {count} ثبت شد. ادامه بده یا 'پایان' رو بزن.")
        return CHOOSE_SKIN
    except:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کن.")
        return CONFIRM_END

async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    skins = context.user_data.get('skins', {})
    if not skins:
        await update.message.reply_text("هنوز اسکینی ثبت نکردی!")
        return ConversationHandler.END
    summary = ""
    total_price = 0
    for skin, count in skins.items():
        price = (count * 25000 if skin == 'Deluxe' and count < 20 else
                 500000 if skin == 'Deluxe' and 20 <= count <= 40 else
                 700000 if skin == 'Deluxe' and count > 40 else
                 PRICES[skin] * count)
        summary += f"{skin}: {count}\n"
        total_price += price
    await update.message.reply_text(f"✅ اسکین‌ها:\n{summary}\n💵 قیمت کل: {total_price:,} تومان\n\nقیمت بالا ارزش اکانت شماست.\nبرای ثبت آگهی، قیمت رو خودتون مشخص کنید.")
    await update.message.reply_text("برای شروع دوباره /start رو بزن.")
    return ConversationHandler.END

async def collect_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad'] = {'name': update.message.text}
    await update.message.reply_text("اسکین‌های مهم رو بنویس:")
    return KEY_SKINS

async def key_skins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad']['key_skins'] = update.message.text
    await update.message.reply_text("توضیحات اکانت رو بنویس:")
    return DESCRIPTION

async def description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad']['description'] = update.message.text
    await update.message.reply_text("قیمت مدنظر رو بنویس:")
    return PRICE

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad']['price'] = update.message.text
    await update.message.reply_text("حالا لینک ویدیوی اسکین‌ها رو بفرست (آپلود کن ویدیو رو):")
    return VIDEO

async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.video.get_file()
    file_url = file.file_path
    ad = context.user_data['ad']
    ad['video_url'] = file_url
    ad['user_id'] = update.effective_user.id
    ad['approved'] = False
    ad['index'] = len(ads) + 1
    ads.append(ad)
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"📢 درخواست آگهی جدید:\n\n"
                                                          f"🏷️ نام: {ad['name']}\n"
                                                          f"🔑 اسکین‌های مهم: {ad['key_skins']}\n"
                                                          f"📝 توضیحات: {ad['description']}\n"
                                                          f"💰 قیمت: {ad['price']}\n\n"
                                                          f"/approve_{ad['index']} تایید\n"
                                                          f"/reject_{ad['index']} رد")
    await update.message.reply_text("آگهی شما برای بررسی به ادمین ارسال شد. ✅")
    return ConversationHandler.END

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = int(update.message.text.split("_")[1]) - 1
    if 0 <= index < len(ads):
        ads[index]['approved'] = True
        await update.message.reply_text(f"✅ آگهی شماره {index + 1} تایید شد.")
    else:
        await update.message.reply_text("❌ آگهی پیدا نشد.")

async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = int(update.message.text.split("_")[1]) - 1
    if 0 <= index < len(ads):
        user_id = ads[index]['user_id']
        ads.pop(index)
        await context.bot.send_message(chat_id=user_id, text="❌ آگهی شما تایید نشد.")
        await update.message.reply_text("✅ آگهی رد شد و به کاربر اطلاع داده شد.")
    else:
        await update.message.reply_text("❌ آگهی پیدا نشد.")

app_tele = ApplicationBuilder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
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

app_tele.add_handler(conv_handler)
app_tele.add_handler(CallbackQueryHandler(check_membership_button, pattern="check_membership"))
app_tele.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app_tele.add_handler(CommandHandler("approve", approve))
app_tele.add_handler(CommandHandler("reject", reject))

app_tele.run_polling()
