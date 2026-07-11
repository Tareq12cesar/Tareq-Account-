import telebot
from telebot import types
from flask import Flask, request
import threading
import json
import os
import pymongo

# ======= تنظیمات اولیه =======
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7963209844:AAGT_OxFllzxsxeaudNkg0HX7_0DYd3Zyso')
ADMIN_ID = 6697070308  # آیدی عددی ادمین
CHANNEL_USERNAME = '@TareqMlbb'  # یوزرنیم کانال
CHANNEL_LINK = 'https://t.me/TareqMlbb'

# ======= تنظیمات سیستم موجودی کیف پول کاربر =======
COMMISSION_PERCENT = 5  # درصدی که از مبلغ کل معامله، به هر یک از طرفین (خریدار/فروشنده) به‌عنوان حق واسطه تعلق می‌گیرد
MIN_WITHDRAW_REQUEST = 50000  # حداقل موجودی لازم برای درخواست استفاده از موجودی (تومان)

# ======= تنظیمات عضویت اجباری =======
REQUIRED_CHANNELS = [
    {'username': '@TareqMlbb', 'link': 'https://t.me/TareqMlbb', 'title': 'کانال اول'},
    {'username': '@Mobile_Legend_ir', 'link': 'https://t.me/Mobile_Legend_ir', 'title': 'کانال دوم'},
    {'username': '@Shop_MLBB', 'link': 'https://t.me/Shop_MLBB', 'title': 'کانال سوم'},
]
# ==== پچ کردن آبجکت‌های جدید تلگرام که باعث ارور می‌شن ====

class ChatBoost:
    def __init__(self, boost_id=None, add_date=None, expiration_date=None):
        self.boost_id = boost_id
        self.add_date = add_date
        self.expiration_date = expiration_date

    @classmethod
    def de_json(cls, data):
        if not data:
            return None
        return cls(
            boost_id=data.get("boost_id"),
            add_date=data.get("add_date"),
            expiration_date=data.get("expiration_date")
        )

class ChatBoostRemoved:
    @classmethod
    def de_json(cls, data):
        return cls()

class ChatBoostSource:
    def __init__(self, source_type=None):
        self.source_type = source_type

    @classmethod
    def de_json(cls, data):
        if not data:
            return None
        return cls(source_type=data.get('source'))

class ChatBoostSourcePremium(ChatBoostSource):
    def __init__(self):
        super().__init__('premium')

import telebot.types
telebot.types.ChatBoost = ChatBoost
telebot.types.ChatBoostRemoved = ChatBoostRemoved
telebot.types.ChatBoostSource = ChatBoostSource
telebot.types.ChatBoostSourcePremium = ChatBoostSourcePremium

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}
pending_codes = {}
pending_rejections = {}
pending_deal_points = {}  # وضعیت موقت ادمین هنگام ثبت امتیاز معامله

# ======= لایه داده سیستم امتیاز (ذخیره‌سازی دائمی روی MongoDB Atlas) =======

MONGO_URI = os.environ.get('MONGO_URI')
mongo_client = pymongo.MongoClient(MONGO_URI) if MONGO_URI else None
mongo_db = mongo_client['mlbb_bot'] if mongo_client else None
users_collection = mongo_db['users'] if mongo_db is not None else None
members_collection = mongo_db['members'] if mongo_db is not None else None


def register_member(user_id, username=None):
    """هر کاربری که ربات رو استارت کنه رو (برای شمارش کل اعضا) ثبت می‌کند."""
    uid = str(user_id)
    members_collection.update_one(
        {'_id': uid},
        {'$set': {'username': username}},
        upsert=True
    )


def get_members_count():
    return members_collection.count_documents({})


def get_user_account(user_id, username=None):
    """رکورد حساب کاربری را برمی‌گرداند؛ اگر وجود نداشته باشد می‌سازد."""
    uid = str(user_id)
    doc = users_collection.find_one({'_id': uid})
    if not doc:
        doc = {'_id': uid, 'username': username, 'balance': 0, 'completed_deals': 0}
        users_collection.insert_one(doc)
    elif username and doc.get('username') != username:
        users_collection.update_one({'_id': uid}, {'$set': {'username': username}})
        doc['username'] = username
    return doc


def save_user_account(user_id, account):
    """رکورد حساب کاربری را (بعد از تغییر) دوباره ذخیره می‌کند."""
    uid = str(user_id)
    users_collection.update_one(
        {'_id': uid},
        {'$set': {
            'username': account.get('username'),
            'balance': account['balance'],
            'completed_deals': account['completed_deals'],
        }},
        upsert=True
    )


