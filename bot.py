import telebot
from telebot import types
from flask import Flask, request
import threading

# ======= تنظیمات اولیه =======
BOT_TOKEN = '7933020801:AAHvfiIlfg5frqosVCgY1n1pUFElwQsr7B8'
ADMIN_ID = 6697070308  # آیدی عددی ادمین
CHANNEL_FOR_JOIN = '@TareqMlbb'  # کانال عضویت اجباری (یوزرنیم با @)
CHANNEL_LINK = 'https://t.me/filmskina'  # لینک کانال آگهی‌ها

bot = telebot.TeleBot(BOT_TOKEN)

# ======= ذخیره داده‌ها در حافظه =======
user_data = {}
pending_ads = {}      # آگهی‌های در انتظار تایید {user_id: data}
approved_ads = []     # آگهی‌های تایید شده لیستی

# ======= چک عضویت اجباری =======
def check_membership(chat_id, user_id):
    try:
        member = bot.get_chat_member(CHANNEL_FOR_JOIN, user_id)
        if member.status in ['left', 'kicked']:
            return False
        return True
    except Exception:
        return False

def send_membership_message(chat_id):
    markup = types.InlineKeyboardMarkup()
    join_button = types.InlineKeyboardButton("🔗 عضویت در کانال", url=f"https://t.me/{CHANNEL_FOR_JOIN[1:]}")
    markup.add(join_button)
    bot.send_message(chat_id, "⚠️ برای استفاده از ربات باید در کانال عضو باشید.", reply_markup=markup)

# ======= منوی اصلی =======
def send_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("ثبت آگهی", "مشاهده آگهی‌ها")
    markup.row("قیمت یاب اکانت", "اکانت درخواستی")
    bot.send_message(chat_id, "👋 به ربات خوش آمدید! یکی از گزینه‌ها را انتخاب کنید:", reply_markup=markup)

# ======= استارت و منو =======
@bot.message_handler(commands=['start', 'menu'])
def handle_start(message):
    if not check_membership(message.chat.id, message.from_user.id):
        send_membership_message(message.chat.id)
        return
    send_menu(message.chat.id)

# ======= هندلر دکمه‌ها با چک عضویت =======
@bot.message_handler(func=lambda m: m.text in ["ثبت آگهی", "مشاهده آگهی‌ها", "قیمت یاب اکانت", "اکانت درخواستی", "بازگشت"])
def handle_main_buttons(message):
    if not check_membership(message.chat.id, message.from_user.id):
        send_membership_message(message.chat.id)
        return

    text = message.text
    if text == "ثبت آگهی":
        user_data[message.from_user.id] = {}
        bot.send_message(message.chat.id, "لطفاً نام کالکشن خود را وارد کنید:")
        bot.register_next_step_handler(message, get_collection)
    elif text == "مشاهده آگهی‌ها":
        if not approved_ads:
            bot.send_message(message.chat.id, "فعلاً آگهی تایید شده‌ای موجود نیست.")
            return
        # نمایش آگهی‌ها به صورت پیام به کاربر
        for ad in approved_ads:
            ad_text = f"🏷️ نام کالکشن: {ad['collection']}\n"\
                      f"✨ اسکین‌های کلیدی: {ad['key_skins']}\n"\
                      f"📝 توضیحات: {ad['description']}\n"\
                      f"💰 قیمت فروش: {ad['price']}\n"\
                      f"👤 توسط: @{ad['username'] if ad['username'] else 'ناشناس'}"
            bot.send_message(message.chat.id, ad_text)
            if 'video_file_id' in ad:
                bot.send_video(message.chat.id, ad['video_file_id'])
    elif text == "قیمت یاب اکانت":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Supreme", "Grand", "Exquisite", "Deluxe", "پایان", "بازگشت")
        bot.send_message(message.chat.id, "✅ لطفاً نوع اسکین‌های خود را انتخاب کنید:", reply_markup=markup)
        user_data[message.from_user.id] = {"skins": {"Supreme":0, "Grand":0, "Exquisite":0, "Deluxe":0}}
        bot.register_next_step_handler(message, price_finder)
    elif text == "اکانت درخواستی":
        bot.send_message(message.chat.id, "لطفاً مشخصات اکانتی که مدنظر دارید و حداکثر قیمت را ارسال کنید.")
    elif text == "بازگشت":
        send_menu(message.chat.id)

# ======= مراحل ثبت آگهی =======
def get_collection(message):
    if not check_membership(message.chat.id, message.from_user.id):
        send_membership_message(message.chat.id)
        return
    user_data[message.from_user.id]['collection'] = message.text
    bot.send_message(message.chat.id, "اسکین‌های کلیدی خود را وارد کنید:")
    bot.register_next_step_handler(message, get_key_skins)

