python
import telebot
import random
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("8726468311:AAEigz5ni7rfl-YfuC6N_GSPnQJ8iq8fdio")
DATABASE_URL = os.getenv("postgresql://postgres:FOSqXOoHFgdAEiOmJlBtgCsIqEMjuEdm@postgres.railway.internal:5432/railway")
bot = telebot.TeleBot(8726468311:AAEigz5ni7rfl-YfuC6N_GSPnQJ8iq8fdio)

def get_db():
    return psycopg2.connect(postgresql://postgres:FOSqXOoHFgdAEiOmJlBtgCsIqEMjuEdm@postgres.railway.internal:5432/railway)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id BIGINT PRIMARY KEY, username VARCHAR(255), name VARCHAR(255),
        age INT, height INT, weight INT, city VARCHAR(255), bio TEXT,
        gender VARCHAR(10), photo_id VARCHAR(255), registered BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS ratings (
        id SERIAL PRIMARY KEY, from_user BIGINT, to_user BIGINT,
        rating VARCHAR(50), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(from_user) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(to_user) REFERENCES users(id) ON DELETE CASCADE)""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY, from_user BIGINT, to_user BIGINT,
        content TEXT, message_type VARCHAR(20), file_id VARCHAR(255),
        read BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(from_user) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(to_user) REFERENCES users(id) ON DELETE CASCADE)""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS matches (
        id SERIAL PRIMARY KEY, user1 BIGINT, user2 BIGINT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(user1, user2),
        FOREIGN KEY(user1) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(user2) REFERENCES users(id) ON DELETE CASCADE)""")
    
    conn.commit()
    cur.close()
    conn.close()

init_db()

MALE_SCALE = ["Sub3","Sub5","LLTN","LTN","HLTN","LMTN","MTN","HMTN","LHTN","HTN","HHTN","CHAD LITE","TRUE ADAM"]
FEMALE_SCALE = ["Sub3","Sub5","LLTB","LTB","HLTB","LMTB","MTB","HMTB","LHTB","HTB","HHTB","Stacy","True Eve"]
SCALE_EMOJIS = {
    "Sub3": "😢", "Sub5": "😐", "LLTN": "😕", "LTN": "🙂", "HLTN": "😊",
    "LMTN": "😄", "MTN": "😍", "HMTN": "🔥", "LHTN": "💎", "HTN": "✨",
    "HHTN": "🌟", "CHAD LITE": "👑", "TRUE ADAM": "👨‍🦱",
    "LLTB": "😢", "LTB": "😐", "HLTB": "😕", "LMTB": "😄", "MTB": "😍",
    "HMTB": "🔥", "LHTB": "💎", "HTB": "✨", "HHTB": "🌟", "Stacy": "👑", "True Eve": "👸"
}
HIGH_RATINGS = ["MTN", "HMTN", "LHTN", "HTN", "HHTN", "CHAD LITE", "TRUE ADAM",
    "MTB", "HMTB", "LHTB", "HTB", "HHTB", "Stacy", "True Eve"]

def get_scale(gender):
    return FEMALE_SCALE if gender == 'female' else MALE_SCALE

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("🎲 Оценить"), KeyboardButton("💌 Письма"))
    kb.add(KeyboardButton("👤 Профиль"), KeyboardButton("💕 Мои оценки"))
    kb.add(KeyboardButton("❤️‍🔥 Мэтчи"), KeyboardButton("🏆 Топ"))
    kb.add(KeyboardButton("🗑️ Удалить профиль"))
    return kb

def rating_kb(gender, target_id):
    kb = InlineKeyboardMarkup(row_width=2)
    for r in get_scale(gender):
        kb.add(InlineKeyboardButton(f"{SCALE_EMOJIS.get(r, '⭐')} {r}", callback_data=f"rate_{target_id}_{r}"))
    return kb

def gender_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("💪 ПАРЕНЬ", callback_data="gender_male"))
    kb.add(InlineKeyboardButton("🌸 ДЕВУШКА", callback_data="gender_female"))
    return kb

def user_view_kb(user_id):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("💌 Письмо", callback_data=f"msg_{user_id}"))
    kb.add(InlineKeyboardButton("📞 Запросить ЮЗ", callback_data=f"askuser_{user_id}"))
    return kb

def message_type_kb(target_id):
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(InlineKeyboardButton("📝 Текст", callback_data=f"msgtype_text_{target_id}"),
           InlineKeyboardButton("🎤 Голос", callback_data=f"msgtype_voice_{target_id}"),
           InlineKeyboardButton("🎙️ Кружок", callback_data=f"msgtype_circle_{target_id}"))
    return kb

user_states = {}

def set_state(user_id, **state):
    user_states[user_id] = state

def get_state(user_id):
    return user_states.get(user_id, {})

def clear_state(user_id):
    if user_id in user_states:
        del user_states[user_id]

def get_user(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def create_user(user_id, username, name):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (id, username, name) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", (user_id, username, name))
    conn.commit()
    cur.close()
    conn.close()

def update_user(user_id, **kwargs):
    conn = get_db()
    cur = conn.cursor()
    set_clause = ", ".join([f"{k}=%s" for k in kwargs.keys()])
    values = list(kwargs.values()) + [user_id]
    cur.execute(f"UPDATE users SET {set_clause} WHERE id=%s", values)
    conn.commit()
    cur.close()
    conn.close()

def delete_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def get_random_user(exclude_user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE id!=%s AND registered=TRUE ORDER BY RANDOM() LIMIT 1", (exclude_user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def save_rating(from_user, to_user, rating):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO ratings (from_user, to_user, rating) VALUES (%s, %s, %s)", (from_user, to_user, rating))
    conn.commit()
    cur.close()
    conn.close()
    check_match(from_user, to_user, rating)

def check_match(from_user, to_user, new_rating):
    if new_rating not in HIGH_RATINGS:
        return
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT rating FROM ratings WHERE from_user=%s AND to_user=%s ORDER BY created_at DESC LIMIT 1", (to_user, from_user))
    opposite = cur.fetchone()
    cur.close()
    
    if opposite and opposite['rating'] in HIGH_RATINGS:
        cur = conn.cursor()
        cur.execute("INSERT INTO matches (user1, user2) VALUES (%s, %s) ON CONFLICT DO NOTHING", (min(from_user, to_user), max(from_user, to_user)))
        conn.commit()
        cur.close()
        
        user1 = get_user(from_user)
        user2 = get_user(to_user)
        bot.send_message(from_user, f"❤️‍🔥 **ЛУКМЭТЧ!** ❤️‍🔥\n\nТы и @{user2['username']} лайкнули друг друга!\n\n👥 @{user2['username']}", parse_mode='Markdown')
        bot.send_message(to_user, f"❤️‍🔥 **ЛУКМЭТЧ!** ❤️‍🔥\n\nТы и @{user1['username']} лайкнули друг друга!\n\n👥 @{user1['username']}", parse_mode='Markdown')
    conn.close()

def save_message(from_user, to_user, content, msg_type, file_id=None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (from_user, to_user, content, message_type, file_id) VALUES (%s, %s, %s, %s, %s)", (from_user, to_user, content, msg_type, file_id))
    conn.commit()
    cur.close()
    conn.close()

def get_user_ratings(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT r.rating, u.username FROM ratings r JOIN users u ON r.from_user = u.id WHERE r.to_user=%s ORDER BY r.created_at DESC", (user_id,))
    ratings = cur.fetchall()
    cur.close()
    conn.close()
    return ratings

def get_unread_messages(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT m.id, m.from_user, m.content, m.message_type, m.file_id, u.username FROM messages m JOIN users u ON m.from_user = u.id WHERE m.to_user=%s AND m.read=FALSE ORDER BY m.created_at DESC", (user_id,))
    messages = cur.fetchall()
    cur.close()
    conn.close()
    return messages

def mark_message_read(msg_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE messages SET read=TRUE WHERE id=%s", (msg_id,))
    conn.commit()
    cur.close()
    conn.close()

def get_matches(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT CASE WHEN user1=%s THEN user2 ELSE user1 END as matched_user FROM matches WHERE user1=%s OR user2=%s", (user_id, user_id, user_id))
    matches = cur.fetchall()
    cur.close()
    conn.close()
    return [m['matched_user'] for m in matches]

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.chat.id
    user = get_user(uid)
    if not user:
        create_user(uid, m.from_user.username or f"user_{uid}", m.from_user.first_name)
        bot.send_message(uid, "💖 **ДОБРО ПОЖАЛОВАТЬ В MOGGVINCHIK!** 💖\n\nСколько тебе лет? (14+)", parse_mode='Markdown')
    else:
        bot.send_message(uid, f"✨ С возвращением, @{user['username']}!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True, content_types=['text'])
def handle_text(m):
    uid = m.chat.id
    user = get_user(uid)
    state = get_state(uid)
    if not user:
        return
    
    if not user.get('age') and m.text.isdigit():
        age = int(m.text)
        if age < 14:
            bot.send_message(uid, "❌ Только для 14+")
            return
        update_user(uid, age=age)
        bot.send_message(uid, "📏 Твой рост? (см)")
    elif user.get('age') and not user.get('height') and m.text.isdigit():
        update_user(uid, height=int(m.text))
        bot.send_message(uid, "⚖️ Твой вес? (кг)")
    elif user.get('height') and not user.get('weight') and m.text.isdigit():
        update_user(uid, weight=int(m.text))
        bot.send_message(uid, "🏙️ Из какого ты города?")
    elif user.get('weight') and not user.get('city'):
        update_user(uid, city=m.text[:50])
        bot.send_message(uid, "📝 Напиши о себе (макс 200 символов)")
    elif user.get('city') and not user.get('bio'):
        update_user(uid, bio=m.text[:200])
        bot.send_message(uid, "📸 Отправь свою фотографию")
    elif m.text == "🎲 Оценить":
        rate_menu(m)
    elif m.text == "👤 Профиль":
        show_profile(m)
    elif m.text == "💕 Мои оценки":
        show_ratings(m)
    elif m.text == "💌 Письма":
        show_messages(m)
    elif m.text == "❤️‍🔥 Мэтчи":
        show_matches(m)
    elif m.text == "🏆 Топ":
        show_top(m)
    elif m.text == "🗑️ Удалить профиль":
        confirm_delete(m)
    elif m.text == "📬 Прочитать письма":
        read_messages(m)
    elif m.text == "⬅️ Назад":
        bot.send_message(uid, "Главное меню", reply_markup=main_menu())
    elif state.get("action") == "sending_message" and state.get("msg_type") == "text":
        save_message(uid, state.get("target_id"), m.text, "text")
        bot.send_message(uid, "✅ Письмо отправлено!", reply_markup=main_menu())
        clear_state(uid)
    elif state.get("action") == "confirm_delete":
        if m.text.lower() == "да":
            delete_user(uid)
            bot.send_message(uid, "❌ Твой профиль удален")
            clear_state(uid)
        elif m.text.lower() == "нет":
            bot.send_message(uid, "✅ Отмена", reply_markup=main_menu())
            clear_state(uid)

@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    uid = m.chat.id
    user = get_user(uid)
    if user and user.get('city') and not user.get('photo_id'):
        update_user(uid, photo_id=m.photo[-1].file_id)
        bot.send_message(uid, "👤 Выбери свой пол:", reply_markup=gender_kb())

@bot.message_handler(content_types=['voice'])
def handle_voice(m):
    uid = m.chat.id
    state = get_state(uid)
    if state.get("action") == "sending_message" and state.get("msg_type") == "voice":
        save_message(uid, state.get("target_id"), "🎤 Голосовое сообщение", "voice", m.voice.file_id)
        bot.send_message(uid, "✅ Голосовое письмо отправлено!", reply_markup=main_menu())
        clear_state(uid)

@bot.message_handler(content_types=['video_note'])
def handle_circle(m):
    uid = m.chat.id
    state = get_state(uid)
    if state.get("action") == "sending_message" and state.get("msg_type") == "circle":
        save_message(uid, state.get("target_id"), "🎙️ Кружок", "circle", m.video_note.file_id)
        bot.send_message(uid, "✅ Кружок отправлен!", reply_markup=main_menu())
        clear_state(uid)

@bot.callback_query_handler(func=lambda c: c.data.startswith('gender_'))
def set_gender(c):
    uid = c.from_user.id
    gender = 'male' if 'male' in c.data else 'female'
    update_user(uid, gender=gender, registered=True)
    bot.edit_message_text("✅ Профиль готов!", cПроблема с доступом к репо. Дай мне готовый код, скопируй на GitHub вручную:
Откройте `bot.py` в GitHub → нажмите **✏️ Edit** → **замените весь код** на этот:

```python
import telebot
import random
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("TELEGRAM_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
bot = telebot.TeleBot(TOKEN)

def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id BIGINT PRIMARY KEY, username VARCHAR(255), name VARCHAR(255),
        age INT, height INT, weight INT, city VARCHAR(255), bio TEXT,
        gender VARCHAR(10), photo_id VARCHAR(255), registered BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS ratings (
        id SERIAL PRIMARY KEY, from_user BIGINT, to_user BIGINT,
        rating VARCHAR(50), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(from_user) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(to_user) REFERENCES users(id) ON DELETE CASCADE)""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY, from_user BIGINT, to_user BIGINT,
        content TEXT, message_type VARCHAR(20), file_id VARCHAR(255),
        read BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(from_user) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(to_user) REFERENCES users(id) ON DELETE CASCADE)""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS matches (
        id SERIAL PRIMARY KEY, user1 BIGINT, user2 BIGINT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(user1, user2),
        FOREIGN KEY(user1) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(user2) REFERENCES users(id) ON DELETE CASCADE)""")
    
    conn.commit()
    cur.close()
    conn.close()