def add_deal_credit(user_id, deal_amount, username=None):
    """بعد از انجام موفق یک معامله، ۵٪ از مبلغ کل معامله را به‌عنوان حق واسطه به موجودی کاربر اضافه می‌کند."""
    commission = round(deal_amount * COMMISSION_PERCENT / 100)
    account = get_user_account(user_id, username)
    account['balance'] += commission
    account['completed_deals'] += 1
    save_user_account(user_id, account)
    return account, commission


def format_toman(amount):
    return f"{amount:,} تومان"


# ======= دستور ادمین برای ثبت معامله موفق و افزودن موجودی (با آیدی عددی کاربر) =======

@bot.message_handler(commands=['dealdone'])
def start_add_deal_points(message):
    if message.chat.id != ADMIN_ID:
        return
    bot.send_message(
        message.chat.id,
        "🆔 آیدی عددی کاربری که معامله براش انجام شد رو بفرست:"
    )
    bot.register_next_step_handler(message, ask_deal_points_amount)


def ask_deal_points_amount(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, "❌ آیدی نامعتبره. دوباره دستور /dealdone رو بزن.")
        return

    pending_deal_points[ADMIN_ID] = {'user_id': target_id}
    bot.send_message(
        message.chat.id,
        f"💰 مبلغ کل معامله چقدر بوده (تومان)؟ (به این کاربر {COMMISSION_PERCENT}٪ همین مبلغ تعلق می‌گیره)"
    )
    bot.register_next_step_handler(message, apply_deal_points)


def apply_deal_points(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        deal_amount = int(message.text.strip())
        if deal_amount <= 0:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفاً فقط یه عدد بزرگ‌تر از صفر بفرست. دوباره دستور /dealdone رو بزن.")
        pending_deal_points.pop(ADMIN_ID, None)
        return

    pending = pending_deal_points.pop(ADMIN_ID, None)
    if not pending:
        return

    target_id = pending['user_id']
    account, credited = add_deal_credit(target_id, deal_amount)

    bot.send_message(
        ADMIN_ID,
        f"✅ به حساب کاربر {target_id} مبلغ {format_toman(credited)} ({COMMISSION_PERCENT}٪ از {format_toman(deal_amount)}) اضافه شد.\n"
        f"موجودی جدید: {format_toman(account['balance'])} | {account['completed_deals']} معامله موفق"
    )
    try:
        bot.send_message(
            target_id,
            "🎉 تبریک! یک معامله موفق براتون ثبت شد.\n\n"
            f"💰 مبلغ اضافه‌شده: {format_toman(credited)}\n"
            f"👛 موجودی فعلی شما: {format_toman(account['balance'])}\n"
            f"✅ تعداد معاملات موفق شما: {account['completed_deals']}"
        )
    except Exception:
        pass  # کاربر شاید ربات رو بلاک کرده باشه


# ======= دستور ادمین برای صفر کردن موجودی بعد از استفاده کاربر از جایزه =======

pending_reset_balance = {}

@bot.message_handler(commands=['resetbalance'])
def start_reset_balance(message):
    if message.chat.id != ADMIN_ID:
        return
    bot.send_message(
        message.chat.id,
        "🆔 آیدی عددی کاربری که می‌خوای موجودیش رو صفر کنی رو بفرست:"
    )
    bot.register_next_step_handler(message, apply_reset_balance)


def apply_reset_balance(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, "❌ آیدی نامعتبره. دوباره دستور /resetbalance رو بزن.")
        return

    account = get_user_account(target_id)
    old_balance = account['balance']
    account['balance'] = 0
    save_user_account(target_id, account)

    bot.send_message(
        ADMIN_ID,
        f"✅ موجودی کاربر {target_id} صفر شد (قبلاً {format_toman(old_balance)} بود)."
    )
    try:
        bot.send_message(
            target_id,
            f"👛 موجودی شما ({format_toman(old_balance)}) استفاده شد و صفر شد."
        )
    except Exception:
        pass


# ======= نمایش حساب کاربری =======

def show_account(message):
    account = get_user_account(message.from_user.id, message.from_user.username)
    text = (
        "👤 حساب کاربری شما:\n\n"
        f"🆔 آیدی عددی: {message.from_user.id}\n"
        f"👛 موجودی شما: {format_toman(account['balance'])}\n"
        f"✅ تعداد معاملات موفق: {account['completed_deals']}\n\n"
        "ℹ️ موجودی قابل برداشت نقدی نیست. وقتی حداقل به "
        f"{format_toman(MIN_WITHDRAW_REQUEST)} برسید، می‌تونید درخواست بدید "
        "تا تو معامله بعدی‌تون لحاظ بشه.\n\n"
        f"💡 بابت هر معامله موفق هم خریدار هم فروشنده هرکدام {COMMISSION_PERCENT}٪ "
        "از حق واسطه رو دریافت می‌کنن."
    )
    markup = None
    if account['balance'] >= MIN_WITHDRAW_REQUEST:
        text += (
            "\n\n📩 موجودی شما به حد نصاب رسیده! برای درخواست، روی دکمه "
            "«درخواست استفاده از موجودی» که پایین همین پیام هست بزنید. "
            "بعدش خودمون تو معامله بعدی‌تون باهاتون هماهنگ می‌کنیم."
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            "📩 درخواست استفاده از موجودی",
            callback_data="request_withdraw"
        ))
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "request_withdraw")
def handle_withdraw_request(call):
    account = get_user_account(call.from_user.id, call.from_user.username)
    if account['balance'] < MIN_WITHDRAW_REQUEST:
        bot.answer_callback_query(call.id, "موجودی شما به حد نصاب نرسیده.", show_alert=True)
        return

    bot.answer_callback_query(call.id, "✅ درخواست شما ارسال شد.")
    bot.send_message(
        call.message.chat.id,
        "📩 درخواست شما برای استفاده از موجودی ثبت شد. تو معامله بعدی‌تون باهاتون هماهنگ می‌شه."
    )
    username_part = f"@{account['username']}" if account.get('username') else "بدون یوزرنیم"
    bot.send_message(
        ADMIN_ID,
        "📩 درخواست استفاده از موجودی:\n\n"
        f"🆔 آیدی: {call.from_user.id} ({username_part})\n"
        f"👛 موجودی فعلی: {format_toman(account['balance'])}\n\n"
        "این مبلغ رو تو معامله بعدی این کاربر لحاظ کن، بعد با /resetbalance صفرش کن."
    )


