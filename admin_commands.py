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

# Функция для проверки наличия достижения у пользователя
def has_achievement(cur, user_id, achievement_id):
    cur.execute('''
        SELECT COUNT(*) FROM user_achievements
        WHERE user_id = %s AND achievement_id = %s
    ''', (user_id, achievement_id))
    return cur.fetchone()[0] > 0

# Обработчик команды /add_content
def add_content(message, bot, try_delete_message, save_message_id):
    try:
        if not is_allowed_user(message.from_user.id):
            bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")
            return

        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Получаем всех пользователей
                cur.execute('SELECT user_id FROM users')
                users = cur.fetchall()

                for user in users:
                    user_id = user[0]

                    # Добавляем первое достижение, если его еще нет
                    if not has_achievement(cur, user_id, 1):
                        add_achievement(cur, user_id, 1)
                        bot.send_message(message.chat.id, "Перерасчёт 1-го достижения запущен...")
                    # Проверяем, сколько раз пользователь был добавлен в базу данных
                    cur.execute('SELECT COUNT(*) FROM users WHERE user_id = %s', (user_id,))
                    count = cur.fetchone()[0]

                    # Добавляем достижения в зависимости от количества, если их еще нет
                    if count >= 12 and not has_achievement(cur, user_id, 2):
                        add_achievement(cur, user_id, 2)
                        bot.send_message(message.chat.id, "Перерасчёт 2-го достижения запущен...")

                    if count >= 20 and not has_achievement(cur, user_id, 3):
                        add_achievement(cur, user_id, 3)
                        bot.send_message(message.chat.id, "Перерасчёт 3-го достижения запущен...")

        bot.send_message(message.chat.id, "Достижения успешно пересчитаны для всех пользователей.")
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')

    except Exception as e:
        logging.exception("Ошибка при пересчете достижений")
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
