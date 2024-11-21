import logging
import os
import time
from datetime import datetime

import psycopg2
import requests
import telebot
from dotenv import load_dotenv
from telebot import types
import pandas as pd

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение переменных окружения
DATABASE_URL = os.getenv('DATABASE_URL')
TOKEN = os.getenv('TOKEN')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID'))
MODER_USER_ID0 = int(os.getenv('MODER_USER_ID0'))
MODER_USER_ID1 = int(os.getenv('MODER_USER_ID1'))
MODER_USER_ID2 = int(os.getenv('MODER_USER_ID2'))
MODER_USER_ID3 = int(os.getenv('MODER_USER_ID3'))
MODER_USER_ID4 = int(os.getenv('MODER_USER_ID4'))
MODER_USER_ID5 = int(os.getenv('MODER_USER_ID5'))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Подключение к PostgreSQL
try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    logging.info("Успешное подключение к базе данных")
except Exception as e:
    logging.error(f"Ошибка подключения к базе данных: {e}")
    exit()

# Функция для получения содержимого по id из таблицы bot_content
def get_content_by_id(content_id):
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT content, image FROM bot_content WHERE id = %s
                ''', (content_id,))
                result = cur.fetchone()
                return result if result else (None, None)
    except Exception as e:
        logging.error(f"Ошибка при выполнении SQL-запроса: {e}")
        return (None, None)

# Функция для получения текущей даты
def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")

# Функция для добавления данных в таблицу users
def add_user_data(user_id, username, select_tea):
    date = get_current_date()
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO users (user_id, username, date, select_tea, age, gender)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (user_id, username, date, select_tea, 0, 'u'))
                conn.commit()
    except Exception as e:
        logging.error(f"Ошибка при добавлении данных в таблицу users: {e}")

# Функция для проверки прав доступа
def is_allowed_user(user_id):
    allowed_users = [ADMIN_USER_ID, MODER_USER_ID0, MODER_USER_ID1, MODER_USER_ID2, MODER_USER_ID3, MODER_USER_ID4, MODER_USER_ID5]
    return user_id in allowed_users

# Создание экземпляра бота
bot = telebot.TeleBot(TOKEN)

# Словарь для хранения идентификаторов сообщений с командами и клавиатурой
message_ids = {}

# Функция для создания клавиатуры с кнопками
def create_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(1, 13)]
    for i in range(0, len(buttons), 3):
        keyboard.row(*buttons[i:i+3])
    return keyboard

# Функция для попытки удаления сообщения с проверкой
def try_delete_message(chat_id, message_type):
    if chat_id in message_ids and message_type in message_ids[chat_id]:
        message_id = message_ids[chat_id][message_type]
        try:
            bot.delete_message(chat_id=chat_id, message_id=message_id)
            del message_ids[chat_id][message_type]
        except telebot.apihelper.ApiTelegramException as e:
            if e.error_code == 400 and 'message to delete not found' in e.description:
                logging.warning(f"Сообщение уже удалено или не найдено: {e.error_code} - {e.description} (chat_id: {chat_id}, message_type: {message_type}, message_id: {message_id})")
                del message_ids[chat_id][message_type]  # Удаляем запись из словаря, чтобы избежать повторных попыток удаления
            else:
                logging.error(f"Ошибка удаления сообщения: {e.error_code} - {e.description} (chat_id: {chat_id}, message_type: {message_type}, message_id: {message_id})")
    else:
        logging.warning(f"Сообщение типа '{message_type}' для чата {chat_id} не найдено в словаре message_ids.")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    try:
        try_delete_message(message.chat.id, 'keyboard')
        keyboard = types.InlineKeyboardMarkup()
        bot.send_message(message.chat.id, 'Добро пожаловать в чай-бот принципов Agile!', reply_markup=keyboard)
        message_ids[message.chat.id] = {'command': message.message_id}
        try_delete_message(message.chat.id, 'command')
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /start: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /new_tea
@bot.message_handler(commands=['new_tea'])
def new_tea(message):
    try:
        try_delete_message(message.chat.id, 'keyboard')
        keyboard = create_keyboard()
        sent_message = bot.send_message(message.chat.id, 'Выберите номер:', reply_markup=keyboard)
        message_ids[message.chat.id] = {'command': message.message_id, 'keyboard': sent_message.message_id}
        try_delete_message(message.chat.id, 'command')
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /new_tea: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /help
@bot.message_handler(commands=['help'])
def help(message):
    try:
        try_delete_message(message.chat.id, 'keyboard')
        bot.send_message(message.chat.id, 'Этот бот помогает изучать принципы Agile. Используйте команду /new_tea для начала.')
        message_ids[message.chat.id] = {'command': message.message_id}
        try_delete_message(message.chat.id, 'command')
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /help: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /add_content
@bot.message_handler(commands=['add_content'])
def add_content(message):
    try:
        if message.from_user.id == ADMIN_USER_ID:
            # setup_unique_users_table()
            # setup_achievements_tables()
            bot.send_message(message.chat.id, "Таблицы unique_users, achievements и user_achievements успешно созданы и заполнены данными.")
        else:
            bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")
    except Exception as e:
        logging.error(f"Ошибка при добавлении новых столбцов и данных: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /get_users_data
@bot.message_handler(commands=['get_users_data'])
def get_users_data(message):
    try:
        if not is_allowed_user(message.from_user.id):
            bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")
            return

        # Получение данных из таблицы users
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT user_id, username, date, select_tea, age, gender FROM users
                ''')
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]

        # Создание DataFrame из полученных данных
        df = pd.DataFrame(rows, columns=columns)

        # Путь для сохранения результата в формате XLSX
        output_file = 'parsed_data.xlsx'

        # Сохранение данных в XLSX файл
        df.to_excel(output_file, index=False)

        # Отправка файла пользователю
        with open(output_file, 'rb') as file:
            bot.send_document(message.chat.id, file)

        logging.info(f"Данные успешно сохранены в {output_file} и отправлены пользователю {message.from_user.id}")
    except Exception as e:
        logging.error(f"Ошибка при получении данных пользователей: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик нажатия на кнопку
@bot.callback_query_handler(func=lambda call: True)
def button(call):
    try:
        content_id = int(call.data)
        content, image = get_content_by_id(content_id)

        if content:
            formatted_content = f"<b>{content}</b>"
            if image:
                bot.send_photo(call.message.chat.id, image, caption=formatted_content, parse_mode='HTML')
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=formatted_content, parse_mode='HTML')
            add_user_data(call.from_user.id, call.from_user.username, content_id)
        else:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Содержимое не найдено.")

        try_delete_message(call.message.chat.id, 'keyboard')
        try_delete_message(call.message.chat.id, 'command')
        new_tea(call.message)
    except Exception as e:
        logging.error(f"Ошибка в обработчике нажатия на кнопку: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик неопознанных команд
@bot.message_handler(func=lambda message: True)
def unknown_command(message):
    bot.send_message(message.chat.id, "Простите, такой команды нет. Используйте /help для получения справки.")

# Запуск бота с повторными попытками
def start_polling():
    while True:
        try:
            bot.polling(none_stop=True)
        except requests.exceptions.ConnectionError as e:
            logging.error(f"Ошибка подключения: {e}")
            time.sleep(10)  # Подождать 10 секунд перед повторной попыткой
        except requests.exceptions.ReadTimeout as e:
            logging.error(f"Ошибка таймаута чтения: {e}")
            time.sleep(10)  # Подождать 10 секунд перед повторной попыткой
        except requests.exceptions.Timeout as e:
            logging.error(f"Ошибка таймаута: {e}")
            time.sleep(10)  # Подождать 10 секунд перед повторной попыткой
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка запроса: {e}")
            time.sleep(10)  # Подождать 10 секунд перед повторной попыткой
        except telebot.apihelper.ApiTelegramException as e:
            if e.error_code == 502:
                logging.warning(f"Ошибка 502 Bad Gateway: {e}")
                time.sleep(10)  # Подождать 10 секунд перед повторной попыткой
            else:
                logging.error(f"Ошибка API Telegram: {e}")
                time.sleep(10)  # Подождать 10 секунд перед повторной попыткой
        except Exception as e:
            logging.error(f"Непредвиденная ошибка: {e}")
            time.sleep(10)  # Подождать 10 секунд перед повторной попыткой

# Запуск опроса
start_polling()
