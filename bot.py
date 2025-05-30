from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)
BOT_TOKEN = "7933020801:AAHaBEa43nikjSSNj_qKZ0L27r3ooJV6UDI"
CHANNEL_USERNAME = "@Mobile_Legend_IR"
ADMIN_ID = 6697070308  # ادمین ربات را اینجا قرار بده

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

# حالت‌های conversation برای محاسبه قیمت
CHOOSE_SKIN, CONFIRM_END = range(2)

# حالت‌های conversation برای ثبت آگهی
(ASK_COLLECTION, ASK_TOTAL_SKINS, ASK_IMPORTANT_SKINS, ASK_DESCRIPTION,
 ASK_PRICE, ASK_VIDEO, CONFIRM_AD) = range(100, 107)

# حالت‌های مشاهده آگهی (فعلاً نیازی نیست conversation)

# ---------------------------------
# توابع چک عضویت

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
            "برای ادامه /start رو بزن."
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

# ---------------------------------
# منوی اصلی

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

    keyboard = [
        [KeyboardButton("محاسبه قیمت اسکین")],
        [KeyboardButton("ثبت آگهی فروش")],
        [KeyboardButton("مشاهده آگهی‌ها")]
    ]
    await update.message.reply_text(
        "سلام! لطفاً یکی از گزینه‌ها را انتخاب کن:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return 999  # حالت انتخاب منو

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "محاسبه قیمت اسکین":
        # پاکسازی داده‌های قبلی برای محاسبه قیمت
        context.user_data['skins'] = {}
        keyboard = [[KeyboardButton(skin)] for skin in ['Supreme', 'Grand', 'Exquisite', 'Deluxe']]
        await update.message.reply_text(
            "لطفاً نوع اسکینت رو انتخاب کن.",
            reply_markup=ReplyKeyboardMarkup(keyboard + [['پایان']], one_time_keyboard=False, resize_keyboard=True)
        )
        return CHOOSE_SKIN

    elif text == "ثبت آگهی فروش":
        await update.message.reply_text("لطفاً کالکشن اکانتت رو وارد کن:")
        return ASK_COLLECTION

    elif text == "مشاهده آگهی‌ها":
        ads = context.bot_data.get('ads', [])
        if not ads:
            await update.message.reply_text("فعلاً هیچ آگهی‌ای ثبت نشده.")
        else:
            msg = "آگهی‌های ثبت شده:\n\n"
            for i, ad in enumerate(ads, 1):
                msg += (f"آگهی {i}:\n"
                        f"کالکشن: {ad['collection']}\n"
                        f"تعداد اسکین‌ها: {ad['total_skins']}\n"
                        f"اسکین‌های مهم: {ad['important_skins']}\n"
                        f"توضیح: {ad['description']}\n"
                        f"قیمت فروش: {ad['price']}\n"
                        "-------------------------\n")
            await update.message.reply_text(msg)
        return ConversationHandler.END

    else:
        await update.message.reply_text("لطفاً یکی از گزینه‌های موجود را انتخاب کن.")
        return 999

# ---------------------------------
# بخش محاسبه قیمت

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

# ---------------------------------
# بخش ثبت آگهی

async def ask_collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ad'] = {}
    context.user_data['ad']['user_id'] = update.effective_user.id
    context.user_data['ad']['username'] = update.effective_user.username or "ندارد"

    collection = update.message.text
    if 'collection' not in context.user_data['ad']:
        context.user_data['ad']['collection'] = collection
        await update.message.reply_text("تعداد کل اسکین‌های اکانت رو وارد کن:")
        return ASK_TOTAL_SKINS

async def ask_total_skins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        total_skins = int(update.message.text)
        context.user_data['ad']['total_skins'] = total_skins
        await update.message.reply_text("تعداد اسکین‌های مهم اکانت رو وارد کن:")
        return ASK_IMPORTANT_SKINS
    except:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کن:")
        return ASK_TOTAL_SKINS

async def ask_important_skins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        important_skins = int(update.message.text)
        context.user_data['ad']['important_skins'] = important_skins
        await update.message.reply_text("یک توضیح کوتاه درباره اکانت بده:")
        return ASK_DESCRIPTION
    except:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کن:")
        return ASK_IMPORTANT_SKINS

async def ask_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text
    context.user_data['ad']['description'] = description
    await update.message.reply_text("قیمت فروش
