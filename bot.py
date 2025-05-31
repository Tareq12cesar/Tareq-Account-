from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters

CHANNEL_USERNAME = "@Mobile_Legend_ir"

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

CHOOSE_SKIN, CONFIRM_END = range(2)

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
        await query.edit_message_text(
            "✅ عضویت شما تایید شد! حالا می‌تونی از ربات استفاده کنی.\n"
            "توجه: اسکین‌های رایگان مثل **کوف کارینا** و... رو حساب نکنید چون ارزش خاصی ندارن.\n\n"
            "بعد از مطالعه، دکمه /start رو بزن و ادامه بده."
        )
    else:
        keyboard = [
            [InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("عضوشدم | فعال‌سازی", callback_data="check_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"⛔️ هنوز عضو کانال نشدی!\n\nلطفاً روی دکمه زیر کلیک کن و بعد دوباره دکمه 'عضوشدم | فعال‌سازی' رو بزن.",
            reply_markup=reply_markup
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(user_id, context):
        keyboard = [
            [InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("عضوشدم | فعال‌سازی", callback_data="check_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "برای استفاده از ربات لطفاً عضو کانال زیر شوید:",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    context.user_data['skins'] = {}

    keyboard = [[KeyboardButton(skin)] for skin in ['Supreme', 'Grand', 'Exquisite', 'Deluxe']]
    await update.message.reply_text(
        "سلام! لطفاً نوع اسکینت رو انتخاب کن.",
        reply_markup=ReplyKeyboardMarkup(keyboard + [['پایان']], one_time_keyboard=False, resize_keyboard=True)
    )
    return CHOOSE_SKIN

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

        if skin in context.user_data['skins']:
            context.user_data['skins'][skin] += count
        else:
            context.user_data['skins'][skin] = count

        await update.message.reply_text(
            f"✅ اسکین {skin} با تعداد {count} اضافه شد! برای ادامه انتخاب کن یا 'پایان' رو بزن."
        )

        keyboard = [[KeyboardButton(skin)] for skin in ['Supreme', 'Grand', 'Exquisite', 'Deluxe']]
        await update.message.reply_text(
            "یک اسکین دیگه انتخاب کن یا 'پایان' رو بزن:",
            reply_markup=ReplyKeyboardMarkup(keyboard + [['پایان']], one_time_keyboard=False, resize_keyboard=True)
        )

        return CHOOSE_SKIN
    except:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کن.")
        return CONFIRM_END

async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    skins = context.user_data.get('skins', {})
    if not skins:
        await update.message.reply_text("هنوز هیچ اسکینی انتخاب نکردی!")
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

    keyboard = [[InlineKeyboardButton("برای آگهی کردن کلیک کنید", url="https://t.me/Tareq_Cesar_Trade")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ اسکین‌هایی که انتخاب کردی:\n{summary}\nقیمت کل: {total_price:,} تومان\n\nقیمت بالا ارزش اکانت شماست\nبرای ثبت آگهی تو کانال، قیمت فروش رو خودتون تعیین می‌کنید",
        reply_markup=reply_markup
    )

    await update.message.reply_text("برای شروع دوباره /start رو بزن.")
    return ConversationHandler.END

app = ApplicationBuilder().token("7933020801:AAHvfiIlfg5frqosVCgY1n1pUFElwQsr7B8").build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSE_SKIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_skin)],
        CONFIRM_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_end)]
    },
    fallbacks=[CommandHandler("start", start)]
)

app.add_handler(conv_handler)
app.add_handler(CallbackQueryHandler(check_membership_button, pattern="check_membership"))

# مراحل ثبت آگهی
COLLECTION, KEY_SKINS, DESCRIPTION, PRICE, VIDEO = range(5)

approved_ads = []
# فرض کن approved_ads اینجا تعریف شده:
approved_ads = [
    {
        'collection': 'کالکشن اول',
        'key_skins': 'اسکین A, اسکین B',
        'description': 'اکانت خوب و نایاب',
        'price': 1500000,
        'video_file_id': 'ABC123xyz...'  # نمونه file_id ویدیو
    },
    # آگهی‌های دیگر...
]

# 1. تابع نمایش آگهی‌ها:
async def view_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not approved_ads:
        await update.message.reply_text("فعلاً هیچ آگهی تایید شده‌ای وجود ندارد.")
        return

    for ad in approved_ads:
        text = (
            f"🎯 کالکشن: {ad['collection']}\n"
            f"🌟 اسکین‌های مهم: {ad['key_skins']}\n"
            f"📝 توضیح: {ad['description']}\n"
            f"💰 قیمت فروش: {ad['price']:,} تومان"
        )
        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=ad['video_file_id'],
            caption=text
        )

# 2. اضافه کردن هندلر:
app.add_handler(CommandHandler("view_ads", view_ads))

# 3. ادامه کد اصلی ربات...
ADMIN_ID = 6697070308

async def advertise_start(update, context):
    await update.message.reply_text("مرحله 1: لطفاً نام کالکشن اکانت خود را وارد کنید:")
    return COLLECTION

