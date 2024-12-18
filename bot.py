import logging
import os
import time
from datetime import datetime

import psycopg2
import requests
import telebot
from dotenv import load_dotenv
from telebot import types

from admin_commands import (add_content, get_unique_users_data,
                            get_users_achievements_data, get_users_data)
from message_utils import save_message_id, try_delete_message
from utils import (close_connection, get_current_date, is_allowed_user,
                   open_connection)

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение переменных окружения
DATABASE_URL = os.getenv('DATABASE_URL')
TOKEN = os.getenv('TOKEN')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID'))
MODER_USER_IDS = [int(os.getenv(f'MODER_USER_ID{i}')) for i in range(6)]

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание экземпляра бота
bot = telebot.TeleBot(TOKEN)

# Словарь для сопоставления текста на кнопках с полями в базе данных
button_to_field = {
    'age_14': 'age',
    'age_15_21': 'age',
    'age_22_45': 'age',
    'age_45+': 'age',
    'gender_male': 'gender',
    'gender_female': 'gender',
    'eval_1': 'evaluation',
    'eval_2': 'evaluation',
    'eval_3': 'evaluation',
    'eval_4': 'evaluation',
    'eval_5': 'evaluation',
    'tea_1': 'favorite_tea',
    'tea_2': 'favorite_tea',
    'tea_3': 'favorite_tea',
    'tea_4': 'favorite_tea',
    'tea_5': 'favorite_tea',
    'tea_6': 'favorite_tea',
    'tea_7': 'favorite_tea',
    'tea_8': 'favorite_tea',
    'tea_9': 'favorite_tea',
    'tea_10': 'favorite_tea',
    'tea_11': 'favorite_tea',
    'tea_12': 'favorite_tea',
    'cancel': None  # Отмена не требует обновления данных
}

# Словарь для сопоставления текста на кнопках с конкретными значениями
button_to_value = {
    'age_14': 'до 14',
    'age_15_21': 'от 15 до 21',
    'age_22_45': 'от 22 до 45',
    'age_45+': '45+',
    'gender_male': 'муж.',
    'gender_female': 'жен.',
    'eval_1': 1,
    'eval_2': 2,
    'eval_3': 3,
    'eval_4': 4,
    'eval_5': 5,
    'tea_1': 1,
    'tea_2': 2,
    'tea_3': 3,
    'tea_4': 4,
    'tea_5': 5,
    'tea_6': 6,
    'tea_7': 7,
    'tea_8': 8,
    'tea_9': 9,
    'tea_10': 10,
    'tea_11': 11,
    'tea_12': 12,
    'cancel': None  # Отмена не требует обновления данных
}


# Функция для повторных попыток подключения к базе данных
def connect_to_db(max_retries=3, delay=5):
    retries = 0
    while retries < max_retries:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            logging.info("Успешное подключение к базе данных")
            return conn
        except Exception as e:
            logging.error(f"Ошибка подключения к базе данных: {e}")
            retries += 1
            time.sleep(delay)
    logging.error("Превышено количество попыток подключения к базе данных")
    return None

# Функция для получения содержимого по id из таблицы bot_content
def get_content_by_id(content_id):
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT content, image, tea_name, quote_agile, question, link, id FROM bot_content WHERE id = %s', (content_id,))
            result = cur.fetchone()
            if result:
                return result
            else:
                return (None, None, None, None, None, None, None)
    except Exception as e:
        logging.error(f"Ошибка при выполнении SQL-запроса: {e}")
        return (None, None, None, None, None, None, None)

# Функция для добавления данных в таблицу users
def add_user_data(user_id, username, select_tea):
    conn = connect_to_db()
    if conn is None:
        return
    date = get_current_date()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO users (user_id, username, date, select_tea, age, gender)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, username, date, select_tea, 0, 'u'))
            conn.commit()
    except Exception as e:
        logging.error(f"Ошибка при добавлении данных в таблицу users: {e}")
    finally:
        conn.close()