# ======= دکمه منو =======
def send_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("ثبت آگهی"),
        types.KeyboardButton("اکانت درخواستی"),
        types.KeyboardButton("مشاهده آگهی‌ها"),
        types.KeyboardButton("قیمت یاب اکانت"),
        types.KeyboardButton("👤 حساب کاربری"),
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
        markup.add(types.InlineKeyboardButton(f"📢 عضویت در {ch['title']}", url=ch['link']))
    markup.add(types.InlineKeyboardButton("🔄 بررسی عضویت", callback_data="check_join"))
    bot.send_message(chat_id, "📢 برای کار کردن با ربات، لطفا در کانال‌های زیر عضو شو و بعد دکمه «بررسی عضویت» رو بزن", reply_markup=markup)
# ======= دستور /start و /menu =======
@bot.message_handler(commands=['start'])
def menu_command(message):
    user_id = message.from_user.id
    register_member(user_id, message.from_user.username)

    if not is_user_joined(user_id):
        send_force_join_prompt(message.chat.id)
        return

    send_menu(user_id)


@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.chat.id != ADMIN_ID:
        return
    count = get_members_count()
    bot.send_message(message.chat.id, f"👥 تعداد کل کاربرانی که ربات رو استارت کردن: {count} نفر")

# ======= هندل کردن دکمه‌ها =======
@bot.message_handler(func=lambda message: message.text in ["ثبت آگهی", "اکانت درخواستی", "مشاهده آگهی‌ها", "قیمت یاب اکانت", "👤 حساب کاربری", "بازگشت"])
def handle_buttons(message):
    if not is_user_joined(message.from_user.id):
        send_force_join_prompt(message.chat.id)
        return

    if message.text == "ثبت آگهی":
        get_collection(message)
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
    elif message.text == "👤 حساب کاربری":
        show_account(message)
    elif message.text == "بازگشت":
        send_menu(message.chat.id)

# ======= سیستم ثبت آگهی =======
def get_collection(message):
    if check_back(message): return
    user_data[message.chat.id] = {
        'user_id': message.chat.id,
        'username': message.from_user.username
    }

    form_text = (
    "فرم رو کپی کنید و پر کنید چیزهایی هم که ندارید از لیست پاک کنید)\n\n"
    "```\n"
    "کالکشن:\n\n"
    "لجند:\n\n"
    "ناروتو:\n"
    "کوف:\n"
    "جوجوتسو:\n"
    "هانترهانتر:\n"
    "اسپیرانت:\n"
    "ترنسفورمرز:\n"
    "استاروارز:\n"
    "جنگیر:\n"
    "اتک ان تایتان:\n"
    "نئوبیست:\n"
    "دوکاتی:\n\n"
    "کالکتور:\n"
    "لاکی باکس:\n"
    "استار سالانه:\n"
    "زودیاک:\n\n"
    "ریجن اکانت:\n"
    "اسکین هایی که تو لیست نیس و توضیح مختصر درباره اکانت:\n\n"
    "قیمت:\n"
    "```"
    )

    # ارسال فرم و دکمه
    bot.send_message(message.chat.id, form_text, parse_mode="Markdown")
    # رفتن به مرحله دریافت فرم
    bot.register_next_step_handler(message, get_form_text)
    
