import telebot
from telebot import types
import csv
import os
import time
import threading
from datetime import datetime

# ==========================================
TOKEN = '7976931399:AAGb9HHg-a6wmLVMIsuChCjZadLB8JReRaw'
ADMIN_ID = 5431881491
WEBAPP_URL = "https://leqwes.github.io/vuz_app/"
# ==========================================

bot = telebot.TeleBot(TOKEN)
STATS_FILE = 'statistics.csv'
SUBS_FILE = 'subscriptions.csv'
PAMYATKA_FILE = 'pamyatka.pdf'

EXAM_DATES = {
    "История/Лит/Хим": "2026-06-01", "Русский язык": "2026-06-04",
    "Математика (Б/П)": "2026-06-08", "Общество/Физика": "2026-06-11",
    "Био/Гео/Ин.яз": "2026-06-15", "Информатика (КЕГЭ)": "2026-06-18"
}

# --- ФУНКЦИИ БАЗЫ ---
def save_to_csv(user_id, username, action, info=""):
    try:
        exists = os.path.isfile(STATS_FILE)
        with open(STATS_FILE, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            if not exists: writer.writerow(['ID', 'Ник', 'Время', 'Действие', 'Инфо'])
            uname = username if username else "Аноним"
            writer.writerow([user_id, uname, datetime.now().strftime("%Y-%m-%d %H:%M"), action, info])
    except: pass

def add_subscription(user_id, subject):
    subs = []
    if os.path.exists(SUBS_FILE):
        with open(SUBS_FILE, 'r', encoding='utf-8') as f: subs = list(csv.reader(f))
    for row in subs:
        if str(row[0]) == str(user_id) and row[1] == subject: return False
    with open(SUBS_FILE, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([user_id, subject])
    return True

def notification_loop():
    while True:
        if datetime.now().strftime("%H:%M") == "09:00":
            if os.path.exists(SUBS_FILE):
                with open(SUBS_FILE, 'r', encoding='utf-8') as f:
                    for row in csv.reader(f):
                        try:
                            if row[1] in EXAM_DATES:
                                # Упрощенная проверка по части названия
                                for key, date in EXAM_DATES.items():
                                    if key in row[1] or row[1] in key:
                                        days = (datetime.strptime(date, "%Y-%m-%d") - datetime.now()).days
                                        if days > 0:
                                            bot.send_message(row[0], f"🔔 Напоминание!\nДо ЕГЭ ({row[1]}) осталось: **{days} дн.**", parse_mode="Markdown")
                                        break
                        except: pass
            time.sleep(61)
        time.sleep(30)

t = threading.Thread(target=notification_loop)
t.daemon = True
t.start()

# --- МЕНЮ ---
@bot.message_handler(commands=['start'])
def start(message):
    save_to_csv(message.from_user.id, message.from_user.username, "START", "Зашел в меню")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    # ГЛАВНАЯ КНОПКА (Сайт)
    webApp = types.WebAppInfo(WEBAPP_URL)
    markup.add(types.KeyboardButton(text="📱 Открыть VuzPoisk App", web_app=webApp))
    
    markup.row("🏆 Доп. баллы", "🎓 После СПО")
    markup.row("📂 Документы", "🌟 Льготы")
    markup.row("📩 Обратная связь", "📄 Памятка")

    bot.send_message(message.chat.id, 
                     "🚀 **VuzPoisk 2.0 готов!**\n\n"
                     "Весь поиск, тесты и таймер переехали в удобное приложение.\n"
                     "Нажми **📱 Открыть VuzPoisk App** 👇", 
                     reply_markup=markup, parse_mode="Markdown")

# --- ОБРАБОТКА ДАННЫХ ОТ САЙТА ---
@bot.message_handler(content_types=['web_app_data'])
def web_app_handler(message):
    data = message.web_app_data.data.split('|')
    action = data[0]

    # Приложение просто сообщает о поиске (для статистики)
    if action == "LOG":
        # LOG|SEARCH|Москва|220
        save_to_csv(message.from_user.id, message.from_user.username, action, data[1] + " " + data[2])
    
    # Подписка на таймер из приложения
    elif action == "TIMER":
        subj = data[1]
        if add_subscription(message.from_user.id, subj):
            bot.send_message(message.chat.id, f"✅ Уведомления для **{subj}** включены!\nБуду писать каждое утро в 09:00.", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"Ты уже подписан на **{subj}**.")

# --- СПРАВОЧНИК ---
@bot.message_handler(func=lambda m: m.text == "🎓 После СПО")
def show_spo(message):
    bot.send_message(message.chat.id, "🎓 **ПОСТУПЛЕНИЕ ПОСЛЕ СПО:**\n1. Можно сдавать внутренние экзамены.\n2. Диплом с отличием дает бонусы.\n3. Сроки подачи короче.", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🌟 Льготы")
def show_lgots(message):
    bot.send_message(message.chat.id, "🌟 **ЛЬГОТЫ:**\n1. БВИ (Олимпиады).\n2. Особая квота (Сироты, Инвалиды).\n3. Отдельная квота (СВО).", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🏆 Доп. баллы")
def show_bonus(message):
    bot.send_message(message.chat.id, "🏆 **БОНУСЫ:**\n🥇 Медаль: +5-10\n🏃 ГТО: +2-5\n🤝 Волонтерство: +2", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📂 Документы")
def show_docs(message):
    bot.send_message(message.chat.id, "📂 **ДОКУМЕНТЫ:**\n1. Паспорт\n2. Аттестат\n3. СНИЛС\n4. Фото\n5. Медсправка", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📩 Обратная связь")
def feedback(message):
    msg = bot.send_message(message.chat.id, "✍️ Напиши сообщение админу:")
    bot.register_next_step_handler(msg, lambda m: bot.send_message(ADMIN_ID, f"📩 {m.from_user.username}: {m.text}"))

@bot.message_handler(func=lambda m: m.text == "📄 Памятка")
def send_pdf(message):
    if os.path.exists(PAMYATKA_FILE):
        with open(PAMYATKA_FILE, 'rb') as f: bot.send_document(message.chat.id, f)
    else: bot.send_message(message.chat.id, "Файл не найден.")

# --- АДМИНКА ---
@bot.message_handler(commands=['sendall'])
def admin_send(message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text.replace('/sendall', '').strip()
    ids = set()
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8-sig') as f:
            for row in csv.reader(f, delimiter=';'):
                if len(row) > 0 and row[0].isdigit(): ids.add(row[0])
    for uid in ids:
        try: bot.send_message(uid, text)
        except: pass
    bot.send_message(message.chat.id, f"✅ Отправлено: {len(ids)}")

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        with open(STATS_FILE, 'rb') as f: bot.send_document(message.chat.id, f)
    except: bot.send_message(message.chat.id, "База пуста.")

try:
    print("Бот запущен...")
    bot.polling(none_stop=True)
except Exception as e:
    print(f"Ошибка: {e}")
