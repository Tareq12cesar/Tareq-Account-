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
        user_data[message.from_user.id] = {'user_id': message.from_user.id, 'username': message.from_user.username}
        bot.send_message(message.chat.id, "لطفاً مشخصات اکانتی که مدنظر دارید، با حداکثر قیمتی که می‌خواید هزینه کنید را ارسال کنید.")
        bot.register_next_step_handler(message, receive_account_request)
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

# ======= بخش اکانت درخواستی =======
def receive_account_request(message):
    if check_back(message): return
    user_data[message.from_user.id]['account_request_text'] = message.text
    bot.send_message(message.chat.id, "✅ درخواست شما ثبت شد.\nآیا می‌خواهید ارسال شود؟ (بله / خیر)")
    bot.register_next_step_handler(message, confirm_account_request)

def confirm_account_request(message):
    if check_back(message): return
    text = message.text.strip().lower()
    if text == 'بله':
        # ارسال پیام به ادمین با دکمه‌های تأیید و رد
        user_id = message.from_user.id
        data = user_data.get(user_id)
        if not data or 'account_request_text' not in data:
            bot.send_message(message.chat.id, "❌ مشکلی پیش آمده، لطفاً مجدداً تلاش کنید.")
            send_menu(message.chat.id)
            return

        caption = f"📩 درخواست اکانت جدید:\n\n" \
                  f"📝 متن درخواست:\n{data['account_request_text']}\n\n" \
                  f"👤 از طرف کاربر: @{data['username'] or 'نامشخص'} (ID: {user_id})"

        markup = types.InlineKeyboardMarkup()
        approve_button = types.InlineKeyboardButton("✅ تأیید", callback_data=f"accountreq_approve_{user_id}")
        reject_button = types.InlineKeyboardButton("❌ رد", callback_data=f"accountreq_reject_{user_id}")
        markup.add(approve_button, reject_button)

        bot.send_message(ADMIN_ID, caption, reply_markup=markup)
        bot.send_message(message.chat.id, "درخواست شما به ادمین ارسال شد.\nمنتظر پاسخ باشید.")
    elif text == 'خیر':
        bot.send_message(message.chat.id, "درخواست شما لغو شد.")
        send_menu(message.chat.id)
    else:
        bot.send_message(message.chat.id, "لطفاً فقط 'بله' یا 'خیر' را ارسال کنید.")
        bot.register_next_step_handler(message, confirm_account_request)

@bot.callback_query_handler(func=lambda call: call.data.startswith('accountreq_approve_') or call.data.startswith('accountreq_reject_'))
def handle_account_request_admin(call):
    parts = call.data.split('_')
    action = parts[1]
    user_id = int(parts[2])

    data = user_data.get(user_id)
    if not data or 'account_request_text' not in data:
        bot.answer_callback_query(call.id, "اطلاعات درخواست یافت نشد.")
        return

    if action == 'approve':
        bot.send_message(ADMIN_ID, "✅ لطفاً کد تأیید را وارد کنید:")
        pending_codes[ADMIN_ID] = {'user_id': user_id, 'type': 'account_request'}
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    elif action == 'reject':
        bot.send_message(ADMIN_ID, "❌ لطفاً دلیل رد را بنویسید:")
        pending_rejections[ADMIN_ID] = {'user_id': user_id, 'type': 'account_request'}
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID)
def handle_admin_text(message):
    # بررسی کد تأیید
    if ADMIN_ID in pending_codes:
        code = message.text.strip()
        pending = pending_codes.pop(ADMIN_ID)
        user_id = pending['user_id']

        if pending.get('type') == 'account_request':
            data = user_data.get(user_id)
            if not data or 'account_request_text' not in data:
                bot.send_message(ADMIN_ID, "❌ اطلاعات درخواست یافت نشد.")
                return

            caption = f"✅ درخواست اکانت تایید شد.\n\n" \
                      f"📝 متن درخواست:\n{data['account_request_text']}\n\n" \
                      f"🆔 کد تایید: {code}\n\n" \
                      f"👤 از طرف کاربر: @{data['username'] or 'نامشخص'}"

            # ارسال کد به کاربر
            bot.send_message(user_id, f"درخواست شما تایید شد.\nکد تایید: {code}\nلطفا این کد را به ادمین ارسال کنید.")

            # ارسال به کانال
            bot.send_message(CHANNEL_USERNAME, caption)

        else:
            # این بخش برای کد تأیید آگهی‌های ثبت شده است
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
         return

    # بررسی رد درخواست یا آگهی
    if ADMIN_ID in pending_rejections:
        reason = message.text.strip()
        pending = pending_rejections.pop(ADMIN_ID)
        user_id = pending['user_id']

        if pending.get('type') == 'account_request':
            bot.send_message(user_id, f"❌ متأسفانه درخواست اکانت شما توسط ادمین رد شد.\n
            
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
