import psycopg2
import telebot
from telebot import types
from datetime import datetime
import time
from dotenv import load_dotenv
import os

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение переменных окружения
DATABASE_URL = os.getenv('DATABASE_URL')
TOKEN = os.getenv('TOKEN')

# Подключение к PostgreSQL
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Функция для получения содержимого по id из таблицы bot_content
def get_content_by_id(content_id):
    cur.execute('''
        SELECT content, image FROM bot_content WHERE id = %s
    ''', (content_id,))
    result = cur.fetchone()
    return result if result else (None, None)

# Функция для получения текущей даты
def get_current_date():
    # Получаем текущую дату и время
    now = datetime.now()
    # Форматируем дату в строку формата YYYY-MM-DD
    current_date = now.strftime("%Y-%m-%d")
    return current_date

# Функция для добавления данных в таблицу users
def add_user_data(user_id, username, select_tea):
    date = get_current_date()
    cur.execute('''
        INSERT INTO users (user_id, username, date, select_tea, age, gender)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (user_id, username, date, select_tea, 0, 'u'))
    conn.commit()

# Создание экземпляра бота
bot = telebot.TeleBot(TOKEN)

# Обработчик команды /new_tea
@bot.message_handler(commands=['new_tea'])
def start(message):
    keyboard = types.InlineKeyboardMarkup()
    buttons = []
    for i in range(1, 13):
        buttons.append(types.InlineKeyboardButton(str(i), callback_data=str(i)))
        if len(buttons) == 3:
            keyboard.row(*buttons)
            buttons = []
    if buttons:
        keyboard.row(*buttons)
    bot.send_message(message.chat.id, 'Выберите номер:', reply_markup=keyboard)

# Обработчик нажатия на кнопку
@bot.callback_query_handler(func=lambda call: True)
def button(call):
    content_id = int(call.data)
    content, image = get_content_by_id(content_id)

    if content:
        # Используем HTML-разметку для отображения текста крупнее
        formatted_content = f"<b>{content}</b>"
        if image:
            bot.send_photo(call.message.chat.id, image, caption=formatted_content, parse_mode='HTML')
        else:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=formatted_content, parse_mode='HTML')
        add_user_data(call.from_user.id, call.from_user.username, content_id)
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Содержимое не найдено.")

    # Удаление сообщения с клавиатурой
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

# Запуск бота с увеличенным временем ожидания и обработкой исключений
def main():
    while True:
        try:
            bot.polling(none_stop=True, timeout=30, long_polling_timeout=30)
        except Exception as e:
            print(f"Ошибка: {e}")
            print("Переподключение через 5 секунд...")
            time.sleep(5)

if __name__ == '__main__':
    main()
