import telebot
from telebot import types
from flask import Flask, request
import threading

# ======= تنظیمات اولیه =======
BOT_TOKEN = '7933020801:AAHvfiIlfg5frqosVCgY1n1pUFElwQsr7B8'
ADMIN_ID = 6697070308  # آیدی ادمین
CHANNEL_USERNAME = '@filmskina'  # کانال نهایی برای ارسال درخواست‌های تایید شده

bot = telebot.TeleBot(BOT_TOKEN)

# ذخیره موقت داده‌های درخواست‌ها
user_requests = {}
pending_approval_codes = {}  # برای ذخیره منتظر وارد کردن کد توسط ادمین
pending_reject_reasons = {}  # برای ذخیره منتظر وارد کردن دلیل رد توسط ادمین

# ======= منوی اصلی =======
def send_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("ثبت درخواست"),
        types.KeyboardButton("بازگشت")
    )
    bot.send_message(chat_id, "سلام! لطفاً گزینه مورد نظر را انتخاب کنید:", reply_markup=markup)

# ======= چک بازگشت =======
def check_back(message):
    if message.text == "بازگشت":
        send_menu(message.chat.id)
        return True
    return False

# ======= شروع ربات =======
@bot.message_handler(commands=['start', 'menu'])
def start_menu(message):
    send_menu(message.chat.id)

# ======= هندل دکمه‌ها =======
@bot.message_handler(func=lambda m: m.text in ["ثبت درخواست", "بازگشت"])
def handle_main_buttons(message):
    if message.text == "ثبت درخواست":
        bot.send_message(message.chat.id, "لطفاً متن درخواست خود را ارسال کنید:")
        bot.register_next_step_handler(message, get_request_text)
    elif message.text == "بازگشت":
        send_menu(message.chat.id)

# ======= دریافت متن درخواست =======
def get_request_text(message):
    if check_back(message):
        return
    user_requests[message.chat.id] = {
        'user_id': message.from_user.id,
        'username': message.from_user.username or "نامشخص",
        'text': message.text
    }

    # نمایش متن درخواست برای تایید نهایی کاربر
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("تایید", "لغو")
    bot.send_message(message.chat.id,
                     f"متن درخواست شما:\n\n{message.text}\n\nلطفاً تایید یا لغو کنید.",
                     reply_markup=markup)
    bot.register_next_step_handler(message, final_user_confirmation)

# ======= تایید نهایی کاربر =======
def final_user_confirmation(message):
    if check_back(message):
        user_requests.pop(message.chat.id, None)
        return

    if message.text == "لغو":
        bot.send_message(message.chat.id, "درخواست شما لغو شد.", reply_markup=types.ReplyKeyboardRemove())
        user_requests.pop(message.chat.id, None)
        send_menu(message.chat.id)
        return

    if message.text == "تایید":
        data = user_requests.get(message.chat.id)
        if not data:
            bot.send_message(message.chat.id, "خطا: درخواست شما یافت نشد.", reply_markup=types.ReplyKeyboardRemove())
            send_menu(message.chat.id)
            return

        # ارسال پیام درخواست به ادمین
        markup = types.InlineKeyboardMarkup()
        approve_btn = types.InlineKeyboardButton("✅ تأیید (وارد کردن کد)", callback_data=f"approve_{message.chat.id}")
        reject_btn = types.InlineKeyboardButton("❌ رد (نوشتن دلیل)", callback_data=f"reject_{message.chat.id}")
        markup.add(approve_btn, reject_btn)

        text_to_admin = f"📨 درخواست جدید از @{data['username']} (id: {data['user_id']}):\n\n{data['text']}"
        bot.send_message(ADMIN_ID, text_to_admin, reply_markup=markup)

        bot.send_message(message.chat.id, "درخواست شما برای بررسی به ادمین ارسال شد.\nلطفاً منتظر پاسخ باشید.", reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, "لطفاً یکی از گزینه‌های تایید یا لغو را انتخاب کنید.")
        bot.register_next_step_handler(message, final_user_confirmation)

# ======= هندل callback ادمین =======
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def admin_callback(call):
    action, user_chat_id_str = call.data.split('_', 1)
    user_chat_id = int(user_chat_id_str)

    if action == "approve":
        bot.send_message(ADMIN_ID, "✅ لطفاً کد تأیید دلخواه برای این درخواست را وارد کنید:")
        pending_approval_codes[ADMIN_ID] = user_chat_id
        bot.edit_message_reply_markup(ADMIN_ID, call.message.message_id, reply_markup=None)

    elif action == "reject":
        bot.send_message(ADMIN_ID, "❌ لطفاً دلیل رد درخواست را بنویسید:")
        pending_reject_reasons[ADMIN_ID] = user_chat_id
        bot.edit_message_reply_markup(ADMIN_ID, call.message.message_id, reply_markup=None)

# ======= هندل متن ادمین (کد تأیید یا دلیل رد) =======
@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID)
def handle_admin_text(message):
    # اگر منتظر کد تایید است
    if ADMIN_ID in pending_approval_codes:
        user_chat_id = pending_approval_codes.pop(ADMIN_ID)
        code = message.text.strip()
        data = user_requests.get(user_chat_id)

        if not data:
            bot.send_message(ADMIN_ID, "❌ خطا: درخواست کاربر پیدا نشد.")
            return

        # ارسال پیام تایید به کاربر
        bot.send_message(user_chat_id,
                         f"✅ درخواست شما تایید شد.\nکد تایید: {code}\nلطفاً این کد را به ادمین ارسال کنید.")

        # ارسال درخواست به کانال با کد تأیید
        caption = f"📨 درخواست تأیید شده:\n\n{data['text']}\n\n👤 ارسال‌کننده: @{data['username']}\n🆔 کد درخواست: {code}"
        bot.send_message(CHANNEL_USERNAME, caption)

        # حذف درخواست از موقت
        user_requests.pop(user_chat_id, None)
        return

    # اگر منتظر دلیل رد است
    if ADMIN_ID in pending_reject_reasons:
        user_chat_id = pending_reject_reasons.pop(ADMIN_ID)
        reason = message.text.strip()
        data = user_requests.get(user_chat_id)

        if not data:
            bot.send_message(ADMIN_ID, "❌ خطا: درخواست کاربر پیدا نشد.")
            return

        # ارسال پیام رد به کاربر با دلیل
        bot.send_message(user_chat_id, f"❌ متأسفانه درخواست شما رد شد.\nدلیل: {reason}")

        # حذف درخواست از موقت
        user_requests.pop(user_chat_id, None)
        return

# ======= اجرای ربات با Flask =======
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

def run():
    app.run(host='0.0.0.0', port=8080)

import threading
threading.Thread(target=run).start()

bot.infinity_polling()
