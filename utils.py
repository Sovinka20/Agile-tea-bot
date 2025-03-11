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
# Список ID администраторов
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS').split(',')))
MODER_IDS = list(map(int, os.getenv('MODER_IDS').split(',')))

# Настройка логирования
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='app.log',
                    filemode='w')

logger = logging.getLogger(__name__)

# Примеры логирования
# logger.debug('Это сообщение отладки')
# logger.info('Это информационное сообщение')
# logger.warning('Это предупреждение')
# logger.error('Это сообщение об ошибке')
# logger.critical('Это критическое сообщение')



def get_current_date():
    """
    Возвращает текущую дату в формате 'ГГГГ-ММ-ДД'.

    :return: Строка с текущей датой.
    """
    return datetime.now().strftime('%Y-%m-%d')

# Функция для проверки прав доступа
def is_allowed_user(user_id):
    """
    Проверяет, имеет ли пользователь права администратора или модератора.

    :param user_id: ID пользователя.
    :return: True, если пользователь имеет права, иначе False.
    """


    logger.info(user_id in ADMIN_IDS + MODER_IDS)

    return user_id in ADMIN_IDS + MODER_IDS

# Функция для открытия соединения с базой данных
def open_connection():
    """
    Открывает соединение с базой данных PostgreSQL.

    :return: Объект соединения с базой данных.
    :raises: Исключение, если подключение не удалось.
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("Успешное подключение к базе данных")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        raise

def close_connection(conn):
    """
    Закрывает соединение с базой данных.

    :param conn: Объект соединения с базой данных.
    """
    if conn:
        conn.close()
        logger.info("Соединение с базой данных закрыто")