init_db()

MALE_SCALE = ["Sub3","Sub5","LLTN","LTN","HLTN","LMTN","MTN","HMTN","LHTN","HTN","HHTN","CHAD LITE","TRUE ADAM"]
FEMALE_SCALE = ["Sub3","Sub5","LLTB","LTB","HLTB","LMTB","MTB","HMTB","LHTB","HTB","HHTB","Stacy","True Eve"]
SCALE_EMOJIS = {
    "Sub3": "😢", "Sub5": "😐", "LLTN": "😕", "LTN": "🙂", "HLTN": "😊",
    "LMTN": "😄", "MTN": "😍", "HMTN": "🔥", "LHTN": "💎", "HTN": "✨",
    "HHTN": "🌟", "CHAD LITE": "👑", "TRUE ADAM": "👨‍🦱",
    "LLTB": "😢", "LTB": "😐", "HLTB": "😕", "LMTB": "😄", "MTB": "😍",
    "HMTB": "🔥", "LHTB": "💎", "HTB": "✨", "HHTB": "🌟", "Stacy": "👑", "True Eve": "👸"
}
HIGH_RATINGS = ["MTN", "HMTN", "LHTN", "HTN", "HHTN", "CHAD LITE", "TRUE ADAM",
    "MTB", "HMTB", "LHTB", "HTB", "HHTB", "Stacy", "True Eve"]

