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

# ======= چک کردن بازگشت در هر مرحله =======
def check_back(message):
    if message.text == "بازگشت":
        send_menu(message.chat.id)
        return True
    return False

# ======= دستور /start و /menu =======
@bot.message_handler(commands=['start', 'menu'])
def menu_command(message):
    send_menu(message.chat.id)

# ======= هندل کردن دکمه‌ها =======
@bot.message_handler(func=lambda message: message.text in ["ثبت آگهی", "اکانت درخواستی", "مشاهده آگهی‌ها", "قیمت یاب اکانت", "بازگشت"])
def handle_buttons(message):
    if message.text == "ثبت آگهی":
        user_data[message.from_user.id] = {'user_id': message.from_user.id, 'username': message.from_user.username}
        bot.send_message(message.chat.id, "لطفاً نام کالکشن خود را وارد کنید:")
        bot.register_next_step_handler(message, get_collection)
    elif message.text == "اکانت درخواستی":
        bot.send_message(message.chat.id, "لطفاً مشخصات اکانتی که مدنظر دارید، با حداکثر قیمتی که می‌خواید هزینه کنید را ارسال کنید.")
    elif message.text == "مشاهده آگهی‌ها":
        markup = types.InlineKeyboardMarkup()
        channel_button = types.InlineKeyboardButton("🔗 رفتن به کانال آگهی‌ها", url=CHANNEL_LINK)
        markup.add(channel_button)
        bot.send_message(message.chat.id, "✅ برای مشاهده آگهی‌های ثبت‌شده، روی دکمه زیر کلیک کنید:", reply_markup=markup)
    elif message.text == "قیمت یاب اکانت":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Supreme", "Grand", "Exquisite", "Deluxe", "بازگشت")
        bot.send_message(message.chat.id, "✅ لطفاً نوع اسکین‌های خود را انتخاب کنید:", reply_markup=markup)
        bot.register_next_step_handler(message, calculate_price)
    elif message.text == "بازگشت":
        send_menu(message.chat.id)

# ======= سیستم ثبت آگهی =======
def get_collection(message):
    if check_back(message): return
    user_data[message.chat.id]['collection'] = message.text
    bot.send_message(message.chat.id, "لطفاً اسکین‌های مهم اکانت را وارد کنید:")
    bot.register_next_step_handler(message, get_key_skins)

def get_key_skins(message):
    if check_back(message): return
    user_data[message.chat.id]['key_skins'] = message.text
    bot.send_message(message.chat.id, "توضیحات کامل اکانت را وارد کنید:")
    bot.register_next_step_handler(message, get_description)

def get_description(message):
    if check_back(message): return
    user_data[message.chat.id]['description'] = message.text
    bot.send_message(message.chat.id, "قیمت مورد نظر برای فروش اکانت را وارد کنید:")
    bot.register_next_step_handler(message, get_price)

def get_price(message):
    if check_back(message): return
    user_data[message.chat.id]['price'] = message.text
    bot.send_message(message.chat.id, "لطفاً یک ویدئو از اکانت خود ارسال کنید:")
    bot.register_next_step_handler(message, get_video)

def get_video(message):
    if check_back(message): return
    if message.content_type != 'video':
        bot.send_message(message.chat.id, "❌ لطفاً فقط یک ویدئو ارسال کنید:")
        bot.register_next_step_handler(message, get_video)
        return
    user_data[message.chat.id]['video'] = message.video.file_id
    send_to_admin(message.chat.id)

