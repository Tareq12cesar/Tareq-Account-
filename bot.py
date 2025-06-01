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
    if check_back(message):
        return

    text = message.text.strip()
    chat_id = message.chat.id

    if text == "قیمت نهایی":
        if chat_id not in user_data or 'counts' not in user_data[chat_id] or not user_data[chat_id]['counts']:
            bot.send_message(chat_id, "❌ اطلاعات کافی برای محاسبه قیمت وجود ندارد. لطفاً ابتدا نوع اسکین و تعداد را انتخاب کنید.")
            send_skin_selection_menu(chat_id)
            return
        
        counts = user_data[chat_id]['counts']

        fixed_prices = {
            "Supreme": 1200000,
            "Grand": 500000,
            "Exquisite": 300000
        }

        total_price = 0
        for skin_type, count in counts.items():
            if skin_type in fixed_prices:
                total_price += fixed_prices[skin_type] * count
            else:  # Deluxe
                if count < 20:
                    total_price += 25000 * count
                elif 20 <= count <= 39:
                    total_price += 500000
                else:
                    total_price += 700000

        final_message = (
            f"💰 قیمت کل اسکین‌های شما:\n\n"
            + "\n".join([f"{stype}: تعداد {cnt}" for stype, cnt in counts.items()]) + "\n\n"
            + f"💵 مبلغ کل: {total_price:,} تومان\n\n"
            + "💡 قیمت بالا ارزش اکانت شماست\n"
            + "برای ثبت آگهی تو کانال، قیمت فروش رو خودتون تعیین می‌کنید."
        )
        bot.send_message(chat_id, final_message)
        send_skin_selection_menu(chat_id)
        return

    valid_skin_types = ["Supreme", "Grand", "Exquisite", "Deluxe"]
    if text in valid_skin_types:
        if chat_id not in user_data:
            user_data[chat_id] = {'counts': {}}
        user_data[chat_id]['current_skin_type'] = text  # ذخیره موقت برای مرحله دریافت تعداد

        explanations = {
            "Supreme": "✅ این دسته شامل اسکین‌های لجند می‌باشد.\n\nچندتا اسکین از این دسته داری؟",
            "Grand": "✅ این دسته شامل اسکین‌های کوف، جوجوتسو، سوپر هیرو، استاروارز، ناروتو، ابیس و... می‌باشد.\n(از اسکین‌های پرایم فقط راجر رو اینجا وارد کنید و بقیه رو در قسمت Exquisite وارد کنید)\n\n❌ توجه داشته باشید اسکین‌های رایگان این دسته مثل کارینا، تاموز، فلورین، راجر و... رو حساب نکنید.\n\nچندتا اسکین از این دسته داری؟",
            "Exquisite": "✅ این دسته شامل اسکین‌های کالکتور، لاکی باکس و کلادز می‌باشد (اسکین‌های پرایم در این قسمت وارد کنید).\n\n❌ توجه داشته باشید اسکین‌های رایگان این دسته مثل ناتالیا و... رو حساب نکنید.\n\nچندتا اسکین از این دسته داری؟",
            "Deluxe": "✅ این دسته شامل اسکین‌های زودیاک، لایتبورن، اپیک شاپ و... می‌باشد.\n\nچندتا اسکین از این دسته داری؟"
        }
        bot.send_message(chat_id, explanations[text])
        bot.register_next_step_handler(message, get_skin_count)
        return

    bot.send_message(chat_id, "❌ لطفاً از دکمه‌ها استفاده کنید.")
    send_skin_selection_menu(chat_id)

def get_skin_count(message):
    chat_id = message.chat.id
    try:
        count = int(message.text.strip())
        if count < 0:
            raise ValueError()
    except Exception:
        bot.send_message(chat_id, "❌ لطفاً فقط عدد مثبت وارد کنید. چندتا اسکین داری؟")
        bot.register_next_step_handler(message, get_skin_count)
        return

    skin_type = user_data[chat_id].get('current_skin_type')
    if not skin_type:
        bot.send_message(chat_id, "❌ خطا در دریافت نوع اسکین. لطفاً دوباره انتخاب کنید.")
        send_skin_selection_menu(chat_id)
        return

    if 'counts' not in user_data[chat_id]:
        user_data[chat_id]['counts'] = {}

    user_data[chat_id]['counts'][skin_type] = count
    user_data[chat_id]['current_skin_type'] = None

    bot.send_message(
        chat_id,
        "✅ اطلاعات ثبت شد.\n\nلطفاً نوع اسکین‌های خود را انتخاب کنید یا دکمه «قیمت نهایی» را بزنید."
    )
    send_skin_selection_menu(chat_id)

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
