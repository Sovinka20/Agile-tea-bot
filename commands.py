import logging
import os

import psycopg2
from telebot import types

from message_utils import save_message_id, try_delete_message
from utils import get_current_date

# Получение переменных окружения
DATABASE_URL = os.getenv('DATABASE_URL')

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
        with conn.cursor() as cur:
            cur.execute('SELECT content, image, tea_name, quote_agile, question, id FROM bot_content WHERE id = %s', (content_id,))
            result = cur.fetchone()
            return result if result else (None, None)
    except Exception as e:
        logging.error(f"Ошибка при выполнении SQL-запроса: {e}")
        return (None, None)


# Обработчик команды /my_achievements
def my_achievements(message, bot, try_delete_message, save_message_id):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')

        TEST_USER_ID = message.from_user.id

        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # add_achievement(cur, TEST_USER_ID, 1)
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
                    # add_achievement(cur, TEST_USER_ID, 2)
                    bot.send_message(TEST_USER_ID, "Поздравляем! Ваше новое достижение - Чайный лист! Вы выбрали чаи 12 раз!")
                    tea_leaf_file_path = os.path.join('tea_leaf.gif')
                    if os.path.exists(tea_leaf_file_path):
                        with open(tea_leaf_file_path, 'rb') as file:
                            bot.send_document(TEST_USER_ID, file)
                    else:
                        logging.error(f"Файл '{tea_leaf_file_path}' не найден.")

                if count >= 20:
                    # add_achievement(cur, TEST_USER_ID, 2)
                    bot.send_message(TEST_USER_ID, "Поздравляем! Ваше новое достижение - Чайный пакетик! Вы выбрали чай 20 раз!")
                    tea_leaf_file_path = os.path.join('tea bag.gif')
                    if os.path.exists(tea_leaf_file_path):
                        with open(tea_leaf_file_path, 'rb') as file:
                            bot.send_document(TEST_USER_ID, file)
                    else:
                        logging.error(f"Файл '{tea_leaf_file_path}' не найден.")

        # save_message_id(message.chat.id, 'command', message.message_id)
        # try_delete_message(bot, message.chat.id, 'command')

    except Exception as e:
        logging.exception("Ошибка при добавлении новых столбцов и данных")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")


# Функция для добавления данных в таблицу users
def add_user_data(user_id, username, select_tea):
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

# Функция для создания клавиатуры с кнопками
def create_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(1, 13)]
    for i in range(0, len(buttons), 3):
        keyboard.row(*buttons[i:i+3])
    return keyboard

