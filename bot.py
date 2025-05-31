from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes,
    CallbackQueryHandler, ConversationHandler
)

# حالت‌های مختلف برای ConversationHandler
COLLECTION, KEY_SKINS, DESCRIPTION, PRICE, VIDEO, ADMIN_REVIEW = range(6)

# شناسه ادمین خودت رو اینجا قرار بده
TOKEN = "7933020801:AAHvfiIlfg5frqosVCgY1n1pUFElwQsr7B8"
ADMIN_ID = 6697070308

# داده‌ها در حافظه (در حالت واقعی بهتر دیتابیس استفاده کنی)
pending_ads = []  # آگهی‌های در انتظار تایید (دیکشنری با اطلاعات کامل)
approved_ads = []  # آگهی‌های تایید شده (هر آگهی با یک id منحصر به فرد)

# متغیر موقت برای ذخیره داده کاربر در طول گفتگو
user_ad_data = {}

# قیمت اسکین‌ها (مثال)
skin_prices = {
    "Supreme": 1000000,
    "Grand": 700000,
    "Exquisite": 500000,
    "Deluxe": None  # قیمت بر اساس تعداد متغیر است
}

# توضیحات اسکین‌ها
skin_descriptions = {
    "Supreme": "✅ اسکین‌های Supreme نایاب و بسیار ارزشمند هستند.",
    "Grand": "✅ اسکین‌های Grand بسیار زیبا و کمیاب هستند.\n❌ اسکین‌های رایگان در این دسته قرار نمی‌گیرند.",
    "Exquisite": "✅ اسکین‌های Exquisite ارزش متوسطی دارند.\n❌ اسکین‌های رایگان در این دسته قرار نمی‌گیرند.",
    "Deluxe": "✅ اسکین‌های Deluxe قیمت متغیر دارند و بر اساس تعداد محاسبه می‌شوند."
}

# تابع شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("ثبت آگهی جدید", callback_data="start_ad")],
        [InlineKeyboardButton("مشاهده آگهی‌ها", callback_data="view_ads")],
    ]
    await update.message.reply_text("سلام! خوش آمدید.\nلطفا یکی از گزینه‌ها را انتخاب کنید:", 
                                    reply_markup=InlineKeyboardMarkup(keyboard))

# شروع فرایند ثبت آگهی
async def start_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_ad_data[query.from_user.id] = {}
    await query.message.reply_text("لطفا نام کالکشن خود را وارد کنید:")
    return COLLECTION

# دریافت نام کالکشن
async def collection_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_ad_data[user_id]['collection'] = update.message.text
    await update.message.reply_text("لطفا اسکین‌های کلیدی خود را وارد کنید (مثلاً: Layla, Alucard):")
    return KEY_SKINS

# دریافت اسکین‌های کلیدی
async def key_skins_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_ad_data[user_id]['key_skins'] = update.message.text
    await update.message.reply_text("لطفا توضیحاتی درباره اکانت خود بنویسید:")
    return DESCRIPTION

# دریافت توضیحات
async def description_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_ad_data[user_id]['description'] = update.message.text
    await update.message.reply_text("لطفا قیمت فروش اکانت را وارد کنید (به تومان):")
    return PRICE

# دریافت قیمت
async def price_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    price_text = update.message.text
    if not price_text.isdigit():
        await update.message.reply_text("لطفا فقط عدد وارد کنید.")
        return PRICE
    user_ad_data[user_id]['price'] = int(price_text)
    await update.message.reply_text("لطفا ویدیوی اسکین‌های خود را ارسال کنید:")
    return VIDEO

# دریافت ویدیو
async def video_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if update.message.video:
        user_ad_data[user_id]['video_file_id'] = update.message.video.file_id
        # افزودن به لیست انتظار تایید ادمین
        pending_ads.append({
            "user_id": user_id,
            **user_ad_data[user_id]
        })
        await update.message.reply_text("آگهی شما دریافت شد و پس از تایید ادمین منتشر خواهد شد.")
        user_ad_data.pop(user_id, None)
        # اطلاع ادمین
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"آگهی جدید برای تایید دریافت شد.\n"
                 f"کالکشن: {pending_ads[-1]['collection']}\n"
                 f"اسکین‌ها: {pending_ads[-1]['key_skins']}\n"
                 f"توضیح: {pending_ads[-1]['description']}\n"
                 f"قیمت: {pending_ads[-1]['price']} تومان",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("تایید", callback_data=f"approve_{len(pending_ads)-1}")],
                [InlineKeyboardButton("رد", callback_data=f"reject_{len(pending_ads)-1}")]
            ])
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("لطفا فقط ویدیو ارسال کنید.")
        return VIDEO

