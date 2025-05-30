import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InputMediaVideo
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# --- تنظیمات اولیه ---
BOT_TOKEN = "7933020801:AAHaBEa43nikjSSNj_qKZ0L27r3ooJV6UDI"
CHANNEL_USERNAME = "@Mobile_Legend_ir"
ADMIN_ID = 6697070308  # شناسه عددی ادمین

# --- تنظیمات لاگ ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- قیمت اسکین‌ها ---
PRICES = {
    'Supreme': 1200000,
    'Grand': 500000,
    'Exquisite': 300000
}

EXPLANATIONS = {
    'Supreme': "✅ این دسته شامل اسکین‌های لجند می‌باشد.\n\nچندتا اسکین از این دسته داری؟",
    'Grand': "✅ این دسته شامل اسکین‌های کوف، جوجوتسو، سوپر هیرو، استاروارز، ناروتو، ابیس و... می‌باشد.\n\n❌ توجه داشته باشید اسکین‌های رایگان این دسته مثل کارینا، تاموز، فلورین، راجر و... رو حساب نکنید.\n\nچندتا اسکین از این دسته داری؟",
    'Exquisite': "✅ این دسته شامل اسکین‌های کالکتور، لاکی باکس و کلادز می‌باشد.\n\n❌ توجه داشته باشید اسکین‌های رایگان این دسته مثل ناتالیا و... رو حساب نکنید.\n\nچندتا اسکین از این دسته داری؟",
    'Deluxe': "✅ این دسته شامل اسکین‌های زودیاک، لایتبورن، اپیک شاپ و... می‌باشد.\n\nچندتا اسکین از این دسته داری؟"
}

# --- مراحل مکالمه ---
(
    CHOOSE_SKIN,
    CONFIRM_END,
    ASK_COLLECTION,
    ASK_KEY_SKINS,
    ASK_DESCRIPTION,
    ASK_PRICE,
    ASK_VIDEO,
    WAITING_APPROVAL
) = range(8)

# --- لیست آگهی‌های تأییدشده ---
approved_ads = []

# --- بررسی عضویت کاربر در کانال ---
async def check_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# --- دکمه بررسی عضویت ---
async def check_membership_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if await check_membership(user_id, context):
        await query.edit_message_text(
            "✅ عضویت شما تأیید شد! حالا می‌تونی از ربات استفاده کنی.\n\nبعد از مطالعه، دکمه /start رو بزن و ادامه بده."
        )
    else:
        keyboard = [
            [InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("عضوشدم | فعال‌سازی", callback_data="check_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "⛔️ هنوز عضو کانال نشدی!\n\nلطفاً روی دکمه زیر کلیک کن و بعد دوباره دکمه 'عضوشدم | فعال‌سازی' رو بزن.",
            reply_markup=reply_markup
        )

# --- شروع مکالمه ---
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

# --- انتخاب نوع اسکین ---
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

# --- تأیید تعداد اسکین ---
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

# --- نمایش خلاصه و قیمت کل ---
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

    await update.message.reply_text(
        f"✅ اسکین‌هایی که انتخاب کردی:\n{summary}\nقیمت کل: {total_price:,} تومان\n\nقیمت بالا ارزش اکانت شماست.\nآیا مایل به ثبت آگهی هستید؟ (بله/خیر)"
    )

    return ASK_COLLECTION

# --- دریافت نام کالکشن ---
async def ask_collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text == 'بله':
        await update.message.reply_text("لطفاً نام کالکشن اکانت خود را وارد کنید:")
        return ASK_KEY_SKINS
    else:
        await update.message.reply_text("ممنون از استفاده از ربات! برای شروع دوباره /start را وارد کنید.")
        return ConversationHandler.END

# --- دریافت اسکین‌های کلیدی ---
async def ask_key_skins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['collection_name'] = update.message.text
    await update.message.reply_text("لطفاً اسکین‌های کلیدی اکانت خود را وارد کنید:")
    return ASK_DESCRIPTION

# --- دریافت توضیحات ---
async def ask_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['key_skins'] = update.message.text
    await update.message.reply_text("لطفاً توضیحاتی درباره اکانت خود وارد کنید:")
    return ASK_PRICE

# --- دریافت قیمت فروش ---
async def ask_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    await update.message.reply_text("لطفاً قیمت فروش اکانت خود را وارد کنید:")
    return ASK_VIDEO

# --- دریافت ویدیو ---
async def ask_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['price'] = update.message.text
    await update.message.reply_text("لطفاً ویدیویی از اسکین‌های اکانت خود ارسال کنید:")
    return WAITING_APPROVAL

# --- ارسال آگهی به ادمین برای تأیید ---
async def waiting_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video
    if not video:
        await update.message.reply_text("لطفاً یک ویدیو ارسال کنید.")
        return ASK_VIDEO

    context.user_data['video'] = video.file_id

    # ارسال آگهی به29
