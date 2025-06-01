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
pending_codes = {}
pending_rejections = {}

# ======= دکمه منو =======
def send_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("ثبت آگهی"),
        types.KeyboardButton("اکانت درخواستی"),
        types.KeyboardButton("مشاهده آگهی‌ها"),
        types.KeyboardButton("قیمت یاب اکانت"),
        types.KeyboardButton("بازگشت")
    )
    bot.send_message(chat_id, "سلام! از منو زیر گزینه مورد نظر را انتخاب کنید:", reply_markup=markup)

# ======= هندل کردن دکمه‌ها =======
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    text = message.text
    chat_id = message.chat.id

    if text == "بازگشت":
        send_menu(chat_id)
        return

    if text in ["ثبت آگهی", "اکانت درخواستی", "مشاهده آگهی‌ها", "قیمت یاب اکانت"]:
        if text == "ثبت آگهی":
            user_data[chat_id] = {'user_id': message.from_user.id, 'username': message.from_user.username}
            send_cancelable_message(chat_id, "لطفاً نام کالکشن خود را وارد کنید:", get_collection)
        elif text == "اکانت درخواستی":
            send_cancelable_message(chat_id, "لطفاً مشخصات اکانتی که مدنظر دارید، با حداکثر قیمتی که می‌خواید هزینه کنید را ارسال کنید.")
        elif text == "مشاهده آگهی‌ها":
            markup = types.InlineKeyboardMarkup()
            channel_button = types.InlineKeyboardButton("🔗 رفتن به کانال آگهی‌ها", url=CHANNEL_LINK)
            markup.add(channel_button)
            bot.send_message(chat_id, "✅ برای مشاهده آگهی‌های ثبت‌شده، روی دکمه زیر کلیک کنید:", reply_markup=markup)
        elif text == "قیمت یاب اکانت":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add("Supreme", "Grand", "Exquisite", "Deluxe", "بازگشت")
            bot.send_message(chat_id, "✅ لطفاً نوع اسکین‌های خود را انتخاب کنید:", reply_markup=markup)
            bot.register_next_step_handler(message, calculate_price)
    else:
        bot.send_message(chat_id, "❌ دستور نامعتبر است. لطفاً از منو استفاده کنید.")
        send_menu(chat_id)

# ======= تابع ثبت مراحل آگهی =======
def send_cancelable_message(chat_id, text, next_step=None):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add("بازگشت")
    bot.send_message(chat_id, text, reply_markup=markup)
    if next_step:
        bot.register_next_step_handler_by_chat_id(chat_id, next_step)

def get_collection(message):
    if message.text == "بازگشت":
        send_menu(message.chat.id)
        return
    user_data[message.chat.id]['collection'] = message.text
    send_cancelable_message(message.chat.id, "لطفاً اسکین‌های مهم اکانت را وارد کنید:", get_key_skins)

def get_key_skins(message):
    if message.text == "بازگشت":
        send_menu(message.chat.id)
        return
    user_data[message.chat.id]['key_skins'] = message.text
    send_cancelable_message(message.chat.id, "توضیحات کامل اکانت را وارد کنید:", get_description)

def get_description(message):
    if message.text == "بازگشت":
        send_menu(message.chat.id)
        return
    user_data[message.chat.id]['description'] = message.text
    send_cancelable_message(message.chat.id, "قیمت مورد نظر برای فروش اکانت را وارد کنید:", get_price)

def get_price(message):
    if message.text == "بازگشت":
        send_menu(message.chat.id)
        return
    user_data[message.chat.id]['price'] = message.text
    bot.send_message(message.chat.id, "لطفاً یک ویدئو از اکانت خود ارسال کنید:", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("بازگشت"))
    bot.register_next_step_handler_by_chat_id(message.chat.id, get_video)

def get_video(message):
    if message.text == "بازگشت":
        send_menu(message.chat.id)
        return
    if message.content_type != 'video':
        bot.send_message(message.chat.id, "❌ لطفاً فقط یک ویدئو ارسال کنید:")
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_video)
        return
    user_data[message.chat.id]['video'] = message.video.file_id
    send_to_admin(message.chat.id)

