import telebot
from telebot import types
from flask import Flask, request

TOKEN = "7933020801:AAHvfiIlfg5frqosVCgY1n1pUFElwQsr7B8"
ADMIN_ID = 6697070308  # شناسه ادمین
CHANNEL_USERNAME = "@filmskina"
CHANNEL_LINK = "https://t.me/filmskina"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ذخیره اطلاعات آگهی‌های کاربر به صورت موقت
user_ads = {}

# وضعیت منتظر تایید یا رد ادمین
pending_approval = {}
pending_reject = {}

# ----- منوی اصلی -----
def send_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("ثبت آگهی"),
        types.KeyboardButton("اکانت درخواستی"),
        types.KeyboardButton("مشاهده آگهی‌ها"),
        types.KeyboardButton("بازگشت")
    )
    bot.send_message(chat_id, "لطفاً یک گزینه انتخاب کنید:", reply_markup=markup)

# ----- بررسی بازگشت -----
def check_back(message):
    if message.text == "بازگشت":
        send_main_menu(message.chat.id)
        return True
    return False

# ----- شروع ربات -----
@bot.message_handler(commands=['start', 'menu'])
def start_handler(message):
    send_main_menu(message.chat.id)

# ----- هندل دکمه‌های منو -----
@bot.message_handler(func=lambda m: m.text in ["ثبت آگهی", "اکانت درخواستی", "مشاهده آگهی‌ها", "بازگشت"])
def main_menu_handler(message):
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

    elif message.text == "بازگشت":
        send_main_menu(message.chat.id)

# ----- مراحل ثبت آگهی -----
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
    caption = f"آگهی جدید:\n" \
              f"کالکشن: {ad['collection']}\n" \
              f"اسکین‌های مهم: {ad['key_skins']}\n" \
              f"توضیحات: {ad['description']}\n" \
              f"قیمت: {ad['price']} تومان\n" \
              f"فرستنده: @{message.from_user.username or message.from_user.id}"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تایید و ارسال کد", callback_data=f"approve_{message.chat.id}"),
        types.InlineKeyboardButton("❌ رد آگهی", callback_data=f"reject_{message.chat.id}")
    )

    bot.send_video(ADMIN_ID, ad['video_id'], caption=caption, reply_markup=markup)
    bot.send_message(message.chat.id, "آگهی شما برای بررسی به ادمین ارسال شد.")
    send_main_menu(message.chat.id)

# ----- تایید و رد ادمین -----
@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('reject_'))
def admin_callback_handler(call):
    user_id = int(call.data.split('_')[1])
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "شما ادمین نیستید!")
        return

    if call.data.startswith('approve_'):
        bot.send_message(ADMIN_ID, "لطفاً کد تایید آگهی را وارد کنید:")
        pending_approval[ADMIN_ID] = user_id
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    elif call.data.startswith('reject_'):
        bot.send_message(ADMIN_ID, "لطفاً دلیل رد آگهی را بنویسید:")
        pending_reject[ADMIN_ID] = user_id
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID)
def admin_text_handler(message):
    if ADMIN_ID in pending_approval:
        user_id = pending_approval.pop(ADMIN_ID)
        ad = user_ads.get(user_id)
        if not ad:
            bot.send_message(ADMIN_ID, "آگهی یافت نشد!")
            return
        code = message.text.strip()
        caption = f"آگهی تایید شده:\n" \
                  f"کالکشن: {ad['collection']}\n" \
                  f"اسکین‌های مهم: {ad['key_skins']}\n" \
                  f"توضیحات: {ad['description']}\n" \
                  f"قیمت: {ad['price']} تومان\n" \
                  f"کد آگهی: {code}"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("ارتباط با ادمین", url=f"tg://user?id={ADMIN_ID}"))

        bot.send_video(CHANNEL_USERNAME, ad['video_id'], caption=caption, reply_markup=markup)
        bot.send_message(user_id, f"آگهی شما تایید و منتشر شد.\nکد آگهی: {code}")

    elif ADMIN_ID in pending_reject:
        user_id = pending_reject.pop(ADMIN_ID)
        reason = message.text.strip()
        bot.send_message(user_id, f"آگهی شما توسط ادمین رد شد.\nدلیل: {reason}")

# ----- دریافت اکانت درخواستی -----
def receive_account_request(message):
    if check_back(message): return
    bot.send_message(ADMIN_ID, f"درخواست اکانت درخواستی از @{message.from_user.username or message.from_user.id}:\n{message.text}")
    bot.send_message(message.chat.id, "درخواست شما ثبت شد. پس از بررسی با شما تماس گرفته می‌شود.")
    send_main_menu(message.chat.id)

# ---------- اجرا در فلَسک ----------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

def run():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    import threading
    threading.Thread(target=run).start()
    bot.infinity_polling()