async def get_collection(update, context):
    context.user_data['ad_collection'] = update.message.text
    await update.message.reply_text("مرحله 2: تعداد و اسکین‌های مهم را وارد کنید:")
    return KEY_SKINS

async def get_key_skins(update, context):
    context.user_data['ad_key_skins'] = update.message.text
    await update.message.reply_text("مرحله 3: یک توضیح مختصر درباره اکانت بدهید:")
    return DESCRIPTION

async def get_description(update, context):
    context.user_data['ad_description'] = update.message.text
    await update.message.reply_text("مرحله 4: قیمت فروش را وارد کنید (به تومان):")
    return PRICE

async def get_price(update, context):
    price_text = update.message.text
    if not price_text.isdigit():
        await update.message.reply_text("لطفاً فقط عدد وارد کنید.")
        return PRICE
    context.user_data['ad_price'] = int(price_text)
    await update.message.reply_text("مرحله 5: لطفاً ویدیو اکانت را ارسال کنید (حداکثر 50 مگابایت):")
    return VIDEO

async def get_video(update, context):
    if not update.message.video:
        await update.message.reply_text("لطفاً فقط ویدیو ارسال کنید.")
        return VIDEO
    video_file_id = update.message.video.file_id
    context.user_data['ad_video'] = video_file_id

    user = update.effective_user
    ad_text = (
        f"🆕 آگهی جدید از کاربر: {user.full_name} (id: {user.id})\n\n"
        f"🎯 کالکشن: {context.user_data['ad_collection']}\n"
        f"🌟 اسکین‌های مهم: {context.user_data['ad_key_skins']}\n"
        f"📝 توضیح: {context.user_data['ad_description']}\n"
        f"💰 قیمت فروش: {context.user_data['ad_price']:,} تومان\n"
        f"\nبرای تایید یا رد، یکی از دکمه‌ها را بزنید:"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ تایید", callback_data="ad_approve"),
            InlineKeyboardButton("❌ رد", callback_data="ad_reject")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_video(
        chat_id=ADMIN_ID,
        video=video_file_id,
        caption=ad_text,
        reply_markup=reply_markup
    )

    await update.message.reply_text("آگهی شما به ادمین ارسال شد و پس از تایید نمایش داده خواهد شد.\nبرای شروع دوباره /start را بزنید.")
    return ConversationHandler.END
import re

def extract_ad_info(caption):
    data = {}
    lines = caption.split('\n')

    for line in lines:
        if line.startswith("🆕 آگهی جدید از کاربر:"):
            match = re.search(r"کاربر: (.+) id: (\d+)", line)
            if match:
                data['user_name'] = match.group(1).strip()
                data['user_id'] = int(match.group(2).strip())
        elif line.startswith("🎯 کالکشن:"):
            data['collection'] = line.split("🎯 کالکشن:")[1].strip()
        elif line.startswith("🌟 اسکین‌های مهم:"):
            data['key_skins'] = line.split("🌟 اسکین‌های مهم:")[1].strip()
        elif line.startswith("📝 توضیح:"):
            data['description'] = line.split("📝 توضیح:")[1].strip()
        elif line.startswith("💰 قیمت فروش:"):
            price_text = line.split("💰 قیمت فروش:")[1].strip().replace(" تومان", "").replace(",", "")
            data['price'] = int(price_text)
    return data

async def admin_callback_handler(update, context):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    if user.id != ADMIN_ID:
        await query.edit_message_caption("⚠️ فقط ادمین می‌تواند این آگهی را تایید یا رد کند.")
        return

    callback_data = query.data
    message = query.message

    # استخراج اطلاعات آگهی از کپشن پیام
    ad_info = extract_ad_info(message.caption)
    if not ad_info:
        await query.edit_message_caption("خطا در خواندن اطلاعات آگهی!")
        return

    user_id = ad_info.get('user_id')
    collection = ad_info.get('collection')
    key_skins = ad_info.get('key_skins')
    description = ad_info.get('description')
    price = ad_info.get('price')
    
    if callback_data == "ad_approve":
        # ذخیره آگهی در لیست تایید شده‌ها
        approved_ads.append({
            'user_id': user_id,
            'collection': collection,
            'key_skins': key_skins,
            'description': description,
            'price': price,
            'video_file_id': message.video.file_id
        })
        await query.edit_message_caption("✅ آگهی تایید و ذخیره شد.")
        # اطلاع به کاربر درباره تایید آگهی
        try:
            await context.bot.send_message(user_id, "آگهی شما تایید و منتشر شد.")
        except:
            pass

    elif data == "ad_reject":
        await query.edit_message_caption("❌ آگهی رد شد.")
        try:
            await context.bot.send_message(user_id, "آگهی شما توسط ادمین رد شد.")
        except:
            pass

advertise_conv = ConversationHandler(
    entry_points=[CommandHandler("advertise", advertise_start)],
    states={
        COLLECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_collection)],
        KEY_SKINS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_key_skins)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
        PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
        VIDEO: [MessageHandler(filters.VIDEO | filters.Document.VIDEO, get_video)],
    },
    fallbacks=[],
)

app.add_handler(advertise_conv)
app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="ad_"))

app.run_polling()
