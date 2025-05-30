import telebot
from telebot import types

# --- اطلاعات مهم ---
API_TOKEN = '7933020801:AAHaBEa43nikjSSNj_qKZ0L27r3ooJV6UDI'
ADMIN_ID = 6697070308  # آیدی عددی ادمین

bot = telebot.TeleBot(API_TOKEN)

ads = []  # لیست آگهی‌ها
user_ads = {}  # داده‌های موقت کاربران

# --- شروع ربات ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('ثبت آگهی', 'مشاهده آگهی‌ها')
    bot.send_message(message.chat.id, 'سلام! به ربات ثبت آگهی خوش اومدی. یکی از گزینه‌ها رو انتخاب کن:', reply_markup=markup)

# --- ثبت آگهی ---
@bot.message_handler(func=lambda m: m.text == 'ثبت آگهی')
def submit_ad(message):
    bot.send_message(message.chat.id, 'نام کالکشن خود را وارد کنید:')
    bot.register_next_step_handler(message, get_collection_name)

def get_collection_name(message):
    user_ads[message.chat.id] = {'collection': message.text}
    bot.send_message(message.chat.id, 'اسکین‌های مهم خود را بنویسید:')
    bot.register_next_step_handler(message, get_key_skins)

def get_key_skins(message):
    user_ads[message.chat.id]['key_skins'] = message.text
    bot.send_message(message.chat.id, 'توضیحات اکانت خود را بنویسید:')
    bot.register_next_step_handler(message, get_description)

def get_description(message):
    user_ads[message.chat.id]['description'] = message.text
    bot.send_message(message.chat.id, 'قیمت فروش اکانت خود را به تومان وارد کنید:')
    bot.register_next_step_handler(message, get_price)

def get_price(message):
    user_ads[message.chat.id]['price'] = message.text
    bot.send_message(message.chat.id, 'یک ویدیو از اسکین‌های خود ارسال کنید:')
    bot.register_next_step_handler(message, get_video)

def get_video(message):
    if not message.video:
        bot.send_message(message.chat.id, 'لطفا یک ویدیو ارسال کنید.')
        bot.register_next_step_handler(message, get_video)
        return
    user_ads[message.chat.id]['video'] = message.video.file_id
    ad = user_ads[message.chat.id]
    ad['user_id'] = message.from_user.id
    ad['status'] = 'pending'
    ads.append(ad)

    # ارسال برای ادمین
    ad_text = f'🔔 یک آگهی جدید برای تایید:\n\n✅ نام کالکشن: {ad["collection"]}\n✅ اسکین‌های مهم: {ad["key_skins"]}\n✅ توضیحات: {ad["description"]}\n✅ قیمت: {ad["price"]} تومان'
    bot.send_message(ADMIN_ID, ad_text)
    bot.send_video(ADMIN_ID, ad['video'], caption='برای تایید /approve یا برای رد /reject را بزنید.')

    bot.send_message(message.chat.id, 'آگهی شما برای تایید به ادمین ارسال شد.')

# --- تایید یا رد آگهی توسط ادمین ---
@bot.message_handler(commands=['approve'])
def approve_ad(message):
    for ad in ads:
        if ad['status'] == 'pending':
            ad['status'] = 'approved'
            bot.send_message(ad['user_id'], '✅ آگهی شما تایید شد و در لیست آگهی‌ها قرار گرفت.')
            bot.send_message(message.chat.id, 'آگهی تایید شد.')
            return
    bot.send_message(message.chat.id, 'آگهی در انتظار تایید پیدا نشد.')

@bot.message_handler(commands=['reject'])
def reject_ad(message):
    for ad in ads:
        if ad['status'] == 'pending':
            ad['status'] = 'rejected'
            bot.send_message(ad['user_id'], '❌ آگهی شما رد شد.')
            bot.send_message(message.chat.id, 'آگهی رد شد.')
            return
    bot.send_message(message.chat.id, 'آگهی در انتظار تایید پیدا نشد.')

# --- مشاهده آگهی‌ها ---
@bot.message_handler(func=lambda m: m.text == 'مشاهده آگهی‌ها')
def view_ads(message):
    approved_ads = [ad for ad in ads if ad['status'] == 'approved']
    if not approved_ads:
        bot.send_message(message.chat.id, 'هیچ آگهی تایید شده‌ای وجود ندارد.')
        return
    for ad in approved_ads:
        text = f'✅ نام کالکشن: {ad["collection"]}\n✅ اسکین‌های مهم: {ad["key_skins"]}\n✅ توضیحات: {ad["description"]}\n✅ قیمت: {ad["price"]} تومان'
        bot.send_video(message.chat.id, ad['video'], caption=text)

# --- اجرای ربات ---
bot.infinity_polling()
