import psycopg2
import telebot
from telebot import types
from datetime import datetime
import time
from dotenv import load_dotenv
import os
import logging
import requests

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение переменных окружения
DATABASE_URL = os.getenv('DATABASE_URL')
TOKEN = os.getenv('TOKEN')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID'))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Функция для создания таблицы unique_users и добавления данных
def setup_unique_users_table():
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Создание таблицы unique_users
                create_table_query = """
                CREATE TABLE unique_users (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT,
                    username VARCHAR(255),
                    count_select_tea INT,
                    date_start DATE,
                    date_last DATE,
                    age VARCHAR(255) DEFAULT 'default',
                    gender VARCHAR(255) DEFAULT 'default',
                    evaluation INT DEFAULT 0,
                    count_achievements INT DEFAULT 0
                );
                """
                cur.execute(create_table_query)

                # Заполнение таблицы unique_users данными из таблицы users
                insert_data_query = """
                INSERT INTO unique_users (user_id, username, count_select_tea, date_start, date_last)
                SELECT
                    u.user_id,
                    u.username,
                    COUNT(u.select_tea) AS count_select_tea,
                    MIN(u.date::DATE) AS date_start,
                    MAX(u.date::DATE) AS date_last
                FROM
                    users u
                GROUP BY
                    u.user_id, u.username;
                """
                cur.execute(insert_data_query)
                conn.commit()
    except Exception as e:
        logging.error(f"Ошибка при настройке таблицы unique_users: {e}")

# Функция для создания таблиц achievements и user_achievements
def setup_achievements_tables():
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Создание таблицы achievements
                create_achievements_table_query = """
                CREATE TABLE achievements (
                    achievement_id SERIAL PRIMARY KEY,
                    achievement_name VARCHAR(255) NOT NULL,
                    description TEXT
                );
                """
                cur.execute(create_achievements_table_query)

                # Создание таблицы user_achievements
                create_user_achievements_table_query = """
                CREATE TABLE user_achievements (
                    user_achievement_id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES unique_users(id),
                    achievement_id INT REFERENCES achievements(achievement_id),
                    date_achieved DATE
                );
                """
                cur.execute(create_user_achievements_table_query)

                # Заполнение таблицы achievements данными
                insert_achievements_data_query = """
                INSERT INTO achievements (achievement_name, description)
                VALUES
                    ('First Tea Selection', 'User made their first tea selection'),
                    ('Tea Enthusiast', 'User selected tea 10 times'),
                    ('Tea Master', 'User selected tea 100 times');
                """
                cur.execute(insert_achievements_data_query)
                conn.commit()
    except Exception as e:
        logging.error(f"Ошибка при настройке таблиц achievements и user_achievements: {e}")

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
            setup_unique_users_table()
            setup_achievements_tables()
            bot.send_message(message.chat.id, "Таблицы unique_users, achievements и user_achievements успешно созданы и заполнены данными.")
        else:
            bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")
    except Exception as e:
        logging.error(f"Ошибка при добавлении новых столбцов и данных: {e}")
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
