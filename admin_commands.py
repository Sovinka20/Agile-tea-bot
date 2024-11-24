import logging
import os

import pandas as pd
import psycopg2
import telebot  # Добавлен импорт модуля telebot
from dotenv import load_dotenv

# Словарь для хранения идентификаторов сообщений с командами и клавиатурой
message_ids = {}

def try_delete_message(bot, chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        logging.error(f"Ошибка при удалении сообщения: {e}")

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение переменных окружения
DATABASE_URL = os.getenv('DATABASE_URL')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID'))
MODER_USER_ID0 = int(os.getenv('MODER_USER_ID0'))
MODER_USER_ID1 = int(os.getenv('MODER_USER_ID1'))
MODER_USER_ID2 = int(os.getenv('MODER_USER_ID2'))
MODER_USER_ID3 = int(os.getenv('MODER_USER_ID3'))
MODER_USER_ID4 = int(os.getenv('MODER_USER_ID4'))
MODER_USER_ID5 = int(os.getenv('MODER_USER_ID5'))

# Функция для проверки прав доступа
def is_allowed_user(user_id):
    allowed_users = [ADMIN_USER_ID, MODER_USER_ID0, MODER_USER_ID1, MODER_USER_ID2, MODER_USER_ID3, MODER_USER_ID4, MODER_USER_ID5]
    return user_id in allowed_users

# Обработчик команды /add_content
def add_content(message, bot, try_delete_message):
    try:
        if message.from_user.id == ADMIN_USER_ID:
            # setup_unique_users_table()
            # setup_achievements_tables()
            bot.send_message(message.chat.id, "Таблицы unique_users, achievements и user_achievements успешно созданы и заполнены данными.")
        else:
            bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")
        
        # Сохраняем идентификатор сообщения с командой
        message_ids[message.chat.id] = message.message_id
        
        try_delete_message(bot, message.chat.id, message_ids[message.chat.id])
    except Exception as e:
        logging.error(f"Ошибка при добавлении новых столбцов и данных: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /get_users_data
def get_users_data(message, bot, try_delete_message):
    try:
        if not is_allowed_user(message.from_user.id):
            bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")
            try_delete_message(bot, message.chat.id, message_ids[message.chat.id])
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
        
        # Сохраняем идентификатор сообщения с командой
        message_ids[message.chat.id] = message.message_id
        
        try_delete_message(bot, message.chat.id, message_ids[message.chat.id])
    except Exception as e:
        logging.error(f"Ошибка при получении данных пользователей: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /get_unique_users_data
def get_unique_users_data(message, bot, try_delete_message):
    try:
        if not is_allowed_user(message.from_user.id):
            bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")
            try_delete_message(bot, message.chat.id, message_ids[message.chat.id])
            return

        # Получение данных из таблицы unique_users
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT user_id, username, date_start, date_last, age, gender, evaluation, count_achievements FROM unique_users
                ''')
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]

        # Создание DataFrame из полученных данных
        df = pd.DataFrame(rows, columns=columns)

        # Путь для сохранения результата в формате XLSX
        output_file = 'unique_users_data.xlsx'

        # Сохранение данных в XLSX файл
        df.to_excel(output_file, index=False)

        # Отправка файла пользователю
        with open(output_file, 'rb') as file:
            bot.send_document(message.chat.id, file)

        logging.info(f"Данные успешно сохранены в {output_file} и отправлены пользователю {message.from_user.id}")
        
        # Сохраняем идентификатор сообщения с командой
        message_ids[message.chat.id] = message.message_id
        
        try_delete_message(bot, message.chat.id, message_ids[message.chat.id])
    except Exception as e:
        logging.error(f"Ошибка при получении данных уникальных пользователей: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")