def get_scale(gender):
    return FEMALE_SCALE if gender == 'female' else MALE_SCALE

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("🎲 Оценить"), KeyboardButton("💌 Письма"))
    kb.add(KeyboardButton("👤 Профиль"), KeyboardButton("💕 Мои оценки"))
    kb.add(KeyboardButton("❤️‍🔥 Мэтчи"), KeyboardButton("🏆 Топ"))
    kb.add(KeyboardButton("🗑️ Удалить профиль"))
    return kb

def rating_kb(gender, target_id):
    kb = InlineKeyboardMarkup(row_width=2)
    for r in get_scale(gender):
        kb.add(InlineKeyboardButton(f"{SCALE_EMOJIS.get(r, '⭐')} {r}", callback_data=f"rate_{target_id}_{r}"))
    return kb

def gender_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("💪 ПАРЕНЬ", callback_data="gender_male"))
    kb.add(InlineKeyboardButton("🌸 ДЕВУШКА", callback_data="gender_female"))
    return kb

def user_view_kb(user_id):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("💌 Письмо", callback_data=f"msg_{user_id}"))
    kb.add(InlineKeyboardButton("📞 Запросить ЮЗ", callback_data=f"askuser_{user_id}"))
    return kb

def message_type_kb(target_id):
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(InlineKeyboardButton("📝 Текст", callback_data=f"msgtype_text_{target_id}"),
           InlineKeyboardButton("🎤 Голос", callback_data=f"msgtype_voice_{target_id}"),
           InlineKeyboardButton("🎙️ Кружок", callback_data=f"msgtype_circle_{target_id}"))
    return kb

