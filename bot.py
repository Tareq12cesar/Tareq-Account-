import telebot
from telebot import types
from flask import Flask, request
import threading

TOKEN = '7933020801:AAHvfiIlfg5frqosVCgY1n1pUFElwQsr7B8'
ADMIN_ID = 6697070308  # شناسه ادمین
CHANNEL_USERNAME = '@filmskina'  # کانال جوین اجباری
CHANNEL_LINK = 'https://t.me/TareqMlbb'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_ads = {}
pending_approval = {}
pending_reject = {}

# ====== بررسی جوین اجباری ======
def check_membership(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['member', 'creator', 'administrator']
    except:
        return False

def force_join(message):
    if not check_membership(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("✅ عضویت در کانال", url=CHANNEL_LINK)
        markup.add(btn)
        bot.send_message(message.chat.id, "❗️برای استفاده از ربات، ابتدا در کانال عضو شوید:", reply_markup=markup)
        return True
    return False

# ====== منوی اصلی ======
def send_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("ثبت آگهی"),
        types.KeyboardButton("اکانت درخواستی"),
        types.KeyboardButton("مشاهده آگهی‌ها"),
        types.KeyboardButton("قیمت یاب اکانت"),
        types.KeyboardButton("بازگشت")
    )
    bot.send_message(chat_id, "سلام! لطفاً گزینه مورد نظر را انتخاب کنید:", reply_markup=markup)

# ====== چک بازگشت ======
def check_back(message):
    if message.text == "بازگشت":
        send_main_menu(message.chat.id)
        return True
    return False

# ====== استارت ======
@bot.message_handler(commands=['start', 'menu'])
def start_handler(message):
    if force_join(message):
        return
    send_main_menu(message.chat.id)

# ====== هندل دکمه‌های منو ======
@bot.message_handler(func=lambda m: True)
def main_menu_handler(message):
    if force_join(message):
        return

    if message.text == "ثبت آگهی":
        user_ads[message.chat.id] = {}
        bot.send_message(message.chat.id, "نام کالکشن را وارد کنید:")
        bot.register_next_step_handler(message, get_collection_name)

    elif message.text == "اکانت درخواستی":
        bot.send_message(message.chat.id, "مشخصات اکانت درخواستی و حداکثر قیمت را ارسال کنید:")
        bot.register_next_step_handler(message, receive_account_request)

    elif message.text == "مشاهده آگهی‌ها":
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("🔗 رفتن به کانال آگهی‌ها", url=CHANNEL_LINK)
        markup.add(btn)
        bot.send_message(message.chat.id, "برای مشاهده آگهی‌ها روی دکمه زیر کلیک کنید:", reply_markup=markup)

    elif message.text == "قیمت یاب اکانت":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Supreme", "Grand", "Exquisite", "Deluxe", "بازگشت")
        bot.send_message(message.chat.id, "نوع اسکین را انتخاب کنید:", reply_markup=markup)
        bot.register_next_step_handler(message, price_handler)

    else:
        bot.send_message(message.chat.id, "لطفاً یک گزینه از منو انتخاب کنید:")

# ====== مراحل ثبت آگهی ======
def get_collection_name(message):
    if check_back(message): return
    user_ads[message.chat.id]['collection'] = message.text
    bot.send_message(message.chat.id, "اسکین‌های مهم را وارد کنید:")
    bot.register_next_step_handler(message, get_key_skins)

def get_key_skins(message):
    if check_back(message): return
    user_ads[message.chat.id]['key_skins'] = message.text
    bot.send_message(message.chat.id, "توضیحات کامل اکانت را وارد کنید:")
    bot.register_next_step_handler(message, get_description)

def get_description(message):
    if check_back(message): return
    user_ads[message.chat.id]['description'] = message.text
    bot.send_message(message.chat.id, "قیمت فروش را وارد کنید (تومان):")
    bot.register_next_step_handler(message, get_price)

def get_price(message):
    if check_back(message): return
    user_ads[message.chat.id]['price'] = message.text
    bot.send_message(message.chat.id, "لطفاً یک ویدئو از اکانت ارسال کنید:")
    bot.register_next_step_handler(message, get_video)

def get_video(message):
    if check_back(message): return
    if message.content_type != 'video':
        bot.send_message(message.chat.id, "لطفاً فقط ویدئو ارسال کنید!")
        bot.register_next_step_handler(message, get_video)
        return
    user_ads[message.chat.id]['video_id'] = message.video.file_id

    ad = user_ads[message.chat.id]
    caption = f"آگهی جدید:\nکالکشن: {ad['collection']}\nاسکین‌ها: {ad['key_skins']}\nتوضیحات: {ad['description']}\nقیمت: {ad['price']} تومان\nارسال‌کننده: @{message.from_user.username or message.from_user.id}"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تایید", callback_data=f"approve_{message.chat.id}"),
               types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{message.chat.id}"))
    bot.send_video(ADMIN_ID, ad['video_id'], caption=caption, reply_markup=markup)
    bot.send_message(message.chat.id, "آگهی شما برای بررسی به ادمین ارسال شد.")
    send_main_menu(message.chat.id)

# ====== مدیریت ادمین ======
@bot.callback_query_handler(func=lambda call: True)
def admin_callback(call):
    user_id = int(call.data.split('_')[1])
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "شما ادمین نیستید!")
        return

    if call.data.startswith('approve_'):
        bot.send_message(ADMIN_ID, "لطفاً کد تایید را وارد کنید:")
        pending_approval[ADMIN_ID] = user_id
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    elif call.data.startswith('reject_'):
        bot.send_message(ADMIN_ID, "لطفاً دلیل رد آگهی را وارد کنید:")
        pending_reject[ADMIN_ID] = user_id
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID)
def admin_response(message):
    if ADMIN_ID in pending_approval:
        user_id = pending_approval.pop(ADMIN_ID)
        ad = user_ads.get(user_id)
        code = message.text.strip()
        caption = f"آگهی تایید شده:\nکالکشن: {ad['collection']}\nاسکین‌ها: {ad['key_skins']}\nتوضیحات: {ad['description']}\nقیمت: {ad['price']} تومان\nکد آگهی: {code}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("ارتباط با ادمین", url=f"tg://user?id={ADMIN_ID}"))
        bot.send_video(CHANNEL_USERNAME, ad['video_id'], caption=caption, reply_markup=markup)
        bot.send_message(user_id, f"آگهی شما تایید شد. کد آگهی: {code}")

    elif ADMIN_ID in pending_reject:
        user_id = pending_reject.pop(ADMIN_ID)
        bot.send_message(user_id, f"آگهی شما توسط ادمین رد شد.\nدلیل: {message.text.strip()}")

