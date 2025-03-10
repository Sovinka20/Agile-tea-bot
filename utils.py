import logging
import os
import time
from datetime import datetime

import psycopg2
import requests
import telebot
from dotenv import load_dotenv
from telebot import types

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение переменных окружения
DATABASE_URL = os.getenv('DATABASE_URL')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID'))
MODER_USER_IDS = list(map(int, os.getenv('MODER_USER_IDS').split(',')))

def get_current_date():
    return datetime.now().strftime('%Y-%m-%d')

# Функция для проверки прав доступа
def is_allowed_user(user_id):
    logging.info(user_id in [ADMIN_USER_ID] + MODER_USER_IDS)
    return user_id in [ADMIN_USER_ID] + MODER_USER_IDS

# Функция для открытия соединения с базой данных
def open_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        logging.info("Успешное подключение к базе данных")
        return conn
    except Exception as e:
        logging.error(f"Ошибка подключения к базе данных: {e}")
        exit()
    finally:
        conn.close()

# Функция для закрытия соединения с базой данных
def close_connection(conn):
    if conn:
        conn.close()
        logging.info("Соединение с базой данных закрыто")


import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='app.log',
                    filemode='w')

# Примеры логирования
# logging.debug('Это сообщение отладки')
# logging.info('Это информационное сообщение')
# logging.warning('Это предупреждение')
# logging.error('Это сообщение об ошибке')
# logging.critical('Это критическое сообщение')