def send_to_admin(user_id):
    data = user_data[user_id]
    caption = f"📢 آگهی جدید برای بررسی:\n\n" \
              f"🧩 کالکشن: {data['collection']}\n" \
              f"🎮 اسکین‌های مهم: {data['key_skins']}\n" \
              f"📝 توضیحات: {data['description']}\n" \
              f"💰 قیمت: {data['price']} تومان\n\n" \
              f"👤 ارسال‌کننده: @{data['username'] or 'نامشخص'}"

    markup = types.InlineKeyboardMarkup()
    approve_button = types.InlineKeyboardButton("✅ تأیید آگهی (وارد کردن کد)", callback_data=f"approve_{user_id}")
    reject_button = types.InlineKeyboardButton("❌ رد آگهی (نوشتن دلیل)", callback_data=f"reject_{user_id}")
    markup.add(approve_button, reject_button)

    bot.send_video(ADMIN_ID, data['video'], caption=caption, reply_markup=markup)
    bot.send_message(user_id, "آگهی شما برای بررسی به ادمین ارسال شد.\nپس از تأیید، در کانال منتشر خواهد شد.")

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
    if check_back(message): return
    skin_type = message.text

    if skin_type in ["Supreme", "Grand", "Exquisite", "Deluxe"]:
        user_id = message.chat.id
        user_data.setdefault(user_id, {"Supreme": 0, "Grand": 0, "Exquisite": 0, "Deluxe": 0})

        if skin_type == "Supreme":
            explanation = "✅ اسکین‌های Supreme هر کدام به ارزش تقریبی ۱,۲۰۰,۰۰۰ تومان محاسبه می‌شوند.\n❌ اسکین‌های رایگان در این بخش لحاظ نمی‌شوند."
        elif skin_type == "Grand":
            explanation = "✅ اسکین‌های Grand هر کدام به ارزش تقریبی ۵۰۰,۰۰۰ تومان محاسبه می‌شوند.\n❌ اسکین‌های رایگان در این بخش لحاظ نمی‌شوند."
        elif skin_type == "Exquisite":
            explanation = "✅ اسکین‌های Exquisite هر کدام به ارزش تقریبی ۳۰۰,۰۰۰ تومان محاسبه می‌شوند.\n❌ اسکین‌های رایگان در این بخش لحاظ نمی‌شوند."
        else:
            explanation = "✅ اسکین‌های Deluxe به‌صورت زیر محاسبه می‌شوند:\n- کمتر از ۲۰ اسکین: هر اسکین ۲۵۰,۰۰۰ تومان\n- بین ۲۰ تا ۴۰ اسکین: ۵۰۰,۰۰۰ تومان ثابت\n- بالای ۴۰ اسکین: ۷۰۰,۰۰۰ تومان ثابت"

        bot.send_message(user_id, explanation)
        bot.send_message(user_id, f"✅ لطفاً تعداد اسکین‌های {skin_type} خود را وارد کنید:")
        bot.register_next_step_handler(message, lambda msg: process_skin_count(msg, skin_type))
    else:
        bot.send_message(message.chat.id, "❌ نوع اسکین معتبر نیست. لطفاً مجدداً انتخاب کنید.")
        send_menu(message.chat.id)

# ثبت تعداد اسکین‌ها و نمایش دکمه تایید
def process_skin_count(message, skin_type):
    if check_back(message): return
    user_id = message.chat.id
    try:
        count = int(message.text)
        if count < 0:
            raise ValueError
    except ValueError:
        bot.send_message(user_id, "❌ لطفاً یک عدد معتبر وارد کنید.")
        bot.register_next_step_handler(message, lambda msg: process_skin_count(msg, skin_type))
        return

    user_data[user_id][skin_type] = count
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("✅ تأیید و ادامه", "📊 نمایش قیمت نهایی")
    bot.send_message(user_id, f"✅ تعداد {skin_type} ذخیره شد. برای ادامه انتخاب، دکمه تأیید را بزنید یا برای مشاهده قیمت نهایی، دکمه نمایش قیمت نهایی را انتخاب کنید.", reply_markup=markup)
    bot.register_next_step_handler(message, handle_next_action)

# مدیریت دکمه‌ها بعد از تایید
def handle_next_action(message):
    if check_back(message): return
    if message.text == "✅ تأیید و ادامه":
        send_menu(message.chat.id)
    elif message.text == "📊 نمایش قیمت نهایی":
        show_final_price(message)
    else:
        bot.send_message(message.chat.id, "❌ انتخاب نامعتبر. لطفاً مجدداً انتخاب کنید.")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("✅ تأیید و ادامه", "📊 نمایش قیمت نهایی")
        bot.send_message(message.chat.id, "لطفاً دکمه موردنظر را انتخاب کنید:", reply_markup=markup)
        bot.register_next_step_handler(message, handle_next_action)

# محاسبه و نمایش قیمت نهایی
def show_final_price(message):
    user_id = message.chat.id
    data = user_data.get(user_id, {"Supreme": 0, "Grand": 0, "Exquisite": 0, "Deluxe": 0})

    total_price = 0
    total_price += data["Supreme"] * 1200000
    total_price += data["Grand"] * 500000
    total_price += data["Exquisite"] * 300000

    deluxe_count = data["Deluxe"]
    if deluxe_count < 20:
        total_price += deluxe_count * 250000
    elif 20 <= deluxe_count <= 40:
        total_price += 500000
    elif deluxe_count > 40:
        total_price += 700000

    bot.send_message(message.chat.id, f"✅ ارزش تقریبی اسکین‌های {skin_type} شما: {price:,} تومان\n\n💎 قیمت بالا ارزش اکانت شماست.\nبرای ثبت آگهی تو کانال، قیمت فروش رو خودتون تعیین می‌کنید.", reply_markup=types.ReplyKeyboardRemove())
    send_menu(message.chat.id)
    
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