# ====== قیمت‌یاب ======
def price_handler(message):
    if check_back(message): return
    skin_type = message.text
    prices = {"Supreme": 1200000, "Grand": 500000, "Exquisite": 300000, "Deluxe": 100000}

    if skin_type == "Deluxe":
        bot.send_message(message.chat.id, "تعداد اسکین‌های Deluxe را وارد کنید:")
        bot.register_next_step_handler(message, calculate_deluxe)
    elif skin_type in prices:
        bot.send_message(message.chat.id, f"قیمت تقریبی هر اسکین {skin_type}: {prices[skin_type]} تومان\nتعداد اسکین‌های خود را وارد کنید:")
        bot.register_next_step_handler(message, lambda msg: calc_total(msg, prices[skin_type]))
    else:
        bot.send_message(message.chat.id, "گزینه معتبر انتخاب نشده است.")
        send_main_menu(message.chat.id)

def calculate_deluxe(message):
    try:
        count = int(message.text)
        if count < 20:
            price = count * 25000
        elif 20 <= count <= 40:
            price = 500000
        else:
            price = 700000
        bot.send_message(message.chat.id, f"✅ قیمت کل اسکین‌های Deluxe: {price} تومان")
    except:
        bot.send_message(message.chat.id, "عدد معتبر وارد کنید:")
        bot.register_next_step_handler(message, calculate_deluxe)
    send_main_menu(message.chat.id)

def calc_total(message, per_price):
    try:
        count = int(message.text)
        total = count * per_price
        bot.send_message(message.chat.id, f"✅ قیمت کل: {total} تومان")
    except:
        bot.send_message(message.chat.id, "عدد معتبر وارد کنید:")
        bot.register_next_step_handler(message, lambda msg: calc_total(msg, per_price))
    send_main_menu(message.chat.id)

# ====== اجرا ======
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "!", 200

def run():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    threading.Thread(target=run).start()
    bot.infinity_polling()