def get_form_text(message):
    if check_back(message): return
    user_data[message.chat.id]['info_text'] = message.text

    bot.send_message(message.chat.id, "📹 لطفاً یک ویدئو از اکانت خود ارسال کنید(فیلم اسکین ها از قسمت کالکشن، ریت هیروها و امبلم تو فیلم باشن):")
    bot.register_next_step_handler(message, get_video)

def get_video(message):
    if check_back(message): return
    if message.content_type != 'video':
        bot.send_message(message.chat.id, "❌ لطفاً فقط یک ویدئو ارسال کنید(فیلم اسکین ها از قسمت کالکشن، ریت هیروها و امبلم تو فیلم باشن):")
        bot.register_next_step_handler(message, get_video)
        return

    user_data[message.chat.id]['video'] = message.video.file_id

    # ✅ ارسال پیام به کاربر که آگهی ثبت شد
    bot.send_message(message.chat.id, "✅ آگهی شما دریافت شد و برای بررسی به ادمین ارسال شد.")

    # ✅ فرستادن آگهی برای ادمین
    send_to_admin(message.chat.id)

def send_to_admin(user_id):
    data = user_data[user_id]

    caption = (
        "📢 آگهی جدید برای بررسی:\n\n"
        f"{data['info_text']}\n\n"
        f"👤 ارسال‌کننده: @{data['username'] or 'نامشخص'}"
    )

    markup = types.InlineKeyboardMarkup()
    approve_btn = types.InlineKeyboardButton("✅  تایید و کد", callback_data=f"approve_{user_id}")
    reject_btn = types.InlineKeyboardButton("❌ رد و دلیل", callback_data=f"reject_{user_id}")
    markup.add(approve_btn, reject_btn)

    bot.send_video(ADMIN_ID, data['video'], caption=caption, reply_markup=markup)
    
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
        bot.register_next_step_handler(call.message, handle_admin_text)  # ⬅️ این خط رو اضافه کن
    
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
        data = user_data.get(message.chat.id, {})
        if not any(isinstance(v, int) and v > 0 for v in data.values()):
            bot.send_message(message.chat.id, "❌ هنوز هیچ اسکینی ثبت نشده است.")
            send_skin_selection_menu(message.chat.id)
            return

        fixed_prices = {
            "Supreme": 1500000,
            "Grand": 700000,
            "Exquisite": 400000
        }

        total_price = 0
        summary_lines = []
        for skin_type, count in data.items():
            if not isinstance(count, int):
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
    if message.text.strip() == "بازگشت":
        send_menu(message.chat.id)
        return

    try:
        count = int(message.text.strip())
        if count < 0:
            raise ValueError()
    except Exception:
        bot.send_message(message.chat.id, "❌ لطفاً فقط عدد مثبت وارد کنید. چندتا اسکین داری؟")
        send_skin_selection_menu(message.chat.id)
        return

    # اطمینان از اینکه user_data موجوده
    if message.chat.id not in user_data:
        user_data[message.chat.id] = {}

    user_data[message.chat.id][skin_type] = count

    bot.send_message(
        message.chat.id,
        f"✅ تعداد اسکین‌های دسته {skin_type} ثبت شد.\n\n"
        "لطفاً دسته بعدی را انتخاب کنید یا «قیمت نهایی» را بزنید."
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
    user_id = int(call.data.split("_")[1])
    data = user_data.get(user_id)

    if not data:
        bot.answer_callback_query(call.id, "❌ اطلاعات درخواست یافت نشد.")
        return

    action = call.data.split("_")[0]  # buyapprove یا buyreject

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
                      f"{data['info_text']}\n\n" \
                      f"🆔 کد آگهی: {code}"

            markup = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton("📞 ارتباط با ادمین", url=f"tg://user?id={ADMIN_ID}")
            markup.add(btn)

            bot.send_video(CHANNEL_USERNAME, data['video'], caption=caption, reply_markup=markup)
            bot.send_message(user_id, f"✅ آگهی شما تأیید و در کانال منتشر شد.\n\n"
                                      f"کد آگهی: {code}\n\n"
                                      f"این پیام رو برای ادمین بفرستید")

        elif req_type == 'buy':
            caption = f"🛒 درخواست خرید تأیید شده:\n\n" \
                      f"🎯 اسکین‌های موردنظر: {data['requested_skins']}\n" \
                      f"💰 بودجه: {data['max_budget']}\n" \
                      f"🆔 کد درخواست: {code}"

            markup = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton("📞 ارتباط با ادمین", url=f"tg://user?id={ADMIN_ID}")
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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

threading.Thread(target=run).start()

bot.infinity_polling()
