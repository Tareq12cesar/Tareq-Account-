import telebot
from telebot import types
from flask import Flask, request
import threading

# ======= تنظیمات اولیه =======
BOT_TOKEN = '7933020801:AAHvfiIlfg5frqosVCgY1n1pUFElwQsr7B8'
ADMIN_ID = 6697070308  # آیدی عددی ادمین
CHANNEL_USERNAME = '@filmskina'  # یوزرنیم کانال
CHANNEL_LINK = 'https://t.me/filmskina'

# ======= تنظیمات عضویت اجباری =======
REQUIRED_CHANNELS = [
    {'username': '@TareqMlbb', 'link': 'https://t.me/TareqMlbb'},
    {'username': '@Mobile_Legend_ir', 'link': 'https://t.me/Mobile_Legend_ir'},
    {'username': '@Shop_MLBB', 'link': 'https://t.me/Shop_MLBB'},
]

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
def is_user_joined(user_id):
    for ch in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(ch['username'], user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

def send_force_join_prompt(chat_id):
    markup = types.InlineKeyboardMarkup()
    for ch in REQUIRED_CHANNELS:
        markup.add(types.InlineKeyboardButton(f"📢 عضویت در {ch['username']}", url=ch['link']))
    markup.add(types.InlineKeyboardButton("🔄 بررسی عضویت", callback_data="check_join"))
    bot.send_message(chat_id, "❗ برای استفاده از ربات، ابتدا عضو همه‌ی کانال‌های زیر شوید:", reply_markup=markup)
# ======= دستور /start و /menu =======
@bot.message_handler(commands=['start'])
def menu_command(message):
    user_id = message.from_user.id

    if not is_user_joined(user_id):
        send_force_join_prompt(message.chat.id)
        return

    send_menu(user_id)

# ======= هندل کردن دکمه‌ها =======
@bot.message_handler(func=lambda message: message.text in ["ثبت آگهی", "اکانت درخواستی", "مشاهده آگهی‌ها", "قیمت یاب اکانت", "بازگشت"])
def handle_buttons(message):
    if not is_user_joined(message.from_user.id):
        send_force_join_prompt(message.chat.id)
        return

    if message.text == "ثبت آگهی":
        user_data[message.from_user.id] = {'user_id': message.from_user.id, 'username': message.from_user.username}
        bot.send_message(message.chat.id, "لطفاً نام کالکشن خود را وارد کنید:")
        bot.register_next_step_handler(message, get_collection)
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
    elif message.text == "اکانت درخواستی":
        start_buy_request(message)
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
            summary_lines.append(f"💰 {skin_type}: {count}")
            final_message = "💵 قیمت نهایی کل اسکین‌ها:\n\n" + "\n".join(summary_lines) + f"\n\n💰 جمع کل: {total_price:,} تومان\n\n💡 قیمت بالا ارزش اکانت شماست\nبرای ثبت آگهی تو کانال، قیمت فروش رو خودتون تعیین می‌کنید."
        bot.send_message(message.chat.id, final_message)
        user_data.pop(message.chat.id, None)
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

# ======= سیستم اکانت درخواستی =======

@bot.message_handler(func=lambda message: message.text and "اکانت درخواستی" in message.text)
def start_buy_request(message):
    user_data[message.chat.id] = {'username': message.from_user.username}
    bot.send_message(message.chat.id, "🔍 اسکین‌هایی که می‌خوای تو اکانت باشه رو تایپ کن:")
    bot.register_next_step_handler(message, get_requested_skins)


def get_requested_skins(message):
    if check_back(message): return
    user_data[message.chat.id]['requested_skins'] = message.text
    bot.send_message(message.chat.id, "💰 حداکثر قیمتی که می‌خوای هزینه کنی رو وارد کن:")
    bot.register_next_step_handler(message, confirm_request)


def confirm_request(message):
    if check_back(message): return
    user_data[message.chat.id]['max_budget'] = message.text

    data = user_data[message.chat.id]
    caption = f"🛒 خلاصه درخواست خرید شما:\n\n" \
              f"🎯 اسکین‌های موردنظر: {data['requested_skins']}\n" \
              f"💰 بودجه: {data['max_budget']} تومان\n\n" \
              f"آیا مایل به ارسال این درخواست برای بررسی ادمین هستید؟"

    markup = types.InlineKeyboardMarkup()
    confirm_btn = types.InlineKeyboardButton("✅ تایید و ارسال به ادمین", callback_data=f"confirm_send_{message.chat.id}")
    cancel_btn = types.InlineKeyboardButton("❌ لغو", callback_data="cancel_request")
    markup.add(confirm_btn, cancel_btn)

    bot.send_message(message.chat.id, caption, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_send_") or call.data == "cancel_request")
def handle_request_confirmation(call):
    if call.data == "cancel_request":
        bot.edit_message_text("❌ درخواست لغو شد.", call.message.chat.id, call.message.message_id)
        user_data.pop(call.message.chat.id, None)
        return

    user_id = int(call.data.split('_')[2])
    send_request_to_admin(user_id)
    bot.edit_message_text("✅ درخواست شما برای بررسی به ادمین ارسال شد.", call.message.chat.id, call.message.message_id)


def send_request_to_admin(user_id):
    data = user_data[user_id]
    caption = f"🛒 درخواست خرید جدید:\n\n" \
              f"🎯 اسکین‌های موردنظر: {data['requested_skins']}\n" \
              f"💰 بودجه: {data['max_budget']} تومان\n\n" \
              f"👤 ارسال‌کننده: @{data['username'] or 'نامشخص'}"

    markup = types.InlineKeyboardMarkup()
    approve_button = types.InlineKeyboardButton("✅ تأیید درخواست", callback_data=f"buyapprove_{user_id}")
    reject_button = types.InlineKeyboardButton("❌ رد درخواست", callback_data=f"buyreject_{user_id}")
    markup.add(approve_button, reject_button)

    bot.send_message(ADMIN_ID, caption, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("buyapprove_") or call.data.startswith("buyreject_"))
def handle_buy_request_response(call):
    print("👀 admin clicked buyapprove/buyreject")  # برای تست لاگ

    parts = call.data.split('_')
    action = parts[0]  # buyapprove یا buyreject
    user_id = int(parts[1])

    data = user_data.get(user_id)
    if not data:
        bot.answer_callback_query(call.id, "❌ اطلاعات درخواست یافت نشد.")
        return

    if action == 'buyapprove':
        bot.send_message(ADMIN_ID, "✅ لطفاً یک کد دلخواه برای این درخواست وارد کنید:")
        pending_codes[ADMIN_ID] = {
            'user_id': user_id,
            'message_id': call.message.message_id,
            'type': 'buy'
        }
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    elif action == 'buyreject':
        bot.send_message(ADMIN_ID, "❌ لطفاً دلیل رد درخواست را بنویسید:")
        pending_rejections[ADMIN_ID] = {
            'user_id': user_id,
            'message_id': call.message.message_id,
            'type': 'buy'
        }
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        


@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID)
def handle_admin_text(message):
    if ADMIN_ID in pending_codes:
        code = message.text.strip()
        pending = pending_codes.pop(ADMIN_ID)
        user_id = pending['user_id']
        req_type = pending.get('type', 'ad')

        data = user_data.get(user_id)
        if not data:
            bot.send_message(ADMIN_ID, "❌ اطلاعات کاربر یافت نشد.")
            return

        if req_type == 'ad':
            caption = f"📢 آگهی تأیید شده:\n\n" \
                      f"🧩 کالکشن: {data['collection']}\n" \
                      f"🎮 اسکین‌های مهم: {data['key_skins']}\n" \
                      f"📝 توضیحات: {data['description']}\n" \
                      f"💰 قیمت: {data['price']} تومان\n" \
                      f"🆔 کد آگهی: {code}"

            markup = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton("ارتباط با ادمین", url=f"tg://user?id={ADMIN_ID}")
            markup.add(btn)

            bot.send_video(CHANNEL_USERNAME, data['video'], caption=caption, reply_markup=markup)
            bot.send_message(user_id, f"✅ آگهی شما تأیید و در کانال منتشر شد.\n\n"
                          f"کد آگهی: {code}\n\n"
                          f"این پیام رو برای ادمین بفرستید")
            
        elif req_type == 'buy':
            caption = f"🛒 درخواست خرید تأیید شده:\n\n" \
                      f"🎯 اسکین‌های موردنظر: {data['requested_skins']}\n" \
                      f"💰 بودجه: {data['max_budget']} تومان\n" \
                      f"🆔 کد درخواست: {code}"

            markup = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton("ارتباط با ادمین", url=f"tg://user?id={ADMIN_ID}")
            markup.add(btn)
            
            bot.send_message(CHANNEL_USERNAME, caption, reply_markup=markup)
            bot.send_message(user_id, f"✅ درخواست خرید شما تأیید و در کانال منتشر شد.\n\n"
                          f"کد درخواست: {code}\n\n"
                          f"این پیام رو برای ادمین بفرستید")
    
    elif ADMIN_ID in pending_rejections:
        reason = message.text.strip()
        pending = pending_rejections.pop(ADMIN_ID)
        user_id = pending['user_id']
        req_type = pending.get('type', 'ad')

        if req_type == 'ad':
            bot.send_message(user_id, f"❌ آگهی شما رد شد.\nدلیل: {reason}")
        elif req_type == 'buy':
            bot.send_message(user_id, f"❌ درخواست خرید شما رد شد.\nدلیل: {reason}")

# ======= اجرای ربات با Flask =======

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_user_membership(call):
    user_id = call.from_user.id
    if is_user_joined(user_id):
        bot.edit_message_text("✅ عضویت شما تأیید شد. حالا می‌تونید از ربات استفاده کنید.",
                              call.message.chat.id, call.message.message_id)
        send_menu(user_id)
    else:
        bot.answer_callback_query(call.id, "❗ هنوز در همه کانال‌ها عضو نشدی!", show_alert=True)

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
