import logging
import os
from datetime import datetime

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from telebot import types

from message_utils import save_message_id, try_delete_message
from utils import get_current_date, is_allowed_user

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение переменных окружения
DATABASE_URL = os.getenv('DATABASE_URL')

# Список ID администраторов
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS').split(',')))

def update_achievement_image(message, bot):
    try:
        user_id = message.from_user.id

        # Проверка, является ли пользователь администратором
        if user_id not in ADMIN_IDS:
            bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")
            return

        # Запрашиваем у администратора ID достижения и имя файла
        bot.send_message(message.chat.id, "Введите ID достижения и имя файла изображения в формате:\n"
                                        "<achievement_id> <image_filename>\n"
                                        "Пример: 1 'a_piece_of_sugar.gif'")
        bot.register_next_step_handler(message, process_achievement_image_update, bot)

    except Exception as e:
        logging.error(f"Ошибка в команде /update_achievement_image: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

def process_achievement_image_update(message, bot):
    try:
        user_id = message.from_user.id

        # Проверка, является ли пользователь администратором
        if user_id not in ADMIN_IDS:
            bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")
            return

        # Разбиваем введённые данные на части
        data = message.text.split(maxsplit=1)
        if len(data) != 2:
            bot.send_message(message.chat.id, "Неверный формат данных. Пожалуйста, попробуйте ещё раз.")
            return

        achievement_id, image_filename = data

        # Проверяем, существует ли файл с изображением
        image_path = os.path.join(os.getcwd(), image_filename.strip())
        if not os.path.exists(image_path):
            bot.send_message(message.chat.id, f"Файл '{image_filename}' не найден.")
            return

        # Читаем бинарные данные изображения
        with open(image_path, 'rb') as f:
            image_data = f.read()

        # Обновляем поле image_achievements в таблице achievements
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    UPDATE achievements
                    SET image_achievements = %s
                    WHERE achievement_id = %s
                ''', (image_data, int(achievement_id)))
                conn.commit()

        bot.send_message(message.chat.id, f"Изображение для достижения с ID {achievement_id} успешно обновлено!")

    except Exception as e:
        logging.error(f"Ошибка при обновлении изображения достижения: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

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

# Функция для обновления полей count_select_tea и count_achievements
def update_user_counts(cur, user_id):
    # Подсчет строк в таблице users для данного user_id
    cur.execute('SELECT COUNT(*) FROM users WHERE user_id = %s', (user_id,))
    count_select_tea = cur.fetchone()[0]

    # Подсчет строк в таблице user_achievements для данного user_id
    cur.execute('SELECT COUNT(*) FROM user_achievements WHERE user_id = %s', (user_id,))
    count_achievements = cur.fetchone()[0]

    # Обновление полей в таблице unique_users
    cur.execute('''
        UPDATE unique_users
        SET count_select_tea = %s, count_achievements = %s
        WHERE user_id = %s
    ''', (count_select_tea, count_achievements, user_id))


# Обнолвени таблицы uniqie_users
def add_content(message, bot):
    try:
        logging.info(is_allowed_user(message.from_user.id))

        if not is_allowed_user(message.from_user.id):
            bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")
            save_message_id(message.chat.id, 'command', message.message_id)
            try_delete_message(bot, message.chat.id, 'command')
            # return


        bot.send_message(message.chat.id, "Процесс запущен, ожидайте...")
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')


        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Получаем всех пользователей из таблицы users
                cur.execute('''
                    SELECT user_id, username, MIN(date) as date_start, MAX(date) as date_last 
                    FROM users 
                    GROUP BY user_id, username
                ''')
                users = cur.fetchall()

                for user in users:
                    user_id, username, date_start, date_last = user

                    # Проверяем, существует ли пользователь в таблице unique_users
                    cur.execute('SELECT EXISTS(SELECT 1 FROM unique_users WHERE user_id = %s)', (user_id,))
                    exists = cur.fetchone()[0]

                    # Если пользователь не существует, добавляем его в таблицу unique_users
                    if not exists:
                        cur.execute('''
                            INSERT INTO unique_users (user_id, username, date_start, date_last)
                            VALUES (%s, %s, %s, %s)
                        ''', (user_id, username, date_start, date_last))
                    else:
                        # Если пользователь существует, обновляем date_last
                        cur.execute('''
                            UPDATE unique_users
                            SET date_last = %s
                            WHERE user_id = %s
                        ''', (date_last, user_id))

                # Получаем всех пользователей из таблицы unique_users
                cur.execute('SELECT user_id FROM unique_users')
                unique_users = cur.fetchall()

                for user in unique_users:
                    user_id = user[0]

                    # Добавляем первое достижение, если его еще нет
                    if not has_achievement(cur, user_id, 1):
                        add_achievement(cur, user_id, 1)

                    # Проверяем, сколько раз пользователь был добавлен в базу данных
                    cur.execute('SELECT COUNT(*) FROM users WHERE user_id = %s', (user_id,))
                    count = cur.fetchone()[0]

                    # Добавляем достижения в зависимости от количества, если их еще нет
                    if count >= 12 and not has_achievement(cur, user_id, 2):
                        add_achievement(cur, user_id, 2)

                    if count >= 20 and not has_achievement(cur, user_id, 3):
                        add_achievement(cur, user_id, 3)

                    # Обновляем поля count_select_tea и count_achievements
                    update_user_counts(cur, user_id)

        bot.send_message(message.chat.id, "Достижения и счетчики успешно пересчитаны для всех пользователей.")

    except Exception as e:
        logging.exception("Ошибка при пересчете достижений и счетчиков")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")
    finally:
        conn.close()

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
    finally:
        conn.close()

# Обработчик команды /get_users_achievements_data
def get_users_achievements_data(call, message, bot):
    query = '''
        SELECT user_achievement_id, user_id, achievement_id, date_achieved FROM user_achievements
    '''
    fetch_and_send_data(call, message, bot, query, 'achievements_data.xlsx')


# Обработчик команды /get_users_data
def get_users_data(call, message, bot):
    query = '''
        SELECT user_id, username, date, select_tea, age, gender FROM users
    '''
    fetch_and_send_data(call, message, bot, query, 'parsed_data.xlsx')

# Обработчик команды /get_unique_users_data
def get_unique_users_data(call, message, bot):
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

if not check_table_exists('user_achievements'):
    logging.error("Таблица 'user_achievements' не существует.")
    exit(1)
