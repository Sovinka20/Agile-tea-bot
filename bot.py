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
                            get_users_achievements_data, get_users_data,
                            update_achievement_image)
from commands import (button, create_age, create_evaluation,
                      create_favorite_tea, create_gender, edit_profile, help,
                      my_achievements, my_commands, my_profile, new_tea, start,
                      tea_random, unknown_command)
from message_utils import save_message_id, try_delete_message
from utils import (close_connection, get_current_date, is_allowed_user, logger,
                   open_connection)

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение переменных окружения
DATABASE_URL = os.getenv('DATABASE_URL')
TOKEN = os.getenv('TOKEN')

# Создание экземпляра бота
bot = telebot.TeleBot(TOKEN)




# Словарь для сопоставления текста на кнопках с полями и значениями в базе данных
button_mapping = {
    'age_14': {'field': 'age', 'value': 'до 14'},
    'age_15_21': {'field': 'age', 'value': 'от 15 до 21'},
    'age_22_45': {'field': 'age', 'value': 'от 22 до 45'},
    'age_45+': {'field': 'age', 'value': '45+'},
    'gender_male': {'field': 'gender', 'value': 'муж.'},
    'gender_female': {'field': 'gender', 'value': 'жен.'},
    'eval_1': {'field': 'evaluation', 'value': 1},
    'eval_2': {'field': 'evaluation', 'value': 2},
    'eval_3': {'field': 'evaluation', 'value': 3},
    'eval_4': {'field': 'evaluation', 'value': 4},
    'eval_5': {'field': 'evaluation', 'value': 5},
    'tea_1': {'field': 'favorite_tea', 'value': 1},
    'tea_2': {'field': 'favorite_tea', 'value': 2},
    'tea_3': {'field': 'favorite_tea', 'value': 3},
    'tea_4': {'field': 'favorite_tea', 'value': 4},
    'tea_5': {'field': 'favorite_tea', 'value': 5},
    'tea_6': {'field': 'favorite_tea', 'value': 6},
    'tea_7': {'field': 'favorite_tea', 'value': 7},
    'tea_8': {'field': 'favorite_tea', 'value': 8},
    'tea_9': {'field': 'favorite_tea', 'value': 9},
    'tea_10': {'field': 'favorite_tea', 'value': 10},
    'tea_11': {'field': 'favorite_tea', 'value': 11},
    'tea_12': {'field': 'favorite_tea', 'value': 12},
    'cancel': {'field': None, 'value': None}  # Отмена не требует обновления данных
}

# Функция для повторных попыток подключения к базе данных
def connect_to_db(max_retries=3, delay=5):
    retries = 0
    while retries < max_retries:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            logger.info("Успешное подключение к базе данных")
            return conn
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            retries += 1
            time.sleep(delay)
    logger.error("Превышено количество попыток подключения к базе данных")
    return None

# Функция для получения содержимого по id из таблицы bot_content
def get_content_by_id(content_id):
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT content, image, tea_name, quote_agile, question, link, id FROM bot_content WHERE id = %s', (content_id,))
                result = cur.fetchone()
                return result if result else (None, None, None, None, None, None, None)
    except Exception as e:
        logger.error(f"Ошибка при выполнении SQL-запроса: {e}")
        return (None, None, None, None, None, None, None)

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
        logger.error(f"Ошибка при добавлении данных в таблицу users: {e}")

# Общая функция для добавления достижений
def add_select_all_data_tea(user_id, select_id):
    date = get_current_date()
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO users_all_data_card_tea (user_id, select_id, date_achieved)
                    VALUES (%s, %s, %s)
                ''', (user_id, select_id, date))
                conn.commit()
    except Exception as e:
        logger.error(f"Ошибка при добавлении данных в таблицу users: {e}")

# Функция для обновления данных пользователя
def update_user_data(message, id_users, button_data):
    """
    Обновляет данные пользователя в таблице unique_users по id_users на основе текста на кнопках.

    :param id_users: ID пользователя в таблице unique_users.
    :param button_data: Текст на кнопке, который нужно обработать.
    """
    mapping = button_mapping.get(button_data)
    if not mapping or not mapping['field']:
        return  # Если кнопка "Отмена" или неизвестная кнопка, ничего не делаем

    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                query = f"UPDATE unique_users SET {mapping['field']} = %s WHERE user_id = %s"
                cur.execute(query, (mapping['value'], id_users))
                conn.commit()
                logger.info(f"Данные пользователя с id_users={id_users} обновлены: {mapping['field']}={mapping['value']}")
                bot.send_message(message.chat.id, "Данные успешно обновлены!")
    except Exception as e:
        logger.error(f"Ошибка при обновлении данных пользователя с id_users={id_users}: {e}")

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

@bot.message_handler(commands=['update_achievement_image'])
def handle_update_achievement_image(message):
    from admin_commands import update_achievement_image
    update_achievement_image(message, bot)

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
callback_handlers = {
    'get_users_data': lambda call: get_users_data(call, call.message, bot),
    'get_unique_users_data': lambda call: get_unique_users_data(call, call.message, bot),
    'get_users_achievements_data': lambda call: get_users_achievements_data(call, call.message, bot),
    'start': lambda call: start(call.message, bot),
    'new_tea': lambda call: new_tea(call.message, bot),
    'tea_random': lambda call: tea_random(call.message, bot),
    'help': lambda call: help(call.message, bot),
    'cancel': lambda call: bot.delete_message(call.message.chat.id, call.message.message_id),
    'my_profile': lambda call: my_profile(call.message, bot),
    'edit_profile': lambda call: edit_profile(call.message, bot),
    'create_age': lambda call: create_age(call.message, bot),
    'create_gender': lambda call: create_gender(call.message, bot),
    'create_favorite_tea': lambda call: create_favorite_tea(call.message, bot),
    'create_evaluation': lambda call: create_evaluation(call.message, bot),
    'my_achievements': lambda call: my_achievements(call.message, bot),
}

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    try:
        handler = callback_handlers.get(call.data)
        if handler:
            handler(call)
        elif call.data.startswith(('age_', 'gender_', 'tea_', 'eval_')):
            update_user_data(call.message, call.from_user.id, call.data)
        else:
            button(call, bot)

        bot.delete_message(call.message.chat.id, call.message.message_id)
        try_delete_message(bot, call.message.chat.id, 'command')
    except Exception as e:
        logger.error(f"Ошибка при обработке колбэка: {e}")

@bot.message_handler(func=lambda message: True)
def handle_unknown_command(message):
    unknown_command(message, bot)

# Запуск бота с повторными попытками
def start_polling(max_retries=10):
    retries = 0
    while retries < max_retries:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            retries += 1
            time.sleep(10)

# Запуск опроса
start_polling()