# نمایش آگهی‌ها به کاربران
async def view_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not approved_ads:
        await query.message.reply_text("هیچ آگهی تایید شده‌ای موجود نیست.")
        return
    for ad in approved_ads:
        text = (
            f"کد آگهی: #{ad['id']}\n"
            f"🎯 کالکشن: {ad['collection']}\n"
            f"🌟 اسکین‌های مهم: {ad['key_skins']}\n"
            f"📝 توضیح: {ad['description']}\n"
            f"💰 قیمت فروش: {ad['price']} تومان\n"
        )
        await context.bot.send_video(chat_id=query.message.chat_id, video=ad["video_file_id"], caption=text)

# مدیریت پاسخ ادمین برای تایید یا رد آگهی
async def admin_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("approve_"):
        index = int(data.split("_")[1])
        if 0 <= index < len(pending_ads):
            ad = pending_ads.pop(index)
            # اختصاص کد ترتیبی به آگهی
            ad_id = len(approved_ads) + 1
            ad["id"] = ad_id
            approved_ads.append(ad)

            await query.edit_message_text(f"آگهی شماره #{ad_id} تایید و منتشر شد.")
            try:
                await context.bot.send_message(ad["user_id"], f"آگهی شما تایید و منتشر شد.\nکد آگهی شما: #{ad_id}")
            except:
                pass

    elif data.startswith("reject_"):
        index = int(data.split("_")[1])
        if 0 <= index < len(pending_ads):
            ad = pending_ads.pop(index)
            await query.edit_message_text("آگهی رد شد.")
            try:
                await context.bot.send_message(ad["user_id"], "آگهی شما توسط ادمین رد شد.")
            except:
                pass

# لغو فرایند ثبت آگهی
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("فرایند ثبت آگهی لغو شد.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# --- بخش قیمت‌یاب اسکین‌ها (نمونه ساده) ---

async def price_bot_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Supreme", "Grand"],
        ["Exquisite", "Deluxe"],
        ["پایان"]
    ]
    await update.message.reply_text(
        "لطفا نوع اسکین خود را انتخاب کنید یا 'پایان' را برای مشاهده قیمت کل بزنید:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )
    context.user_data["total_price"] = 0
    context.user_data["selected_skins"] = []
    return 1

async def skin_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "پایان":
        total_price = context.user_data.get("total_price", 0)
        await update.message.reply_text(
            f"قیمت کل اسکین‌ها: {total_price} تومان\n"
            "قیمت بالا ارزش اکانت شماست\n"
            "برای ثبت آگهی تو کانال، قیمت فروش رو خودتون تعیین می‌کنید.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    if text not in skin_prices:
        await update.message.reply_text("لطفا یکی از گزینه‌های موجود را انتخاب کنید.")
        return 1

    # سوال تعداد اسکین‌ها
    context.user_data["current_skin"] = text
    await update.message.reply_text(f"تعداد اسکین‌های {text} را وارد کنید:")
    return 2

async def skin_count_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count_text = update.message.text
    if not count_text.isdigit():
        await update.message.reply_text("لطفا فقط عدد وارد کنید.")
        return 2
    count = int(count_text)
    skin_type = context.user_data.get("current_skin")

    # محاسبه قیمت
    if skin_type == "Deluxe":
        if count < 20:
            price = 25000 * count
        elif 20 <= count <= 40:
            price = 500000
        else:
            price = 700000
    else:
        price = skin_prices[skin_type] * count

    context.user_data["total_price"] += price
    context.user_data["selected_skins"].append((skin_type, count, price))

    # نمایش توضیحات
    desc = skin_descriptions.get(skin_type, "")
    await update.message.reply_text(desc)

    # بازگشت به انتخاب نوع اسکین
    keyboard = [
        ["Supreme", "Grand"],
        ["Exquisite", "Deluxe"],
        ["پایان"]
    ]
    await update.message.reply_text(
        "لطفا نوع اسکین بعدی را انتخاب کنید یا 'پایان' را بزنید:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )
    return 1

def main():
    app = ApplicationBuilder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

    # هندلر ثبت آگهی
    ad_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_ad, pattern="^start_ad$")],
        states={
            COLLECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, collection_received)],
            KEY_SKINS: [MessageHandler(filters.TEXT & ~filters.COMMAND, key_skins_received)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description_received)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price_received)],
            VIDEO: [MessageHandler(filters.VIDEO, video_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    # هندلر پاسخ ادمین
    admin_handler = CallbackQueryHandler(admin_review, pattern="^(approve_|reject_).+")

    # هندلر نمایش آگهی‌ها
    view_ads_handler = CallbackQueryHandler(view_ads, pattern="^view_ads$")

    # هندلر شروع
    start_handler = CommandHandler("start", start)

    # هندلر قیمت‌یاب اسکین
    price_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("price", price_bot_start)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, skin_type_handler)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, skin_count_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(start_handler)
    app.add_handler(ad_conv_handler)
    app.add_handler(admin_handler)
    app.add_handler(view_ads_handler)
    app.add_handler(price_conv_handler)

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