# Обработчик команды /start
def start(message, bot, try_delete_message, save_message_id):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        keyboard = types.InlineKeyboardMarkup()
        bot.send_message(message.chat.id, 'Добро пожаловать в чай-бот принципов Agile!', reply_markup=keyboard)
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /start: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /new_tea
def new_tea(message, bot, try_delete_message, save_message_id):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        keyboard = create_keyboard()
        sent_message = bot.send_message(message.chat.id, 'Выберите номер:', reply_markup=keyboard)
        save_message_id(message.chat.id, 'command', message.message_id)
        save_message_id(message.chat.id, 'keyboard', sent_message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /new_tea: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /help
def help(message, bot, try_delete_message, save_message_id):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        bot.send_message(message.chat.id, 'Этот бот помогает изучать принципы Agile. Используйте команду /new_tea или /my_commands для начала.')
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /help: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик нажатия на кнопку
def button(call, bot, get_content_by_id, add_user_data, try_delete_message, save_message_id):
    try:
        if call.data.isdigit():
            content_id = int(call.data)
            content, image, tea_name, quote_agile, question, id = get_content_by_id(content_id)
                
            if content:
                formatted_content = f"""
<b>{id}.{tea_name}</b>

<i>"{content}"</i>

{quote_agile}
"""
                if image:
                    bot.send_photo(call.message.chat.id, image, caption=formatted_content, parse_mode='HTML')
                else:
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=formatted_content, parse_mode='HTML')
                add_user_data(call.from_user.id, call.from_user.username, content_id)
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Содержимое не найдено.")

            try_delete_message(bot, call.message.chat.id, 'keyboard')
            try_delete_message(bot, call.message.chat.id, 'command')
        else:
            if call.data == 'my_profile':
                my_profile(call.message, bot, try_delete_message, save_message_id)
            else:
                bot.send_message(call.message.chat.id, "Неизвестная команда.")
    except Exception as e:
        logging.error(f"Ошибка в обработчике нажатия на кнопку: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Функция для обработки команды /my_commands
def my_commands(message, bot, try_delete_message, save_message_id, is_allowed_user):
    try:
        user_id = message.from_user.id
        keyboard = types.InlineKeyboardMarkup()
        # Удаляем предыдущую команду
        try_delete_message(bot, message.chat.id, 'keyboard')
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')

        if is_allowed_user(user_id):
            # Кнопки для обычных пользователей
            keyboard.add(types.InlineKeyboardButton("Профиль", callback_data='my_profile'))
            keyboard.add(types.InlineKeyboardButton("Новый чай", callback_data='new_tea'))
            keyboard.add(types.InlineKeyboardButton("Случайный чай", callback_data='tea_random'))
            keyboard.add(types.InlineKeyboardButton("Помощь", callback_data='help'))
            # Кнопки для администраторов и модераторов
            keyboard.add(types.InlineKeyboardButton("Статистика (All users)", callback_data='get_users_data'))
            keyboard.add(types.InlineKeyboardButton("Статистика (Users)", callback_data='get_unique_users_data'))
        else:
            # Кнопки для обычных пользователей
            keyboard.add(types.InlineKeyboardButton("Профиль", callback_data='my_profile'))
            keyboard.add(types.InlineKeyboardButton("Новый чай", callback_data='new_tea'))
            keyboard.add(types.InlineKeyboardButton("Случайный чай", callback_data='tea_random'))
            keyboard.add(types.InlineKeyboardButton("Помощь", callback_data='help'))

        # Добавляем кнопку "Отмена"
        keyboard.add(types.InlineKeyboardButton("Отмена", callback_data='cancel'))

        # Отправляем новое сообщение с клавиатурой
        sent_message = bot.send_message(message.chat.id, "Выберите команду:", reply_markup=keyboard)
        
        # Сохраняем ID нового сообщения
        save_message_id(message.chat.id, 'command', sent_message.message_id)
        # try_delete_message(bot, message.chat.id, 'command')

    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /my_commands: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик неопознанных команд
def unknown_command(message, bot, try_delete_message, save_message_id):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        bot.send_message(message.chat.id, "Простите, такой команды нет. Используйте /help для получения справки.")
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
    except Exception as e:
        logging.error(f"Ошибка в обработчике неопознанной команды: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")



# Обработчик команды /edit_profile
def edit_profile(message, bot, try_delete_message, save_message_id):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
        keyboard = types.InlineKeyboardMarkup()
        buttons = [
            types.InlineKeyboardButton("Возраст", callback_data='create_age'),
            types.InlineKeyboardButton("Пол", callback_data='create_gender'),
            types.InlineKeyboardButton("Любимый чай", callback_data='create_favorite_tea'),
            types.InlineKeyboardButton("Оценку чай-бота", callback_data='create_evaluation'),
            types.InlineKeyboardButton("Отмена", callback_data='cancel')
        ]
        for button in buttons:
            keyboard.add(button)
        sent_message = bot.send_message(message.chat.id, "Выберите, какие данные хотите изменить", reply_markup=keyboard)
        save_message_id(message.chat.id, 'command', message.message_id)
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /create_age: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")


# Обработчик команды /create_age
def create_age(call, message, bot, try_delete_message, save_message_id):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
        keyboard = types.InlineKeyboardMarkup()
        buttons = [
            types.InlineKeyboardButton("до 14", callback_data='age_14'),
            types.InlineKeyboardButton("от 15 до 21", callback_data='age_15_21'),
            types.InlineKeyboardButton("от 22 до 45", callback_data='age_22_45'),
            types.InlineKeyboardButton("45+", callback_data='age_45+'),
            types.InlineKeyboardButton("Отмена", callback_data='cancel')
        ]
        for button in buttons:
            keyboard.add(button)
        sent_message = bot.send_message(message.chat.id, "Сколько вам лет?", reply_markup=keyboard)
        save_message_id(message.chat.id, 'command', message.message_id)
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /create_age: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /create_gender
def create_gender(call, message, bot, try_delete_message, save_message_id):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
        keyboard = types.InlineKeyboardMarkup()
        buttons = [
            types.InlineKeyboardButton("муж.", callback_data='gender_male'),
            types.InlineKeyboardButton("жен.", callback_data='gender_female'),
            types.InlineKeyboardButton("Отмена", callback_data='cancel')
        ]
        for button in buttons:
            keyboard.add(button)
        sent_message = bot.send_message(message.chat.id, "Выберите подходящий вариант", reply_markup=keyboard)
        save_message_id(message.chat.id, 'command', message.message_id)
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /create_gender: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /create_favorite_tea
def create_favorite_tea(call, message, bot, try_delete_message, save_message_id):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
        keyboard = types.InlineKeyboardMarkup()
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT id, tea_name FROM bot_content WHERE id != 0
                ''')
                teas = cur.fetchall()
                logging.error(f"Значение: {teas}")
                buttons = [types.InlineKeyboardButton(f"{tea[0]}.{tea[1]}", callback_data=f'tea_{tea[0]}') for tea in teas]
                buttons.append(types.InlineKeyboardButton("Отмена", callback_data='cancel'))
                for button in buttons:
                    keyboard.add(button)
        sent_message = bot.send_message(message.chat.id, "Выберите подходящий вариант", reply_markup=keyboard)
        save_message_id(message.chat.id, 'command', message.message_id)
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /create_favorite_tea: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /create_evaluation
def create_evaluation(call, message, bot, try_delete_message, save_message_id):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
        keyboard = types.InlineKeyboardMarkup()
        buttons = [
            types.InlineKeyboardButton("⭐️", callback_data='eval_1'),
            types.InlineKeyboardButton("⭐️⭐️", callback_data='eval_2'),
            types.InlineKeyboardButton("⭐️⭐️⭐️", callback_data='eval_3'),
            types.InlineKeyboardButton("⭐️⭐️⭐️⭐️", callback_data='eval_4'),
            types.InlineKeyboardButton("⭐️⭐️⭐️⭐️⭐️", callback_data='eval_5'),
            types.InlineKeyboardButton("Отмена", callback_data='cancel')
        ]
        for button in buttons:
            keyboard.add(button)
        sent_message = bot.send_message(message.chat.id, "Оцените нашего цай-бота :)", reply_markup=keyboard)
        save_message_id(message.chat.id, 'command', message.message_id)
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /create_evaluation: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /my_profile
def my_profile(message, bot, try_delete_message, save_message_id):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT age, gender, favorite_tea, evaluation, count_achievements
                    FROM unique_users WHERE user_id = %s
                ''', (message.from_user.id,))
                user_data = cur.fetchone()
                logging.error(f"Данные: {user_data, message.from_user.id}")

                if user_data:
                    age, gender, favorite_tea, evaluation, count_achievements = user_data
                    with conn.cursor() as cur:
                        cur.execute('''
                            SELECT tea_name FROM bot_content WHERE id = %s
                        ''', (favorite_tea,))
                        favorite_tea_name = cur.fetchone()[0] if favorite_tea else "не указан"
                    profile_text = f"Ваш возраст - {age}\nВаш пол - {gender}\nВаш любимый чай - {favorite_tea_name}\nВаша оценка чай-бота - {'⭐️' * evaluation}\nВаши достижения - {count_achievements}"
                    keyboard = types.InlineKeyboardMarkup()
                    buttons = [
                        types.InlineKeyboardButton("Изменить данные о себе", callback_data='edit_profile'),
                        # types.InlineKeyboardButton("Назад", callback_data='back'),
                        types.InlineKeyboardButton("Отмена", callback_data='cancel')
                    ]
                    for button in buttons:
                        keyboard.add(button)
                    sent_message = bot.send_message(message.chat.id, profile_text, reply_markup=keyboard)
                    save_message_id(message.chat.id, 'command', message.message_id)
                else:
                    bot.send_message(message.chat.id, "Профиль не найден.")
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /my_profile: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")



# Обработчик команды /tea_random
def tea_random(message, bot, try_delete_message, save_message_id):
    logging.error(f"Проверка: {message}")
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        save_message_id(abs(message.chat.id), 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT id FROM bot_content ORDER BY RANDOM() LIMIT 1
                ''')
                content_id = cur.fetchone()[0]
                content, image, tea_name, quote_agile, question, id = get_content_by_id(content_id)
                
                if content:
                    formatted_content = f"""
<b>{id}.{tea_name}</b>

<i>"{content}"</i>

{quote_agile}
"""
                    if image:
                        bot.send_photo(message.chat.id, image, caption=formatted_content, parse_mode='HTML')
                    else:
                        bot.send_message(message.chat.id, formatted_content, parse_mode='HTML')
                    # save_message_id(message.chat.id, 'command', message.message_id)
                    # try_delete_message(bot, message.chat.id, 'command')

                    # Сохранение записи в таблицу users
                    add_user_data(message.from_user.id, message.from_user.username, content_id)
                else:
                    bot.send_message(message.chat.id, "Содержимое не найдено.")
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /tea_random: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")
