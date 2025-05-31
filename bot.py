import telebot
from telebot import types
from flask import Flask, request
import threading

API_TOKEN = '7933020801:AAHvfiIlfg5frqosVCgY1n1pUFElwQsr7B8'
ADMIN_ID = 6697070308  # آی‌دی عددی ادمین
CHANNEL_USERNAME = '@filmskina'  # آیدی کانال یا گروه

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

ads = []  # لیست ذخیره آگهی‌ها در حافظه

# ---------- عضویت اجباری ----------
CHANNEL_ID = '@Mobile_Legend_IR'  # کانال برای عضویت اجباری

def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'creator', 'administrator']
    except:
        return False

# ---------- ثبت آگهی ----------
user_states = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "سلام! برای ثبت آگهی، دستور /post رو بزنید.")

@bot.message_handler(commands=['post'])
def post_ad(message):
    if not is_member(message.from_user.id):
        bot.send_message(message.chat.id, f"برای ثبت آگهی، ابتدا عضو کانال {CHANNEL_ID} شوید.")
        return
    user_states[message.from_user.id] = {'step': 'collection'}
    bot.send_message(message.chat.id, "نام کالکشن را وارد کنید:")

@bot.message_handler(content_types=['text', 'video'])
def handle_message(message):
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if state:
        step = state['step']

        if step == 'collection':
            state['collection'] = message.text
            state['step'] = 'skins'
            bot.send_message(message.chat.id, "اسکین‌های مهم را وارد کنید:")
        elif step == 'skins':
            state['skins'] = message.text
            state['step'] = 'description'
            bot.send_message(message.chat.id, "توضیحات اکانت را وارد کنید:")
        elif step == 'description':
            state['description'] = message.text
            state['step'] = 'price'
            bot.send_message(message.chat.id, "قیمت فروش را وارد کنید:")
        elif step == 'price':
            state['price'] = message.text
            state['step'] = 'video'
            bot.send_message(message.chat.id, "یک ویدیو از اسکین‌ها ارسال کنید:")
        elif step == 'video' and message.content_type == 'video':
            state['video'] = message.video.file_id
            ad_id = len(ads) + 1
            state['ad_id'] = ad_id
            ads.append(state)

            # ارسال برای ادمین تایید
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("تایید آگهی", callback_data=f"approve_{ad_id}"),
                       types.InlineKeyboardButton("رد آگهی", callback_data=f"reject_{ad_id}"))

            ad_text = f"""📌 کالکشن: {state['collection']}
🌟 اسکین‌های مهم: {state['skins']}
📝 توضیحات: {state['description']}
💰 قیمت فروش: {state['price']}"""

            bot.send_video(ADMIN_ID, state['video'], caption=ad_text, reply_markup=markup)
            bot.send_message(message.chat.id, "آگهی شما ارسال شد و در انتظار تایید ادمین است.")
            user_states.pop(user_id)
        else:
            bot.send_message(message.chat.id, "لطفاً مراحل را به ترتیب انجام دهید.")
    else:
        bot.send_message(message.chat.id, "برای ثبت آگهی، دستور /post را بزنید.")

# ---------- تایید یا رد آگهی ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('reject_'))
def handle_approval(call):
    ad_id = int(call.data.split('_')[1])
    ad = next((ad for ad in ads if ad['ad_id'] == ad_id), None)

    if ad:
        if call.data.startswith('approve_'):
            # ارسال به کانال
            ad_text = f"""📌 کالکشن: {ad['collection']}
🌟 اسکین‌های مهم: {ad['skins']}
📝 توضیحات: {ad['description']}
💰 قیمت فروش: {ad['price']}"""
            bot.send_video(CHANNEL_USERNAME, ad['video'], caption=ad_text)
            bot.send_message(call.message.chat.id, "✅ آگهی تایید و منتشر شد.")
            user_id = [k for k, v in user_states.items() if v.get('ad_id') == ad_id]
            if user_id:
                bot.send_message(user_id[0], "✅ آگهی شما تایید و منتشر شد.")
        else:
            bot.send_message(call.message.chat.id, "❌ آگهی رد شد.")

# ---------- Flask برای وبهوک ----------
@app.route('/', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'ok', 200

def run():
    app.run(host='0.0.0.0', port=5000)

def start_bot():
    bot.polling(non_stop=True)

threading.Thread(target=run).start()
threading.Thread(target=start_bot).start()
