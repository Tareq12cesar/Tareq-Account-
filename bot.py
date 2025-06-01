# ======= Import Libraries =======
import telebot
from telebot import types
from flask import Flask, request
import threading

# ======= تنظیمات اولیه =======
BOT_TOKEN = 'AAHvfiIlfg5frqosVCgY1n1pUFElwQsr7B8'
ADMIN_ID = 6697070308
CHANNEL_USERNAME = '@filmskina'
CHANNEL_LINK = 'https://t.me/filmskina'

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}
pending_codes = {}
pending_rejections = {}
price_data = {}

PRICES = {
    'Supreme': 1200000,
    'Grand': 500000,
    'Exquisite': 300000
}

EXPLANATIONS = {
    'Supreme': "✅ این دسته شامل اسکین‌های لجند می‌باشد.\n\nچندتا اسکین از این دسته داری؟",
    'Grand': "✅ این دسته شامل اسکین‌های کوف، جوجوتسو، سوپر هیرو، استاروارز، ناروتو، ابیس و... می‌باشد.(از اسکین های پرایم فقط راجر رو اینجا وارد کنید و بقیه رو در قسمت Exquisite وارد کنید)\n\n❌ توجه داشته باشید اسکین‌های رایگان این دسته مثل کارینا، تاموز، فلورین، راجر و... رو حساب نکنید.\n\nچندتا اسکین از این دسته داری؟",
    'Exquisite': "✅ این دسته شامل اسکین‌های کالکتور، لاکی باکس و کلادز می‌باشد(اسکین های پرایم در این قسمت وارد کنید).\n\n❌ توجه داشته باشید اسکین‌های رایگان این دسته مثل ناتالیا و... رو حساب نکنید.\n\nچندتا اسکین از این دسته داری؟",
    'Deluxe': "✅ این دسته شامل اسکین‌های زودیاک، لایتبورن، اپیک شاپ و... می‌باشد.\n\nچندتا اسکین از این دسته داری؟"
}

# ======= منو اصلی =======
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

# ======= چک کردن بازگشت =======
def check_back(message):
    if message.text == "بازگشت":
        send_menu(message.chat.id)
        return True
    return False

# ======= دکمه‌ها =======
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
        price_data[message.chat.id] = {'skins': {}}
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Supreme", "Grand", "Exquisite", "Deluxe", "پایان", "بازگشت")
        bot.send_message(message.chat.id, "✅ نوع اسکینت رو انتخاب کن:", reply_markup=markup)
        bot.register_next_step_handler(message, handle_skin_type)
    elif message.text == "بازگشت":
        send_menu(message.chat.id)

# ======= قیمت‌یاب جدید =======
def handle_skin_type(message):
    if check_back(message): return
    chat_id = message.chat.id
    text = message.text

    if text == "پایان":
        show_summary(message)
        return
    if text not in PRICES and text != "Deluxe":
        bot.send_message(chat_id, "❌ لطفاً یکی از اسکین‌های موجود یا گزینه 'پایان' رو انتخاب کن.")
        bot.register_next_step_handler(message, handle_skin_type)
        return

    price_data[chat_id]['current_skin'] = text
    bot.send_message(chat_id, EXPLANATIONS[text])
    bot.register_next_step_handler(message, handle_skin_count)

def handle_skin_count(message):
    if check_back(message): return
    chat_id = message.chat.id
    text = message.text
    try:
        count = int(text)
        skin = price_data[chat_id]['current_skin']

        if skin in price_data[chat_id]['skins']:
            price_data[chat_id]['skins'][skin] += count
        else:
            price_data[chat_id]['skins'][skin] = count

        bot.send_message(chat_id, f"✅ اسکین {skin} با تعداد {count} اضافه شد! برای ادامه انتخاب کن یا 'پایان' رو بزن.")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Supreme", "Grand", "Exquisite", "Deluxe", "پایان", "بازگشت")
        bot.send_message(chat_id, "یک اسکین دیگه انتخاب کن یا 'پایان' رو بزن:", reply_markup=markup)
        bot.register_next_step_handler(message, handle_skin_type)

    except:
        bot.send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کن.")
        bot.register_next_step_handler(message, handle_skin_count)

def show_summary(message):
    chat_id = message.chat.id
    skins = price_data.get(chat_id, {}).get('skins', {})
    if not skins:
        bot.send_message(chat_id, "❌ هنوز هیچ اسکینی انتخاب نکردی!")
        send_menu(chat_id)
        return

    summary = ""
    total_price = 0

    for skin, count in skins.items():
        if skin == "Deluxe":
            if count < 20:
                price = count * 25000
            elif 20 <= count <= 40:
                price = 500000
            else:
                price = 700000
        else:
            price = PRICES[skin] * count

        summary += f"{skin}: {count}\n"
        total_price += price

    bot.send_message(chat_id, f"✅ اسکین‌هایی که انتخاب کردی:\n{summary}\nقیمت کل: {total_price:,} تومان\n\nقیمت بالا ارزش اکانت شماست\nبرای ثبت آگهی تو کانال، قیمت فروش رو خودتون تعیین می‌کنید", reply_markup=types.ReplyKeyboardRemove())
    send_menu(chat_id)

# ======= بقیه کد ثبت آگهی و مدیریت ادمین (همونطور که در کد اصلی بود) =======

# ======= اجرای ربات =======
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