# Общая функция для добавления достижений
def add_select_all_data_tea(user_id, select_id):
    conn = connect_to_db()
    if conn is None:
        return
    date = get_current_date()
    try:
        with conn.cursor() as cur:
            cur.execute('''
            INSERT INTO users_all_data_card_tea (user_id, select_id, date_achieved)
            VALUES (%s, %s, %s)
        ''', (user_id, select_id, date))
        conn.commit()
    except Exception as e:
        logging.error(f"Ошибка при добавлении данных в таблицу users: {e}")
    finally:
        conn.close()

def update_user_data(message, id_users, button_data):
    """
    Обновляет данные пользователя в таблице unique_users по id_users на основе текста на кнопках.

    :param id_users: ID пользователя в таблице unique_users.
    :param button_data: Текст на кнопке, который нужно обработать.
    """
    conn = connect_to_db()
    if conn is None:
        return
    try:
        # Получаем поле и значение для обновления
        field = button_to_field.get(button_data)
        value = button_to_value.get(button_data)

        if field is None or value is None:
            return  # Если кнопка "Отмена" или неизвестная кнопка, ничего не делаем

        with conn.cursor() as cur:
            # Формирование SQL-запроса для обновления данных
            query = f"UPDATE unique_users SET {field} = %s WHERE user_id = %s"
            cur.execute(query, (value, id_users))
            conn.commit()
            logging.info(f"Данные пользователя с id_users={id_users} обновлены: {field}={value}")
            bot.send_message(message.chat.id, "Данные успешно обновлены!")
    except Exception as e:
        logging.error(f"Ошибка при обновлении данных пользователя с id_users={id_users}: {e}")
    finally:
        conn.close()

# Регистрация обработчиков команд
@bot.message_handler(commands=['start'])
def handle_start(message):
    from commands import start
    start(message, bot)

@bot.message_handler(commands=['new_tea'])
def handle_new_tea(message):
    from commands import new_tea
    new_tea(message, bot)

@bot.message_handler(commands=['help'])
def handle_help(message):
    from commands import help
    help(message, bot)

@bot.message_handler(commands=['add_content'])
def handle_add_content(message):
    from admin_commands import add_content
    add_content(message, bot)

@bot.message_handler(commands=['get_users_data'])
def handle_get_users_data(message):
    from admin_commands import get_users_data
    get_users_data(message, bot)

@bot.message_handler(commands=['get_unique_users_data'])
def handle_get_unique_users_data(message):
    from admin_commands import get_unique_users_data
    get_unique_users_data(message, bot)

@bot.message_handler(commands=['get_users_achievements_data'])
def handle_get_users_achievements_data(message):
    from admin_commands import get_users_achievements_data
    get_users_achievements_data(message, bot)

@bot.message_handler(commands=['my_commands'])
def handle_my_commands_command(message):
    from commands import my_commands
    my_commands(message, bot)

@bot.message_handler(commands=['create_age'])
def handle_create_age(message):
    from commands import create_age
    create_age(message, bot)

@bot.message_handler(commands=['create_gender'])
def handle_create_gender(message):
    from commands import create_gender
    create_gender(message, bot)

@bot.message_handler(commands=['create_favorite_tea'])
def handle_create_favorite_tea(message):
    from commands import create_favorite_tea
    create_favorite_tea(message, bot)

@bot.message_handler(commands=['create_evaluation'])
def handle_create_evaluation(message):
    from commands import create_evaluation
    create_evaluation(message, bot)

@bot.message_handler(commands=['my_profile'])
def handle_my_profile(message):
    from commands import my_profile
    my_profile(message, bot)

@bot.message_handler(commands=['edit_profile'])
def handle_my_profile(message):
    from commands import edit_profile
    edit_profile(message, bot)

@bot.message_handler(commands=['tea_random'])
def handle_tea_random(message):
    from commands import tea_random
    tea_random(message, bot)

