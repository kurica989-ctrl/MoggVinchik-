import telebot
import random
import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

USERS_FILE = "users.json"
RATINGS_FILE = "ratings.json"

def load_json(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users = load_json(USERS_FILE)
ratings = load_json(RATINGS_FILE)

def save_all():
    save_json(USERS_FILE, users)
    save_json(RATINGS_FILE, ratings)

MALE_SCALE = ["Sub3","Sub5","LLTN","LTN","HLTN","LMTN","MTN","HMTN","LHTN","HTN","HHTN","CHAD LITE","TRUE ADAM"]
FEMALE_SCALE = ["Sub3","Sub5","LLTB","LTB","HLTB","LMTB","MTB","HMTB","LHTB","HTB","HHTB","Stacy","True Eve"]

def get_scale(gender):
    return FEMALE_SCALE if gender == 'female' else MALE_SCALE

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("🎲 Оценить"), KeyboardButton("👤 Мой профиль"))
    kb.add(KeyboardButton("⭐ Кто меня оценил?"), KeyboardButton("🏆 Топ"))
    return kb

def rating_kb(gender, target_id):
    kb = InlineKeyboardMarkup(row_width=3)
    for r in get_scale(gender):
        kb.add(InlineKeyboardButton(r, callback_data=f"rate_{target_id}_{r}"))
    return kb

def gender_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("💪 ПАРЕНЬ", callback_data="gender_male"))
    kb.add(InlineKeyboardButton("🌸 ДЕВУШКА", callback_data="gender_female"))
    return kb

