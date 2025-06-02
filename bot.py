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
        user_data[message.chat.id] = {}
        bot.send_message(message.chat.id, "اسکین‌هایی که می‌خوای رو تایپ کن:")
        bot.register_next_step_handler(message, get_requested_skins)
    elif message.text == "مشاهده آگهی‌ها":
        markup = types.InlineKeyboardMarkup()
        channel_button = types.InlineKeyboardButton("🔗 رفتن به کانال آگهی‌ها", url=CHANNEL_LINK)
        markup.add(channel_button)
        bot.send_message(message.chat.id, "✅ برای مشاهده آگهی‌های ثبت‌شده، روی دکمه زیر کلیک کنید:", reply_markup=markup)
    elif message.text == "قیمت یاب اکانت":
         markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=1)
         markup.add("Supreme")
         markup.add("Grand")
         markup.add("Exquisite")
         markup.add("Deluxe")
         markup.add("بازگشت")
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
from telebot import types

user_data = {}

def send_skin_selection_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=1)  # ستون به جای ۲
    markup.add("Supreme", "Grand", "Exquisite", "Deluxe", "قیمت نهایی", "بازگشت")
    bot.send_message(chat_id, "➕ انتخاب بعدی؟", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["Supreme", "Grand", "Exquisite", "Deluxe", "قیمت نهایی", "بازگشت"])
def calculate_price(message):
    if check_back(message):
        return

    text = message.text.strip()

    if text == "قیمت نهایی":
        if message.chat.id not in user_data or not user_data[message.chat.id]:
            bot.send_message(message.chat.id, "❌ هنوز هیچ اسکینی ثبت نشده است.")
            send_skin_selection_menu(message.chat.id)
            return

        fixed_prices = {
            "Supreme": 1200000,
            "Grand": 500000,
            "Exquisite": 300000
        }

        total_price = 0
        summary_lines = []
        for skin_type, count in user_data[message.chat.id].items():
            if count is None:
                continue
            if skin_type in fixed_prices:
                price = fixed_prices[skin_type] * count
            else:  # Deluxe
                if count < 20:
                    price = 25000 * count
                elif 20 <= count <= 39:
                    price = 500000
                else:
                    price = 700000
            total_price += price
            summary_lines.append(f"💰 {skin_type}: تعداد {count} × قیمت = {price:,} تومان")

        final_message = "💵 قیمت نهایی کل اسکین‌ها:\n\n" + "\n".join(summary_lines) + f"\n\n💰 جمع کل: {total_price:,} تومان\n\n💡 قیمت بالا ارزش اکانت شماست\nبرای ثبت آگهی تو کانال، قیمت فروش رو خودتون تعیین می‌کنید."
        bot.send_message(message.chat.id, final_message)
        send_menu(message.chat.id)
        return

    valid_skin_types = ["Supreme", "Grand", "Exquisite", "Deluxe"]
    if text in valid_skin_types:
        if message.chat.id not in user_data:
            user_data[message.chat.id] = {}

        user_data[message.chat.id][text] = None

        explanations = {
            "Supreme": "✅ این دسته شامل اسکین‌های لجند می‌باشد.\n\nچندتا اسکین از این دسته داری؟",
            "Grand": "✅ این دسته شامل اسکین‌های کوف، جوجوتسو، سوپر هیرو، استاروارز، ناروتو، ابیس و... می‌باشد.\n(از اسکین‌های پرایم فقط راجر رو اینجا وارد کنید و بقیه رو در قسمت Exquisite وارد کنید)\n\n❌ توجه داشته باشید اسکین‌های رایگان این دسته مثل کارینا، تاموز، فلورین، راجر و... رو حساب نکنید.\n\nچندتا اسکین از این دسته داری؟",
            "Exquisite": "✅ این دسته شامل اسکین‌های کالکتور، لاکی باکس و کلادز می‌باشد (اسکین‌های پرایم در این قسمت وارد کنید).\n\n❌ توجه داشته باشید اسکین‌های رایگان این دسته مثل ناتالیا و... رو حساب نکنید.\n\nچندتا اسکین از این دسته داری؟",
            "Deluxe": "✅ این دسته شامل اسکین‌های زودیاک، لایتبورن، اپیک شاپ و... می‌باشد.\n\nچندتا اسکین از این دسته داری؟"
        }
        bot.send_message(message.chat.id, explanations[text])
        bot.register_next_step_handler(message, get_skin_count, text)
        return

    bot.send_message(message.chat.id, "❌ لطفاً از دکمه‌ها استفاده کنید.")
    send_skin_selection_menu(message.chat.id)

def get_skin_count(message, skin_type):
    try:
        count = int(message.text.strip())
        if count < 0:
            raise ValueError()
    except Exception:
        bot.send_message(message.chat.id, "❌ لطفاً فقط عدد مثبت وارد کنید. چندتا اسکین داری؟")
        bot.register_next_step_handler(message, get_skin_count, skin_type)
        return

    user_data[message.chat.id][skin_type] = count

    bot.send_message(
        message.chat.id,
        f"✅ تعداد اسکین‌های دسته {skin_type} ثبت شد.\n\nلطفاً دسته بعدی را انتخاب کنید یا «قیمت نهایی» را بزنید."
    )
    send_skin_selection_menu(message.chat.id)

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


# ======= بخش اکانت درخواستی =======
pending_requests = {}

def get_requested_skins(message):
    if check_back(message): return
    user_data[message.chat.id]['requested_skins'] = message.text
    bot.send_message(message.chat.id, "حداکثر قیمتت رو بگو:")
    bot.register_next_step_handler(message, get_requested_budget)