user_states = {}

def set_state(user_id, **state):
    user_states[user_id] = state

def get_state(user_id):
    return user_states.get(user_id, {})

def clear_state(user_id):
    if user_id in user_states:
        del user_states[user_id]

def get_user(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def create_user(user_id, username, name):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (id, username, name) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", (user_id, username, name))
    conn.commit()
    cur.close()
    conn.close()

def update_user(user_id, **kwargs):
    conn = get_db()
    cur = conn.cursor()
    set_clause = ", ".join([f"{k}=%s" for k in kwargs.keys()])
    values = list(kwargs.values()) + [user_id]
    cur.execute(f"UPDATE users SET {set_clause} WHERE id=%s", values)
    conn.commit()
    cur.close()
    conn.close()

def delete_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def get_random_user(exclude_user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE id!=%s AND registered=TRUE ORDER BY RANDOM() LIMIT 1", (exclude_user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def save_rating(from_user, to_user, rating):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO ratings (from_user, to_user, rating) VALUES (%s, %s, %s)", (from_user, to_user, rating))
    conn.commit()
    cur.close()
    conn.close()
    check_match(from_user, to_user, rating)

def check_match(from_user, to_user, new_rating):
    if new_rating not in HIGH_RATINGS:
        return
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT rating FROM ratings WHERE from_user=%s AND to_user=%s ORDER BY created_at DESC LIMIT 1", (to_user, from_user))
    opposite = cur.fetchone()
    cur.close()
    
    if opposite and opposite['rating'] in HIGH_RATINGS:
        cur = conn.cursor()
        cur.execute("INSERT INTO matches (user1, user2) VALUES (%s, %s) ON CONFLICT DO NOTHING", (min(from_user, to_user), max(from_user, to_user)))
        conn.commit()
        cur.close()
        
        user1 = get_user(from_user)
        user2 = get_user(to_user)
        bot.send_message(from_user, f"❤️‍🔥 **ЛУКМЭТЧ!** ❤️‍🔥\n\nТы и @{user2['username']} лайкнули друг друга!\n\n👥 @{user2['username']}", parse_mode='Markdown')
        bot.send_message(to_user, f"❤️‍🔥 **ЛУКМЭТЧ!** ❤️‍🔥\n\nТы и @{user1['username']} лайкнули друг друга!\n\n👥 @{user1['username']}", parse_mode='Markdown')
    conn.close()

def save_message(from_user, to_user, content, msg_type, file_id=None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (from_user, to_user, content, message_type, file_id) VALUES (%s, %s, %s, %s, %s)", (from_user, to_user, content, msg_type, file_id))
    conn.commit()
    cur.close()
    conn.close()

def get_user_ratings(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT r.rating, u.username FROM ratings r JOIN users u ON r.from_user = u.id WHERE r.to_user=%s ORDER BY r.created_at DESC", (user_id,))
    ratings = cur.fetchall()
    cur.close()
    conn.close()
    return ratings

def get_unread_messages(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT m.id, m.from_user, m.content, m.message_type, m.file_id, u.username FROM messages m JOIN users u ON m.from_user = u.id WHERE m.to_user=%s AND m.read=FALSE ORDER BY m.created_at DESC", (user_id,))
    messages = cur.fetchall()
    cur.close()
    conn.close()
    return messages

def mark_message_read(msg_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE messages SET read=TRUE WHERE id=%s", (msg_id,))
    conn.commit()
    cur.close()
    conn.close()

def get_matches(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT CASE WHEN user1=%s THEN user2 ELSE user1 END as matched_user FROM matches WHERE user1=%s OR user2=%s", (user_id, user_id, user_id))
    matches = cur.fetchall()
    cur.close()
    conn.close()
    return [m['matched_user'] for m in matches]

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.chat.id
    user = get_user(uid)
    if not user:
        create_user(uid, m.from_user.username or f"user_{uid}", m.from_user.first_name)
        bot.send_message(uid, "💖 **ДОБРО ПОЖАЛОВАТЬ В MOGGVINCHIK!** 💖\n\nСколько тебе лет? (14+)", parse_mode='Markdown')
    else:
        bot.send_message(uid, f"✨ С возвращением, @{user['username']}!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True, content_types=['text'])
def handle_text(m):
    uid = m.chat.id
    user = get_user(uid)
    state = get_state(uid)
    if not user:
        return
    
    if not user.get('age') and m.text.isdigit():
        age = int(m.text)
        if age < 14:
            bot.send_message(uid, "❌ Только для 14+")
            return
        update_user(uid, age=age)
        bot.send_message(uid, "📏 Твой рост? (см)")
    elif user.get('age') and not user.get('height') and m.text.isdigit():
        update_user(uid, height=int(m.text))
        bot.send_message(uid, "⚖️ Твой вес? (кг)")
    elif user.get('height') and not user.get('weight') and m.text.isdigit():
        update_user(uid, weight=int(m.text))
        bot.send_message(uid, "🏙️ Из какого ты города?")
    elif user.get('weight') and not user.get('city'):
        update_user(uid, city=m.text[:50])
        bot.send_message(uid, "📝 Напиши о себе (макс 200 символов)")
    elif user.get('city') and not user.get('bio'):
        update_user(uid, bio=m.text[:200])
        bot.send_message(uid, "📸 Отправь свою фотографию")
    elif m.text == "🎲 Оценить":
        rate_menu(m)
    elif m.text == "👤 Профиль":
        show_profile(m)
    elif m.text == "💕 Мои оценки":
        show_ratings(m)
    elif m.text == "💌 Письма":
        show_messages(m)
    elif m.text == "❤️‍🔥 Мэтчи":
        show_matches(m)
    elif m.text == "🏆 Топ":
        show_top(m)
    elif m.text == "🗑️ Удалить профиль":
        confirm_delete(m)
    elif m.text == "📬 Прочитать письма":
        read_messages(m)
    elif m.text == "⬅️ Назад":
        bot.send_message(uid, "Главное меню", reply_markup=main_menu())
    elif state.get("action") == "sending_message" and state.get("msg_type") == "text":
        save_message(uid, state.get("target_id"), m.text, "text")
        bot.send_message(uid, "✅ Письмо отправлено!", reply_markup=main_menu())
        clear_state(uid)
    elif state.get("action") == "confirm_delete":
        if m.text.lower() == "да":
            delete_user(uid)
            bot.send_message(uid, "❌ Твой профиль удален")
            clear_state(uid)
        elif m.text.lower() == "нет":
            bot.send_message(uid, "✅ Отмена", reply_markup=main_menu())
            clear_state(uid)

@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    uid = m.chat.id
    user = get_user(uid)
    if user and user.get('city') and not user.get('photo_id'):
        update_user(uid, photo_id=m.photo[-1].file_id)
        bot.send_message(uid, "👤 Выбери свой пол:", reply_markup=gender_kb())

@bot.message_handler(content_types=['voice'])
def handle_voice(m):
    uid = m.chat.id
    state = get_state(uid)
    if state.get("action") == "sending_message" and state.get("msg_type") == "voice":
        save_message(uid, state.get("target_id"), "🎤 Голосовое сообщение", "voice", m.voice.file_id)
        bot.send_message(uid, "✅ Голосовое письмо отправлено!", reply_markup=main_menu())
        clear_state(uid)

@bot.message_handler(content_types=['video_note'])
def handle_circle(m):
    uid = m.chat.id
    state = get_state(uid)
    if state.get("action") == "sending_message" and state.get("msg_type") == "circle":
        save_message(uid, state.get("target_id"), "🎙️ Кружок", "circle", m.video_note.file_id)
        bot.send_message(uid, "✅ Кружок отправлен!", reply_markup=main_menu())
        clear_state(uid)

@bot.callback_query_handler(func=lambda c: c.data.startswith('gender_'))
def set_gender(c):
    uid = c.from_user.id
    gender = 'male' if 'male' in c.data else 'female'
    update_user(uid, gender=gender, registered=True)
    bot.edit_message_text("✅ Профиль готов!", c.message.chat.id, c.message.message_id)
    bot.send_message(uid, "🎉 **ГОТОВО! Начни оценивать!** 🎉", reply_markup=main_menu(), parse_mode='Markdown')

def rate_menu(m):
    uid = m.chat.id
    user = get_user(uid)
    if not user or not user.get('registered'):
        bot.send_message(uid, "❌ Завершите регистрацию (/start)")
        return
    target = get_random_user(uid)
    if not target:
        bot.send_message(uid, "😢 Нет других пользователей для оценки")
        return
    text = f"👤 **@{target['username']}** ({target['name']})\n\n📅 {target['age']} лет\n📏 {target['height']} см\n⚖️ {target['weight']} кг\n🏙️ {target['city']}\n📝 _{target['bio']}_\n\n💖 **Оцени внешность:**"
    if target.get('photo_id'):
        bot.send_photo(uid, target['photo_id'], caption=text, reply_markup=rating_kb(target['gender'], target['id']), parse_mode='Markdown')
    else:
        bot.send_message(uid, text, reply_markup=rating_kb(target['gender'], target['id']), parse_mode='Markdown')

@bot.callback_query_handler(func=lambda c: c.data.startswith('rate_'))
def set_rating(c):
    parts = c.data.split('_', 2)
    target_id = int(parts[1])
    rating = parts[2]
    uid = c.from_user.id
    save_rating(uid, target_id, rating)
    emoji = SCALE_EMOJIS.get(rating, '⭐')
    bot.answer_callback_query(c.id, f"✅ {emoji} {rating}")
    if rating in HIGH_RATINGS:
        user = get_user(uid)
        target = get_user(target_id)
        bot.send_message(target_id, f"{emoji} **@{user['username']}** оценил тебя на **{rating}**!\n\n👁️ Посмотреть анкету?", reply_markup=user_view_kb(uid), parse_mode='Markdown')

def show_profile(m):
    uid = m.chat.id
    user = get_user(uid)
    if not user or not user.get('registered'):
        bot.send_message(uid, "❌ Завершите регистрацию")
        return
    emoji = "👨" if user['gender'] == 'male' else "👩"
    text = f"{emoji} **@{user['username']}**\n\n📅 {user['age']} лет\n📏 {user['height']} см\n⚖️ {user['weight']} кг\n🏙️ {user['city']}\n📝 _{user['bio']}_"
    if user.get('photo_id'):
        bot.send_photo(uid, user['photo_id'], caption=text, reply_markup=main_menu(), parse_mode='Markdown')
    else:
        bot.send_message(uid, text, reply_markup=main_menu(), parse_mode='Markdown')

def show_ratings(m):
    uid = m.chat.id
    ratings = get_user_ratings(uid)
    if not ratings:
        bot.send_message(uid, "📊 Пока никто не оценил тебя 😞", reply_markup=main_menu())
        return
    text = "💕 **Кто тебя оценил:**\n\n"
    for r in ratings:
        emoji = SCALE_EMOJIS.get(r['rating'], '⭐')
        if r['rating'] in HIGH_RATINGS:
            text += f"{emoji} @{r['username']} — **{r['rating']}**\n"
        else:
            text += f"{emoji} Кто-то — **{r['rating']}**\n"
    bot.send_message(uid, text, parse_mode='Markdown', reply_markup=main_menu())

def show_messages(m):
    uid = m.chat.id
    messages = get_unread_messages(uid)
    if not messages:
        bot.send_message(uid, "📬 Нет новых писем", reply_markup=main_menu())
        return
    text = f"💌 **У тебя {len(messages)} новых писем:**\n\n"
    for msg in messages:
        text += f"📨 От @{msg['username']}\n"
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📬 Прочитать письма"), KeyboardButton("⬅️ Назад"))
    bot.send_message(uid, text, parse_mode='Markdown', reply_markup=kb)

def read_messages(m):
    uid = m.chat.id
    messages = get_unread_messages(uid)
    if not messages:
        bot.send_message(uid, "📬 Нет новых писем", reply_markup=main_menu())
        return
    for msg in messages:
        if msg['message_type'] == 'text':
            bot.send_message(uid, f"💌 **От @{msg['username']}:**\n\n{msg['content']}", parse_mode='Markdown')
        elif msg['message_type'] == 'voice':
            bot.send_voice(uid, msg['file_id'], caption=f"🎤 От @{msg['username']}")
        elif msg['message_type'] == 'circle':
            bot.send_video_note(uid, msg['file_id'])
        mark_message_read(msg['id'])
    bot.send_message(uid, "✅ Все письма прочитаны", reply_markup=main_menu())

def show_matches(m):
    uid = m.chat.id
    matches = get_matches(uid)
    if not matches:
        bot.send_message(uid, "❤️‍🔥 Мэтчей нет, но они появятся! 😊", reply_markup=main_menu())
        return
    text = "❤️‍🔥 **ТВОИ МЭТЧИ:**\n\n"
    for match_id in matches:
        user = get_user(match_id)
        text += f"👥 @{user['username']} ({user['name']})\n"
    bot.send_message(uid, text, parse_mode='Markdown', reply_markup=main_menu())

def show_top(m):
    uid = m.chat.id
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT u.username, u.gender, COUNT(r.id) as count FROM users u LEFT JOIN ratings r ON r.to_user = u.id WHERE u.registered = TRUE GROUP BY u.id ORDER BY count DESC LIMIT 20")
    top_users = cur.fetchall()
    cur.close()
    conn.close()
    if not top_users:
        bot.send_message(uid, "🏆 Пока нет оценок", reply_markup=main_menu())
        return
    text = "🏆 **ТОП МОГГВИНЧИК:**\n\n"
    for i, u in enumerate(top_users, 1):
        em = "👨" if u['gender'] == 'male' else "👩"
        text += f"{i}. {em} @{u['username']} — {u['count']} 🌟\n"
    bot.send_message(uid, text, parse_mode='Markdown', reply_markup=main_menu())

def confirm_delete(m):
    uid = m.chat.id
    set_state(uid, action="confirm_delete")
    bot.send_message(uid, "⚠️ Ты уверен? Напиши 'да' или 'нет'")

@bot.callback_query_handler(func=lambda c: c.data.startswith('msg_'))
def handle_msg(c):
    uid = c.from_user.id
    target_id = int(c.data.split('_')[1])
    set_state(uid, action="choosing_message_type", target_id=target_id)
    bot.send_message(uid, "💌 Выбери тип письма:", reply_markup=message_type_kb(target_id))

@bot.callback_query_handler(func=lambda c: c.data.startswith('askuser_'))
def handle_askuser(c):
    uid = c.from_user.id
    target_id = int(c.data.split('_')[1])
    user = get_user(uid)
    bot.send_message(target_id, f"📞 **@{user['username']}** запросил(-а) твой контакт!", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Дать контакт", callback_data=f"giveuser_{uid}")), parse_mode='Markdown')
    bot.send_message(uid, "📞 Запрос отправлен!")

@bot.callback_query_handler(func=lambda c: c.data.startswith('msgtype_'))
def handle_msgtype(c):
    uid = c.from_user.id
    parts = c.data.split('_')
    msg_type = parts[1]
    target_id = int(parts[2])
    set_state(uid, action="sending_message", msg_type=msg_type, target_id=target_id)
    if msg_type == "text":
        bot.send_message(uid, "📝 Напиши своё письмо:")
    elif msg_type == "voice":
        bot.send_message(uid, "🎤 Отправь голосовое сообщение:")
    elif msg_type == "circle":
        bot.send_message(uid, "🎙️ Отправь кружок (видеосообщение):")

@bot.callback_query_handler(func=lambda c: c.data.startswith('giveuser_'))
def give_user_contact(c):
    user = get_user(c.from_user.id)
    requester_id = int(c.data.split('_')[1])
    bot.send_message(requester_id, f"✅ **Контакт:** @{user['username']}", parse_mode='Markdown')
    bot.answer_callback_query(c.id, "✅ Контакт отправлен!")

print("🚀 БОТ ЗАПУЩЕН!")
bot.infinity_polling()