def get_key_skins(message):
    if not check_membership(message.chat.id, message.from_user.id):
        send_membership_message(message.chat.id)
        return
    user_data[message.from_user.id]['key_skins'] = message.text
    bot.send_message(message.chat.id, "توضیحات اکانت را وارد کنید:")
    bot.register_next_step_handler(message, get_description)

def get_description(message):
    if not check_membership(message.chat.id, message.from_user.id):
        send_membership_message(message.chat.id)
        return
    user_data[message.from_user.id]['description'] = message.text
    bot.send_message(message.chat.id, "قیمت فروش را وارد کنید (به تومان):")
    bot.register_next_step_handler(message, get_price)

def get_price(message):
    if not check_membership(message.chat.id, message.from_user.id):
        send_membership_message(message.chat.id)
        return
    price = message.text
    if not price.isdigit():
        bot.send_message(message.chat.id, "لطفاً قیمت را فقط به صورت عدد وارد کنید:")
        bot.register_next_step_handler(message, get_price)
        return
    user_data[message.from_user.id]['price'] = price
    bot.send_message(message.chat.id, "لطفاً ویدیو یا گیف اسکین‌های خود را ارسال کنید:")
    bot.register_next_step_handler(message, get_video)

def get_video(message):
    if not check_membership(message.chat.id, message.from_user.id):
        send_membership_message(message.chat.id)
        return
    if message.content_type not in ['video', 'animation']:
        bot.send_message(message.chat.id, "لطفاً فقط ویدیو یا گیف ارسال کنید:")
        bot.register_next_step_handler(message, get_video)
        return
    file_id = message.video.file_id if message.content_type == 'video' else message.animation.file_id

    user_data[message.from_user.id]['video_file_id'] = file_id

    # ذخیره در pending_ads برای تایید ادمین
    pending_ads[message.from_user.id] = user_data[message.from_user.id].copy()

    bot.send_message(message.chat.id, "آگهی شما ثبت شد و پس از بررسی توسط ادمین، نتیجه به شما اطلاع داده می‌شود.")
    # ارسال آگهی به ادمین
    send_ad_to_admin(message.from_user.id)

# ======= ارسال آگهی به ادمین برای تایید =======
def send_ad_to_admin(user_id):
    ad = pending_ads.get(user_id)
    if not ad:
        return
    text = f"✅ آگهی جدید:\n"\
           f"🏷️ نام کالکشن: {ad['collection']}\n"\
           f"✨ اسکین‌های کلیدی: {ad['key_skins']}\n"\
           f"📝 توضیحات: {ad['description']}\n"\
           f"💰 قیمت فروش: {ad['price']}\n"\
           f"👤 کاربر: @{bot.get_chat(user_id).username if bot.get_chat(user_id).username else 'ناشناس'}\n\n"\
           f"برای تایید این آگهی: /approve_{user_id}\n"\
           f"برای رد کردن این آگهی: /reject_{user_id}"

    bot.send_message(ADMIN_ID, text)
    if 'video_file_id' in ad:
        bot.send_video(ADMIN_ID, ad['video_file_id'])

# ======= دستورهای ادمین برای تایید و رد آگهی =======
@bot.message_handler(commands=['approve', 'reject'])
def admin_command_handler(message):
    if message.from_user.id != ADMIN_ID:
        return

    # دستور مثل /approve_123456 یا /reject_123456
    command = message.text.split('_')[0][1:]
    user_id_str = message.text.split('_')[1] if len(message.text.split('_'))>1 else None

    if not user_id_str or not user_id_str.isdigit():
        bot.send_message(message.chat.id, "فرمت دستور صحیح نیست.")
        return

    user_id = int(user_id_str)

    if command == 'approve':
        if user_id in pending_ads:
            approved_ads.append(pending_ads[user_id])
            bot.send_message(message.chat.id, f"آگهی کاربر {user_id} تایید شد.")
            bot.send_message(user_id, "آگهی شما تایید و ثبت شد. ممنون از همکاری شما.")
            del pending_ads[user_id]
        else:
            bot.send_message(message.chat.id, "آگهی‌ای برای این کاربر یافت نشد.")
    elif command == 'reject':
        if user_id in pending_ads:
            bot.send_message(message.chat.id, f"آگهی کاربر {user_id} رد شد.")
            bot.send_message(user_id, "متاسفانه آگهی شما توسط ادمین رد شد.")
            del pending_ads[user_id]
        else:
            bot.send_message(message.chat.id, "آگهی‌ای برای این کاربر یافت نشد.")

