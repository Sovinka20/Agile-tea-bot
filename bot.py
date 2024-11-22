import logging
import os
import time
from datetime import datetime

import psycopg2
import requests
import telebot
from dotenv import load_dotenv
from telebot import types

from admin_commands import add_content, get_users_data
# Импорт функций из других файлов
from commands import (button, help, new_tea, start, try_delete_message,
                      unknown_command)

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

# Регистрация обработчиков команд
bot.message_handler(commands=['start'])(lambda message: start(message, bot, try_delete_message))
bot.message_handler(commands=['new_tea'])(lambda message: new_tea(message, bot, try_delete_message))
bot.message_handler(commands=['help'])(lambda message: help(message, bot, try_delete_message))
bot.message_handler(commands=['add_content'])(lambda message: add_content(message, bot, try_delete_message))
bot.message_handler(commands=['get_users_data'])(lambda message: get_users_data(message, bot, try_delete_message))
bot.callback_query_handler(func=lambda call: True)(lambda call: button(call, bot, get_content_by_id, add_user_data, try_delete_message))
bot.message_handler(func=lambda message: True)(lambda message: unknown_command(message, bot, try_delete_message))

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
