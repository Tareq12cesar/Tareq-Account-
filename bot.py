from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

TOKEN = "7933020801:AAHvfiIlfg5frqosVCgY1n1pUFElwQsr7B8"
ADMIN_ID = 6697070308  # آی‌دی ادمین تلگرام تو
CHANNEL_USERNAME = "@Mobile_Legend_IR"  # کانال برای جوین اجباری

# متغیر سراسری برای ذخیره آگهی‌های تایید شده
approved_ads = []

# اینجا متغیرها و دیکشنری قیمت‌ها و توضیحات اسکین‌ها (کد قبلی قیمت‌یابی را اینجا قرار بده)
skin_prices = {
    "Supreme": 350000,
    "Grand": 300000,
    "Exquisite": 150000,
    "Deluxe": None,  # قیمت دلخواه که در زمان محاسبه داده می‌شود
}

skin_explanations = {
    "Supreme": "✅ اسکین Supreme یکی از کمیاب‌ترین و گران‌ترین اسکین‌هاست.",
    "Grand": "✅ اسکین Grand از اسکین‌های ارزشمند بازی است.\n❌ توجه: اسکین‌های رایگان جزو این دسته نیستند.",
    "Exquisite": "✅ اسکین Exquisite دارای طراحی زیبا و خاص است.\n❌ اسکین‌های رایگان جزو این دسته محسوب نمی‌شوند.",
    "Deluxe": "✅ اسکین Deluxe بسته به تعداد، قیمت متفاوتی دارد.",
}

# مرحله ثبت آگهی (توالی سوال‌ها)
advertise_questions = [
    "لطفاً نام کالکشن خود را وارد کنید:",
    "اسکین‌های مهم کالکشن را بنویسید:",
    "توضیح کوتاهی درباره اکانت بدهید:",
    "قیمت فروش اکانت را به تومان وارد کنید:",
    "لطفاً ویدئوی اسکین‌ها را ارسال کنید:"
]

user_advertise_data = {}  # ذخیره موقت اطلاعات ثبت آگهی هر کاربر


async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["member", "creator", "administrator"]:
            return True
        else:
            return False
    except Exception:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [KeyboardButton("ثبت آگهی"), KeyboardButton("مشاهده آگهی‌ها")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"سلام {user.first_name}! خوش آمدی به ربات قیمت‌یاب و ثبت آگهی Mobile Legends.\n"
        "لطفاً یکی از گزینه‌ها را انتخاب کن:",
        reply_markup=reply_markup,
    )


# هندلر دکمه‌های منو با چک جوین اجباری
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update, context):
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")]])
        await update.message.reply_text(
            "⚠️ برای استفاده از ربات باید ابتدا عضو کانال شوید.",
            reply_markup=keyboard
        )
        return

    text = update.message.text
    if text == "ثبت آگهی":
        user_advertise_data[update.effective_user.id] = {
            "step": 0,
            "data": {}
        }
        await update.message.reply_text(advertise_questions[0])
    elif text == "مشاهده آگهی‌ها":
        await view_ads(update, context)
    else:
        await update.message.reply_text("لطفاً یکی از گزینه‌های منو را انتخاب کنید.")


# هندلر مرحله‌ای ثبت آگهی
async def advertise_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_advertise_data:
        # اگر کاربر در روند ثبت آگهی نیست، چیزی نده
        return

    step = user_advertise_data[user_id]["step"]
    data = user_advertise_data[user_id]["data"]

    if step < 4:  # مراحل متنی
        data_field = ["collection", "key_skins", "description", "price"][step]
        data[data_field] = update.message.text
        step += 1
        user_advertise_data[user_id]["step"] = step
        if step < 4:
            await update.message.reply_text(advertise_questions[step])
        else:
            await update.message.reply_text(advertise_questions[4])  # درخواست ویدئو
    else:
        # مرحله ویدئو
        if not update.message.video:
            await update.message.reply_text("لطفاً فقط ویدئو ارسال کنید.")
            return

        video_file_id = update.message.video.file_id
        data["video_file_id"] = video_file_id

        # آماده کردن کپشن برای ارسال به ادمین
        caption = (
            f"👤 کاربر: {user_id}\n"
            f"🎯 کالکشن: {data['collection']}\n"
            f"🌟 اسکین‌های مهم: {data['key_skins']}\n"
            f"📝 توضیح: {data['description']}\n"
            f"💰 قیمت فروش: {data['price']}\n"
        )

        # دکمه‌های تایید و رد برای ادمین
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ تایید", callback_data="ad_approve"),
                InlineKeyboardButton("❌ رد", callback_data="ad_reject"),
            ]
        ])

        # ارسال ویدئو و توضیحات به ادمین
        await context.bot.send_video(
            chat_id=ADMIN_ID,
            video=video_file_id,
            caption=caption,
            reply_markup=keyboard,
        )

        await update.message.reply_text("آگهی شما ارسال شد و در انتظار تایید ادمین است.")
        # حذف داده‌های موقت کاربر
        del user_advertise_data[user_id]


def extract_ad_info(caption):
    try:
        lines = caption.split('\n')
        info = {}
        for line in lines:
            if line.startswith("👤 کاربر:"):
                info['user_id'] = int(line.split(":")[1].strip())
            elif line.startswith("🎯 کالکشن:"):
                info['collection'] = line.split(":", 1)[1].strip()
            elif line.startswith("🌟 اسکین‌های مهم:"):
                info['key_skins'] = line.split(":", 1)[1].strip()
            elif line.startswith("📝 توضیح:"):
                info['description'] = line.split(":", 1)[1].strip()
            elif line.startswith("💰 قیمت فروش:"):
                info['price'] = line.split(":", 1)[1].strip()
        return info
    except Exception:
        return None


async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if user.id != ADMIN_ID:
        await query.edit_message_caption("⚠️ فقط ادمین می‌تواند این آگهی را تایید یا رد کند.")
        return

    callback_data = query.data
    message = query.message

    ad_info = extract_ad_info(message.caption)
    if not ad_info:
        await query.edit_message_caption("خطا در خواندن اطلاعات آگهی!")
        return

    user_id = ad_info.get('user_id')
    collection = ad_info.get('collection')
    key_skins = ad_info.get('key_skins')
    description = ad_info.get('description')
    price = ad_info.get('price')
    video_file_id = message.video.file_id

    if callback_data == "ad_approve":
        approved_ads.append({
            "user_id": user_id,
            "collection": collection,
            "key_skins": key_skins,
            "description": description,
            "price": price,
            "video_file_id": video_file_id,
        })
        await query.edit_message_caption("✅ آگهی تایید و ذخیره شد.")
        try:
            await context.bot.send_message(user_id, "آگهی شما تایید و منتشر شد.")
        except:
            pass

    elif callback_data == "ad_reject":
        await query.edit_message_caption("❌ آگهی رد شد.")
        try:
            await context.bot.send_message(user_id, "آگهی شما توسط ادمین رد شد.")
        except:
            pass


async def view_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not approved_ads:
        await context.bot.send_message(chat_id, "فعلاً آگهی تایید شده‌ای وجود ندارد.")
        return

    for ad in approved_ads:
        text = (
            f"🎯 کالکشن: {ad['collection']}\n"
            f"🌟 اسکین‌های مهم: {ad['key_skins']}\