def get_requested_budget(message):
    if check_back(message): return
    user_data[message.chat.id]['max_price'] = message.text
    bot.send_message(message.chat.id, "درخواستت ثبت شد و برای بررسی به ادمین ارسال شد.")

    caption = f"درخواست اکانت:\n\nاسکین‌های دلخواه: {user_data[message.chat.id]['requested_skins']}\nحداکثر قیمت: {user_data[message.chat.id]['max_price']} تومان\nدرخواست‌دهنده: @{message.from_user.username or 'نامشخص'}"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("تأیید درخواست", callback_data=f"reqapprove_{message.chat.id}"),
        types.InlineKeyboardButton("رد درخواست", callback_data=f"reqreject_{message.chat.id}")
    )

    pending_requests[ADMIN_ID] = {'user_id': message.chat.id}
    bot.send_message(ADMIN_ID, caption, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("reqapprove_") or call.data.startswith("reqreject_"))
def handle_request_decision(call):
    chat_id = int(call.data.split("_")[1])
    action = call.data.split("_")[0]

    pending_requests[ADMIN_ID] = {'user_id': chat_id, 'approve': action == "reqapprove"}
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)

    if action == "reqapprove":
        bot.send_message(ADMIN_ID, "لطفاً یک کد تایید وارد کنید:")
    else:
        bot.send_message(ADMIN_ID, "لطفاً دلیل رد درخواست را بنویسید:")

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and ADMIN_ID in pending_requests)
def handle_admin_response(message):
    info = pending_requests.pop(ADMIN_ID)
    user_id = info['user_id']

    if info['approve']:
        code = message.text.strip()
        text = f"درخواست شما تایید شد.\nکد تایید: {code}\nلطفا این کد را به ادمین ارسال کنید."
        bot.send_message(user_id, text)

        post = f"درخواست تأیید شده:\nاسکین‌ها: {user_data[user_id]['requested_skins']}\nقیمت: {user_data[user_id]['max_price']} تومان\nکد تایید: {code}"
        bot.send_message(CHANNEL_USERNAME, post)
    else:
        reason = message.text.strip()
        bot.send_message(user_id, f"درخواست شما رد شد.\nدلیل: {reason}")



# ======= سیستم اکانت درخواستی با الگویی مشابه ثبت آگهی =======

pending_codes = {}
pending_rejections = {}

def get_requested_skins(message):
    if check_back(message): return
    user_data[message.chat.id]['requested_skins'] = message.text
    bot.send_message(message.chat.id, "حداکثر قیمتی که می‌خوای هزینه کنی رو وارد کن:")
    bot.register_next_step_handler(message, get_requested_price)

def get_requested_price(message):
    if check_back(message): return
    user_data[message.chat.id]['max_price'] = message.text
    bot.send_message(message.chat.id, "درخواستت ثبت شد و برای بررسی به ادمین ارسال شد.")
    send_request_to_admin(message.chat.id)

def send_request_to_admin(user_id):
    data = user_data[user_id]
    caption = (
        f"درخواست اکانت:\n\n"
        f"🧩 اسکین‌های دلخواه: {data['requested_skins']}\n"
        f"💰 حداکثر قیمت: {data['max_price']} تومان\n"
        f"👤 ارسال‌کننده: @{data.get('username') or 'نامشخص'}"
    )

    markup = types.InlineKeyboardMarkup()
    approve_button = types.InlineKeyboardButton("✅ تأیید درخواست (کد دلخواه)", callback_data=f"reqapprove_{user_id}")
    reject_button = types.InlineKeyboardButton("❌ رد درخواست (نوشتن دلیل)", callback_data=f"reqreject_{user_id}")
    markup.add(approve_button, reject_button)

    bot.send_message(ADMIN_ID, caption, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('reqapprove_') or call.data.startswith('reqreject_'))
def handle_request_callback(call):
    parts = call.data.split('_')
    action = parts[0]
    user_id = int(parts[1])

    if user_id not in user_data:
        bot.answer_callback_query(call.id, "اطلاعات درخواست یافت نشد.")
        return

    if action == 'reqapprove':
        bot.send_message(ADMIN_ID, "✅ لطفاً یک کد دلخواه برای این درخواست وارد کنید:")
        pending_codes[ADMIN_ID] = {'user_id': user_id, 'message_id': call.message.message_id}
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    elif action == 'reqreject':
        bot.send_message(ADMIN_ID, "❌ لطفاً دلیل رد درخواست را بنویسید:")
        pending_rejections[ADMIN_ID] = {'user_id': user_id, 'message_id': call.message.message_id}
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and ADMIN_ID in pending_codes)
def handle_code_entry(message):
    user_id = pending_codes[ADMIN_ID]['user_id']
    code = message.text.strip()

    text = f"درخواست شما تایید شد.\nکد تایید: {code}\nلطفا این کد را به ادمین ارسال کنید."
    bot.send_message(user_id, text)

    post = (
        f"✅ درخواست تأیید شده:\n\n"
        f"🧩 اسکین‌ها: {user_data[user_id]['requested_skins']}\n"
        f"💰 قیمت: {user_data[user_id]['max_price']} تومان\n"
        f"📎 کد تایید: {code}"
    )
    bot.send_message(CHANNEL_USERNAME, post)

    pending_codes.pop(ADMIN_ID)

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and ADMIN_ID in pending_rejections)
def handle_reject_reason(message):
    user_id = pending_rejections[ADMIN_ID]['user_id']
    reason = message.text.strip()

    bot.send_message(user_id, f"درخواست شما رد شد.\nدلیل: {reason}")
    pending_rejections.pop(ADMIN_ID)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

# داخل handler ادمین اصلی (handle_admin_text) نیازی به تغییر خاص نیست چون همون متغیرهای pending_codes و pending_rejections استفاده می‌شن