@bot.message_handler(commands=['my_achievements'])
def handle_my_achievements(message):
    from commands import my_achievements
    my_achievements(message, bot)

# Обработчик колбэков
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    try:
        if call.data == 'get_users_data':
            get_users_data(call, call.message, bot)
        elif call.data == 'get_unique_users_data':
            get_unique_users_data(call, call.message, bot)
        elif call.data == 'get_users_achievements_data':
            get_users_achievements_data(call, call.message, bot)
        elif call.data == 'start':
            from commands import start
            start(call.message, bot)
        elif call.data == 'new_tea':
            from commands import new_tea
            new_tea(call.message, bot)
        elif call.data == 'tea_random':
            from commands import tea_random
            tea_random(call.message, bot)
        elif call.data == 'help':
            from commands import help
            help(call.message, bot, try_delete_message, save_message_id)
        elif call.data == 'cancel':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            try_delete_message(bot, call.message.chat.id, 'command')
        elif call.data == 'my_profile':
            from commands import my_profile
            my_profile(call.message, bot)
        elif call.data == 'edit_profile':
            from commands import edit_profile
            edit_profile(call.message, bot)
        
        elif call.data == 'create_age':
            from commands import create_age
            create_age(call.message, bot)
        elif call.data == 'create_gender':
            from commands import create_gender
            create_gender(call.message, bot)
        elif call.data == 'create_favorite_tea':
            from commands import create_favorite_tea
            create_favorite_tea(call.message, bot)
        elif call.data == 'create_evaluation':
            from commands import create_evaluation
            create_evaluation(call.message, bot)
        elif call.data == 'my_achievements':
            from commands import my_achievements
            my_achievements(call.message, bot)
            
        elif call.data.startswith('age_'):
            update_user_data(call.message, call.from_user.id, call.data)
        elif call.data.startswith('gender_'):
            update_user_data(call.message, call.from_user.id, call.data)
        elif call.data.startswith('tea_'):
            update_user_data(call.message, call.from_user.id, call.data)
        elif call.data.startswith('eval_'):
            update_user_data(call.message, call.from_user.id, call.data)
        elif call.data.startswith('view_profile'):
            handle_view_profile_callback(call)
        elif call.data.startswith('edit_profile'):
            handle_edit_profile_callback(call)
        elif call.data.startswith('edit_'):
            handle_edit_callback(call)
        elif call.data == 'more_tea':
            handle_more_tea_callback(call)
        else:
            from commands import button
            button(call, bot)

        bot.delete_message(call.message.chat.id, call.message.message_id)
        try_delete_message(bot, call.message.chat.id, 'command')
    except Exception as e:
        logging.error(f"Ошибка при обработке колбэка: {e}")

@bot.message_handler(func=lambda message: True)
def handle_unknown_command(message):
    from commands import unknown_command
    unknown_command(message, bot, try_delete_message, save_message_id)
    try_delete_message(bot, message.chat.id, 'command')

# Запуск бота с повторными попытками
def start_polling():
    while True:
        try:
            bot.polling(none_stop=True)
        except requests.exceptions.ConnectionError as e:
            logging.error(f"Ошибка подключения: {e}")
            time.sleep(10)
        except requests.exceptions.ReadTimeout as e:
            logging.error(f"Ошибка таймаута чтения: {e}")
            time.sleep(10)
        except requests.exceptions.Timeout as e:
            logging.error(f"Ошибка таймаута: {e}")
            time.sleep(10)
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка запроса: {e}")
            time.sleep(10)
        except telebot.apihelper.ApiTelegramException as e:
            if e.error_code == 502:
                logging.warning(f"Ошибка 502 Bad Gateway: {e}")
                time.sleep(10)
            else:
                logging.error(f"Ошибка API Telegram: {e}")
                time.sleep(10)
        except Exception as e:
            logging.error(f"Непредвиденная ошибка: {e}")
            time.sleep(10)

# Запуск опроса
start_polling()