@bot.message_handler(commands=['start'])
def start(m):
    uid = str(m.chat.id)
    if uid not in users:
        users[uid] = {
            'username': m.from_user.username or f"user_{uid[:5]}",
            'name': m.from_user.first_name,
            'photos': [],
            'gender': None,
            'age': None,
            'height': None,
            'weight': None,
            'city': None,
            'bio': None,
            'registered': False,
            'step': 'age'
        }
        save_all()
        bot.send_message(uid, "💖 ДОБРО ПОЖАЛОВАТЬ В МОГГВИНЧИК! 💖\n\nСколько тебе лет? (14+)", parse_mode='Markdown')
    else:
        bot.send_message(uid, f"✨ С возвращением, @{users[uid]['username']}!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text.isdigit() and users.get(str(m.chat.id), {}).get('step') == 'age')
def step_age(m):
    uid = str(m.chat.id)
    age = int(m.text)
    if age < 14:
        bot.send_message(uid, "❌ Бот только для 14+")
        return
    users[uid]['age'] = age
    users[uid]['step'] = 'height'
    save_all()
    bot.send_message(uid, "📏 Твой рост? (в см)")

@bot.message_handler(func=lambda m: m.text.isdigit() and users.get(str(m.chat.id), {}).get('step') == 'height')
def step_height(m):
    uid = str(m.chat.id)
    users[uid]['height'] = int(m.text)
    users[uid]['step'] = 'weight'
    save_all()
    bot.send_message(uid, "⚖️ Твой вес? (в кг)")

@bot.message_handler(func=lambda m: m.text.isdigit() and users.get(str(m.chat.id), {}).get('step') == 'weight')
def step_weight(m):
    uid = str(m.chat.id)
    users[uid]['weight'] = int(m.text)
    users[uid]['step'] = 'city'
    save_all()
    bot.send_message(uid, "🏙️ Из какого ты города?")

@bot.message_handler(func=lambda m: users.get(str(m.chat.id), {}).get('step') == 'city')
def step_city(m):
    uid = str(m.chat.id)
    users[uid]['city'] = m.text[:50]
    users[uid]['step'] = 'bio'
    save_all()
    bot.send_message(uid, "📝 Напиши немного о себе")

@bot.message_handler(func=lambda m: users.get(str(m.chat.id), {}).get('step') == 'bio')
def step_bio(m):
    uid = str(m.chat.id)
    users[uid]['bio'] = m.text[:200]
    users[uid]['step'] = 'photo'
    save_all()
    bot.send_message(uid, "📸 Отправь своё фото")

@bot.message_handler(content_types=['photo'])
def step_photo(m):
    uid = str(m.chat.id)
    if uid not in users or users[uid].get('step') != 'photo':
        return
    users[uid]['photos'] = [m.photo[-1].file_id]
    users[uid]['step'] = 'gender'
    save_all()
    bot.send_message(uid, "👤 Твой пол:", reply_markup=gender_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith('gender_'))
def set_gender(c):
    uid = str(c.from_user.id)
    gender = 'male' if 'male' in c.data else 'female'
    users[uid]['gender'] = gender
    users[uid]['registered'] = True
    users[uid]['step'] = None
    save_all()
    bot.edit_message_text(f"✅ Пол: {'ПАРЕНЬ' if gender == 'male' else 'ДЕВУШКА'}", c.message.chat.id, c.message.message_id)
    bot.send_message(uid, "🎉 РЕГИСТРАЦИЯ ЗАВЕРШЕНА! 🎉\n\nТеперь ты можешь оценивать других.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🎲 Оценить")
def rate(m):
    uid = str(m.chat.id)
    if uid not in users or not users[uid].get('registered'):
        bot.send_message(uid, "❌ Сначала /start")
        return
    others = [u for u, d in users.items() if u != uid and d.get('registered')]
    if not others:
        bot.send_message(uid, "😢 Нет других пользователей")
        return
    target = random.choice(others)
    tu = users[target]
    text = f"👤 @{tu['username']}\n\n📅 Возраст: {tu.get('age', '?')}\n📏 Рост: {tu.get('height', '?')} см\n⚖️ Вес: {tu.get('weight', '?')} кг\n🏙️ Город: {tu.get('city', '?')}\n📝 {tu.get('bio', '—')}\n\n💖 Оцени внешность по шкале МоггВинчик:"
    bot.send_photo(uid, tu['photos'][0], caption=text, reply_markup=rating_kb(tu['gender'], target))

@bot.callback_query_handler(func=lambda c: c.data.startswith('rate_'))
def set_rating(c):
    parts = c.data.split('_')
    target_id = parts[1]
    rating = '_'.join(parts[2:])
    uid = str(c.from_user.id)
    if target_id not in ratings:
        ratings[target_id] = []
    ratings[target_id].append(rating)
    save_all()
    bot.answer_callback_query(c.id, f"✅ {rating}")
    bot.edit_message_caption(caption=f"⭐ Оценено: {rating}", chat_id=c.message.chat.id, message_id=c.message.message_id)

@bot.message_handler(func=lambda m: m.text == "👤 Мой профиль")
def profile(m):
    uid = str(m.chat.id)
    if uid not in users or not users[uid].get('registered'):
        bot.send_message(uid, "❌ Сначала /start")
        return
    u = users[uid]
    emoji = "👨" if u['gender'] == 'male' else "👩"
    text = f"{emoji} **@{u['username']}**\n\n"
    text += f"📅 Возраст: {u.get('age', '?')}\n📏 Рост: {u.get('height', '?')} см\n⚖️ Вес: {u.get('weight', '?')} кг\n🏙️ Город: {u.get('city', '?')}\n📝 О себе: {u.get('bio', '—')}"
    bot.send_photo(uid, u['photos'][0], caption=text, parse_mode='Markdown', reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "⭐ Кто меня оценил?")
def who_rated(m):
    uid = str(m.chat.id)
    user_ratings = ratings.get(uid, [])
    if not user_ratings:
        bot.send_message(uid, "📊 Пока никто не оценил тебя")
        return
    bot.send_message(uid, f"📊 У тебя {len(user_ratings)} оценок!")

@bot.message_handler(func=lambda m: m.text == "🏆 Топ")
def top(m):
    uid = str(m.chat.id)
    male, female = [], []
    for u, d in users.items():
        if not d.get('registered'):
            continue
        if d['gender'] == 'male':
            male.append(d['username'])
        else:
            female.append(d['username'])
    text = "🏆 **ТОП МОГГВИНЧИК** 🏆\n\n👨 **ПАРНИ:**\n"
    for i, name in enumerate(male[:10], 1):
        text += f"{i}. @{name}\n"
    if not male:
        text += "— пока нет —\n"
    text += "\n👩 **ДЕВУШКИ:**\n"
    for i, name in enumerate(female[:10], 1):
        text += f"{i}. @{name}\n"
    if not female:
        text += "— пока нет —"
    bot.send_message(uid, text, parse_mode='Markdown', reply_markup=main_menu())

print("🚀 БОТ ЗАПУЩЕН!")
bot.infinity_polling()