# ======= ارسال به ادمین =======
def send_to_admin(user_id):
    data = user_data[user_id]
    caption = f"📢 آگهی جدید برای بررسی:\n\n" \
              f"🧩 کالکشن: {data['collection']}\n" \
              f"🎮 اسکین‌های مهم: {data['key_skins']}\n" \
              f"📝 توضیحات: {data['description']}\n" \
              f"💰 قیمت: {data['price']} تومان\n\n" \
              f"👤 ارسال‌کننده: @{data['username'] or 'نامشخص'}"
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تأیید آگهی (کد)", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ رد آگهی (دلیل)", callback_data=f"reject_{user_id}")
    )
    bot.send_video(ADMIN_ID, data['video'], caption=caption, reply_markup=markup)
    bot.send_message(user_id, "آگهی شما برای بررسی به ادمین ارسال شد.\nپس از تأیید، در کانال منتشر خواهد شد.")

# ======= بقیه کدها مثل هندل تایید و رد ادمین و قیمت‌یاب بدون تغییر =======
# ...
@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('reject_'))
def handle_admin_response(call):
    parts = call.data.split('_')
    action = parts[0]
    user_id = int(parts[1])

    data = user_data.get(user_id)
    if not data:
        bot.answer_callback_query(call.id, "اطلاعات آگهی یافت نشد.")
        return

    if action == 'approve':
        bot.send_message(ADMIN_ID, "✅ لطفاً یک کد دلخواه برای این آگهی وارد کنید:")
        pending_codes[ADMIN_ID] = {'user_id': user_id, 'message_id': call.message.message_id}
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    elif action == 'reject':
        bot.send_message(ADMIN_ID, "❌ لطفاً دلیل رد آگهی را بنویسید:")
        pending_rejections[ADMIN_ID] = {'user_id': user_id, 'message_id': call.message.message_id}
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID)
def handle_admin_text(message):
    if ADMIN_ID in pending_codes:
        code = message.text.strip()
        pending = pending_codes.pop(ADMIN_ID)
        user_id = pending['user_id']

        data = user_data.get(user_id)
        if not data:
            bot.send_message(ADMIN_ID, "❌ اطلاعات آگهی یافت نشد.")
            return

        caption = f"📢 آگهی تأیید شده:\n\n" \
                  f"🧩 کالکشن: {data['collection']}\n" \
                  f"🎮 اسکین‌های مهم: {data['key_skins']}\n" \
                  f"📝 توضیحات: {data['description']}\n" \
                  f"💰 قیمت: {data['price']} تومان\n" \
                  f"🆔 کد آگهی: {code}"

        contact_markup = types.InlineKeyboardMarkup()
        contact_button = types.InlineKeyboardButton("ارتباط با ادمین", url=f"tg://user?id={ADMIN_ID}")
        contact_markup.add(contact_button)

        bot.send_video(CHANNEL_USERNAME, data['video'], caption=caption, reply_markup=contact_markup)
        bot.send_message(user_id, f"✅ آگهی شما تأیید و در کانال منتشر شد.\nکد آگهی شما: {code}\n\nلطفاً این کد را به ادمین ارسال کنید.")

    elif ADMIN_ID in pending_rejections:
        reason = message.text.strip()
        pending = pending_rejections.pop(ADMIN_ID)
        user_id = pending['user_id']

        bot.send_message(user_id, f"❌ متأسفانه آگهی شما توسط ادمین رد شد.\nدلیل: {reason}")

# ======= قیمت‌یاب اکانت =======
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
        send_menu(message.chat.id)
    else:
        bot.send_message(message.chat.id, "❌ نوع اسکین معتبر نیست. لطفاً مجدداً تلاش کنید.", reply_markup=types.ReplyKeyboardRemove())
        send_menu(message.chat.id)

# ======= اجرای ربات با Flask =======
app = Flask(name)

@app.route('/', methods=['GET'])
def index():
    return '✅ Bot is alive and running!', 200

@app.route('/', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'ok', 200

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

bot.infinity_polling()

# ======= اجرای ربات با Flask =======
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return '✅ Bot is alive and running!', 200

@app.route('/', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'ok', 200

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

bot.infinity_polling()
