import telebot
from telebot import types
from flask import Flask, request
import threading

# ======= تنظیمات اولیه =======
BOT_TOKEN = '7933020801:AAHvfiIlfg5frqosVCgY1n1pUFElwQsr7B8'
ADMIN_ID = 6697070308  # آیدی عددی ادمین
CHANNEL_USERNAME = '@filmskina'  # یوزرنیم کانال
CHANNEL_LINK = 'https://t.me/filmskina'  # لینک کانال

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}

# ======= دکمه منو =======
def send_menu(chat_id):
    markup = types.InlineKeyboardMarkup()
    post_button = types.InlineKeyboardButton("ثبت آگهی", callback_data='post_ad')
    view_button = types.InlineKeyboardButton("مشاهده آگهی‌ها", url=CHANNEL_LINK)
    price_button = types.InlineKeyboardButton("قیمت یاب اکانت", callback_data='price_finder')
    markup.add(post_button)
    markup.add(view_button)
    markup.add(price_button)
    bot.send_message(chat_id, "سلام! از دکمه‌های زیر استفاده کنید:", reply_markup=markup)

# ======= دستور /start و /menu =======
@bot.message_handler(commands=['start', 'menu'])
def menu_command(message):
    send_menu(message.chat.id)

# ======= سیستم ثبت آگهی =======
@bot.callback_query_handler(func=lambda call: call.data == 'post_ad')
def post_ad(call):
    user_data[call.from_user.id] = {'user_id': call.from_user.id, 'username': call.from_user.username}
    bot.send_message(call.message.chat.id, "لطفاً نام کالکشن خود را وارد کنید:")
    bot.register_next_step_handler(call.message, get_collection)

def get_collection(message):
    user_data[message.chat.id]['collection'] = message.text
    bot.send_message(message.chat.id, "لطفاً اسکین‌های مهم اکانت را وارد کنید:")
    bot.register_next_step_handler(message, get_key_skins)

def get_key_skins(message):
    user_data[message.chat.id]['key_skins'] = message.text
    bot.send_message(message.chat.id, "توضیحات کامل اکانت را وارد کنید:")
    bot.register_next_step_handler(message, get_description)

def get_description(message):
    user_data[message.chat.id]['description'] = message.text
    bot.send_message(message.chat.id, "قیمت مورد نظر برای فروش اکانت را وارد کنید:")
    bot.register_next_step_handler(message, get_price)

def get_price(message):
    user_data[message.chat.id]['price'] = message.text
    bot.send_message(message.chat.id, "لطفاً یک ویدئو از اکانت خود ارسال کنید:")
    bot.register_next_step_handler(message, get_video)

def get_video(message):
    if message.content_type != 'video':
        bot.send_message(message.chat.id, "❌ لطفاً فقط یک ویدئو ارسال کنید:")
        return
    user_data[message.chat.id]['video'] = message.video.file_id
    send_to_admin(message.chat.id)

def send_to_admin(user_id):
    data = user_data[user_id]
    caption = f"📢 آگهی جدید:\n\n" \
              f"🧩 کالکشن: {data['collection']}\n" \
              f"🎮 اسکین‌های مهم: {data['key_skins']}\n" \
              f"📝 توضیحات: {data['description']}\n" \
              f"💰 قیمت: {data['price']} تومان\n\n" \
              f"👤 ارسال‌کننده: @{data['username'] or 'نامشخص'}\n" \
              f"🆔 آیدی عددی: {data['user_id']}"

    markup = types.InlineKeyboardMarkup()
    approve_button = types.InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{user_id}")
    reject_button = types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id}")
    markup.add(approve_button, reject_button)
    bot.send_video(ADMIN_ID, data['video'], caption=caption, reply_markup=markup)
    bot.send_message(user_id, "آگهی شما برای بررسی به ادمین ارسال شد. پس از تأیید، در کانال منتشر خواهد شد.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('reject_'))
def handle_admin_response(call):
    action, user_id = call.data.split('_')
    user_id = int(user_id)
    data = user_data.get(user_id)
    if not data:
        bot.answer_callback_query(call.id, "اطلاعات آگهی یافت نشد.")
        return

    if action == 'approve':
        caption = f"📢 آگهی تأیید شده:\n\n" \
                  f"🧩 کالکشن: {data['collection']}\n" \
                  f"🎮 اسکین‌های مهم: {data['key_skins']}\n" \
                  f"📝 توضیحات: {data['description']}\n" \
                  f"💰 قیمت: {data['price']} تومان\n" \
                  f"👤 ارسال‌کننده: @{data['username'] or 'نامشخص'}"
        bot.send_video(CHANNEL_USERNAME, data['video'], caption=caption)
        bot.send_message(user_id, "✅ آگهی شما تأیید و در کانال منتشر شد.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    elif action == 'reject':
        bot.send_message(user_id, "❌ متأسفانه آگهی شما توسط ادمین رد شد.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

# ======= قیمت‌یاب اکانت (بدون تغییر) =======
@bot.callback_query_handler(func=lambda call: call.data == 'price_finder')
def price_finder(call):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Supreme", "Grand", "Exquisite", "Deluxe")
    bot.send_message(call.message.chat.id, "✅ لطفاً نوع اسکین‌های خود را انتخاب کنید:", reply_markup=markup)
    bot.register_next_step_handler(call.message, calculate_price)

def calculate_price(message):
    skin_type = message.text
    prices = {
        "Supreme": 1200000,
        "Grand": 500000,
        "Exquisite": 300000,
        "Deluxe": 100000
    }
    price = prices.get(skin_type)
    if price:
        bot.send_message(message.chat.id, f"✅ قیمت تقریبی هر اسکین {skin_type}: {price} تومان", reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, "❌ نوع اسکین معتبر نیست. لطفاً مجدداً تلاش کنید.", reply_markup=types.ReplyKeyboardRemove())

# ======= اجرای ربات با Flask (در صورت نیاز) =======
from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return '✅ Bot is alive and running!', 200

@app.route('/', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'ok', 200

import threading

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

bot.infinity_polling()