# ======= قیمت‌یاب اکانت =======
def price_finder(message):
    if not check_membership(message.chat.id, message.from_user.id):
        send_membership_message(message.chat.id)
        return

    user_id = message.from_user.id
    text = message.text

    if text == "بازگشت":
        send_menu(message.chat.id)
        return

    if text == "پایان":
        # محاسبه قیمت نهایی
        skins = user_data[user_id]["skins"]
        total_price = 0

        # قیمت ثابت برای Supreme, Grand, Exquisite
        total_price += skins["Supreme"] * 30000
        total_price += skins["Grand"] * 20000
        total_price += skins["Exquisite"] * 15000

        # Deluxe قیمت متغیر بر اساس تعداد
        deluxe_count = skins["Deluxe"]
        if deluxe_count < 20:
            total_price += deluxe_count * 25000
        elif 20 <= deluxe_count <= 40:
            total_price += 500000
        else:
            total_price += 700000

        text_price = f"💎 ارزش اکانت شما:\n"\
                     f"Supreme: {skins['Supreme']} اسکین × ۳۰,۰۰۰ = {skins['Supreme']*30000} تومان\n"\
                     f"Grand: {skins['Grand']} اسکین × ۲۰,۰۰۰ = {skins['Grand']*20000} تومان\n"\
                     f"Exquisite: {skins['Exquisite']} اسکین × ۱۵,۰۰۰ = {skins['Exquisite']*15000} تومان\n"\
                     f"Deluxe: {deluxe_count} اسکین = "

        if deluxe_count < 20:
            text_price += f"{deluxe_count} × ۲۵,۰۰۰ = {deluxe_count*25000} تومان\n"
        elif 20 <= deluxe_count <= 40:
            text_price += "۵۰۰,۰۰۰ تومان (قیمت ثابت)\n"
        else:
            text_price += "۷۰۰,۰۰۰ تومان (قیمت ثابت)\n"

        text_price += f"\n💰 مجموع قیمت: {total_price} تومان\n\n"\
                      "قیمت بالا ارزش اکانت شماست\n"\
                      "برای ثبت آگهی تو کانال، قیمت فروش رو خودتون تعیین می‌کنید."

        bot.send_message(message.chat.id, text_price, reply_markup=types.ReplyKeyboardRemove())
        send_menu(message.chat.id)
        return

    # اگر متن عدد بود، به عنوان تعداد اسکین‌ها برای نوع انتخاب شده اضافه کن
    if text in ["Supreme", "Grand", "Exquisite", "Deluxe"]:
        bot.send_message(message.chat.id, f"✅ تعداد اسکین‌های {text} را وارد کنید:")
        user_data[user_id]["current_skin"] = text
        bot.register_next_step_handler(message, receive_skin_count)
    else:
        bot.send_message(message.chat.id, "لطفاً یکی از گزینه‌های منو را انتخاب کنید.")

def receive_skin_count(message):
    user_id = message.from_user.id
    if not check_membership(message.chat.id, user_id):
        send_membership_message(message.chat.id)
        return

    count_text = message.text
    if not count_text.isdigit():
        bot.send_message(message.chat.id, "لطفاً فقط عدد وارد کنید:")
        bot.register_next_step_handler(message, receive_skin_count)
        return
    count = int(count_text)
    current_skin = user_data[user_id].get("current_skin", None)
    if current_skin:
        user_data[user_id]["skins"][current_skin] = count
        bot.send_message(message.chat.id, f"✅ تعداد اسکین‌های {current_skin} ثبت شد: {count}")
        bot.send_message(message.chat.id, "در صورت اتمام، گزینه 'پایان' را بزنید یا اسکین دیگری انتخاب کنید.")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Supreme", "Grand", "Exquisite", "Deluxe", "پایان", "بازگشت")
        bot.send_message(message.chat.id, "لطفاً نوع اسکین بعدی را انتخاب کنید:", reply_markup=markup)
        bot.register_next_step_handler(message, price_finder)
    else:
        bot.send_message(message.chat.id, "خطایی رخ داد، لطفاً دوباره امتحان کنید.")
        send_menu(message.chat.id)

# ======= اجرای ربات با Flask و وبهوک =======
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return '✅ Bot is alive and running!', 200

@app.route('/', methods=['POST'])
def webhook():
    json_string = request.stream.read().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return 'ok', 200

def run():
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    threading.Thread(target=run).start()
    bot.infinity_polling()
