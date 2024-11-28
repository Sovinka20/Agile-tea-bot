import logging
import os
from datetime import datetime

import pandas as pd
import psycopg2
from dotenv import load_dotenv

from message_utils import save_message_id, try_delete_message
from utils import get_current_date

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение переменных окружения
DATABASE_URL = os.getenv('DATABASE_URL')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID'))
MODER_USER_IDS = [int(os.getenv(f'MODER_USER_ID{i}')) for i in range(6)]

# Функция для проверки прав доступа
def is_allowed_user(user_id):
    return user_id in [ADMIN_USER_ID] + MODER_USER_IDS

# Общая функция для добавления достижений
def add_achievement(cur, user_id, achievement_id):
    current_date = get_current_date()
    cur.execute('''
        INSERT INTO user_achievements (user_id, achievement_id, date_achieved)
        VALUES (%s, %s, %s)
    ''', (user_id, achievement_id, current_date))

# Обработчик команды /add_content
def add_content(message, bot, try_delete_message, save_message_id):
    try:
        if not is_allowed_user(message.from_user.id):
            bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")
            return

        TEST_USER_ID = 1615170105

        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                add_achievement(cur, TEST_USER_ID, 1)
                bot.send_message(TEST_USER_ID, "Поздравляем! Ваше новое достижение - КУСОЧЕК САХАРА!")
                sugar_file_path = os.path.join('a_piece_of_sugar.gif')
                if os.path.exists(sugar_file_path):
                    with open(sugar_file_path, 'rb') as file:
                        bot.send_document(TEST_USER_ID, file)
                else:
                    logging.error(f"Файл '{sugar_file_path}' не найден.")

                cur.execute('SELECT COUNT(*) FROM users WHERE user_id = %s', (TEST_USER_ID,))
                count = cur.fetchone()[0]

                if count >= 12:
                    add_achievement(cur, TEST_USER_ID, 2)
                    bot.send_message(TEST_USER_ID, "Поздравляем! Ваше новое достижение - Чайный лист! Вы выбрали чаи 12 раз!")
                    tea_leaf_file_path = os.path.join('tea_leaf.jpg')
                    if os.path.exists(tea_leaf_file_path):
                        with open(tea_leaf_file_path, 'rb') as file:
                            bot.send_document(TEST_USER_ID, file)
                    else:
                        logging.error(f"Файл '{tea_leaf_file_path}' не найден.")

        bot.send_message(message.chat.id, "Таблицы unique_users, achievements и user_achievements успешно созданы и заполнены данными.")
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')

    except Exception as e:
        logging.exception("Ошибка при добавлении новых столбцов и данных")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Общая функция для получения и отправки данных
def fetch_and_send_data(call, message, bot, query, output_file):
    try:
        if not is_allowed_user(call.from_user.id):
            bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")
            save_message_id(message.chat.id, 'command', message.message_id)
            try_delete_message(bot, message.chat.id, 'command')
            return

        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')

        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]

        df = pd.DataFrame(rows, columns=columns)
        df.to_excel(output_file, index=False)

        with open(output_file, 'rb') as file:
            bot.send_document(message.chat.id, file)

        logging.info(f"Данные успешно сохранены в {output_file} и отправлены пользователю {message.from_user.id}")
    except Exception as e:
        logging.exception(f"Ошибка при получении данных: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /get_users_data
def get_users_data(call, message, bot, try_delete_message, save_message_id):
    query = '''
        SELECT user_id, username, date, select_tea, age, gender FROM users
    '''
    fetch_and_send_data(call, message, bot, query, 'parsed_data.xlsx')

# Обработчик команды /get_unique_users_data
def get_unique_users_data(call, message, bot, try_delete_message, save_message_id):
    query = '''
        SELECT user_id, username, date_start, date_last, age, gender, evaluation, count_achievements FROM unique_users
    '''
    fetch_and_send_data(call, message, bot, query, 'unique_users_data.xlsx')

# Проверка наличия необходимых переменных окружения
if not DATABASE_URL:
    logging.error("Переменная окружения DATABASE_URL не определена.")
    exit(1)

# Проверка наличия таблиц в базе данных перед выполнением запросов
def check_table_exists(table_name):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')")
            return cur.fetchone()[0]

if not check_table_exists('users'):
    logging.error("Таблица 'users' не существует.")
    exit(1)

if not check_table_exists('unique_users'):
    logging.error("Таблица 'unique_users' не существует.")
    exit(1)
