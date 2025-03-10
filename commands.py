import logging
import os

import psycopg2
from telebot import types

from message_utils import save_message_id, try_delete_message
from utils import (close_connection, get_current_date, is_allowed_user,
                   open_connection)

# Получение переменных окружения
DATABASE_URL = os.getenv('DATABASE_URL')

# Функция для получения содержимого по id из таблицы bot_content
def get_content_by_id_commands(content_id):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute('SELECT content, image, tea_name, quote_agile, question, link, id FROM bot_content WHERE id = %s', (content_id,))
            result = cur.fetchone()
        # close_connection(conn)
            return result if result else (None, None)
    except Exception as e:
        logging.error(f"Ошибка при выполнении SQL-запроса: {e}")
        return (None, None)
    finally:
        conn.close()

# Обработчик команды /my_achievements
def my_achievements(message, bot):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')

        user_id = message.from_user.id

        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Получаем количество выборов чая пользователем
                cur.execute('SELECT COUNT(*) FROM users WHERE user_id = %s', (user_id,))
                count = cur.fetchone()[0]

                # Получаем достижения, которые соответствуют текущему количеству выборов
                cur.execute('''
                    SELECT "achievement_name", "description", "image_achievements" 
                    FROM achievements 
                    WHERE condition <= %s
                ''', (count,))
                achievements = cur.fetchall()

                if achievements:
                    for achievement in achievements:
                        achievement_name, description, image_achievements = achievement
                        bot.send_message(user_id, f"Поздравляем! Ваше новое достижение - {achievement_name}!\n{description}")

                        if image_achievements:
                            # Отправляем изображение, если оно есть
                            bot.send_photo(user_id, image_achievements)
                else:
                    bot.send_message(user_id, "У вас пока нет достижений.")

    except Exception as e:
        logging.exception("Ошибка при получении достижений")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")


# Функция для добавления данных в таблицу users
def add_user_data(user_id, username, select_tea):
    date = get_current_date()
    try:
        conn = psycopg2.connect(DATABASE_URL)
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

# Функция для создания клавиатуры с кнопками
def create_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(1, 13)]
    for i in range(0, len(buttons), 3):
        keyboard.row(*buttons[i:i+3])
    return keyboard

# Обработчик команды /start
def start(message, bot):
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
def new_tea(message, bot):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        keyboard = create_keyboard()
        sent_message = bot.send_message(message.chat.id, 'Выберите номер:', reply_markup=keyboard)
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /new_tea: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /help
def help(message, bot):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        bot.send_message(message.chat.id, 'Этот бот помогает изучать принципы Agile. Используйте команду /new_tea или /my_commands для начала.')
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /help: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")


# Общая функция для добавления достижений
def add_select_all_data_tea(user_id, select_id):
    try:
        conn = psycopg2.connect(DATABASE_URL)

        date = get_current_date()
        with conn.cursor() as cur:
            cur.execute('''
            INSERT INTO users_all_data_card_tea (user_id, select_id, date_achieved)
            VALUES (%s, %s, %s)
        ''', (user_id, select_id, date))
    except Exception as e:
        logging.error(f"Ошибка подключения к базе данных: {e}")
        exit()
    finally:
        conn.close()


# Обработчик нажатия на кнопку
def button(call, bot):
    try:
        if call.data.isdigit():
            content_id = int(call.data)
            content_data = get_content_by_id_commands(content_id)
            if len(content_data) != 7:
                logging.error(f"Ожидалось 7 значений, получено {len(content_data)}")
                bot.send_message(call.message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")
                return
            content, image, tea_name, quote_agile, question, link, id = content_data
            if content:
                formatted_content = f"""
<i>"{content}"</i>
"""
                # Создаем клавиатуру с кнопками
                keyboard = types.InlineKeyboardMarkup()
                
                # Кнопка для изменения formatted_content
                change_button = types.InlineKeyboardButton(text=question, callback_data=f"change_{content_id}")
                keyboard.add(change_button)
                
                # Кнопка для открытия URL
                url_button = types.InlineKeyboardButton(text="Cсылка :)", url=link)
                keyboard.add(url_button)
                
                if image:
                    # Отправляем сообщение с картинкой, текстом и клавиатурой
                    message = bot.send_photo(call.message.chat.id, image, caption=formatted_content, parse_mode='HTML', reply_markup=keyboard)
                else:
                    # Отправляем сообщение с текстом и клавиатурой
                    message = bot.send_message(call.message.chat.id, formatted_content, parse_mode='HTML', reply_markup=keyboard)
                
                add_user_data(call.from_user.id, call.from_user.username, content_id)
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Содержимое не найдено.")
        else:
            if call.data == 'my_profile':
                my_profile(call.message, bot, try_delete_message, save_message_id)
            elif call.data.startswith('change_'):
                # Обработка нажатия на кнопку "change_"
                content_id = int(call.data.split('_')[1])
                content_data = get_content_by_id_commands(content_id)
                if len(content_data) != 7:
                    logging.error(f"Ожидалось 7 значений, получено {len(content_data)}")
                    bot.send_message(call.message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")
                    return
                content, image, tea_name, quote_agile, question, link, id = content_data
                if content:
                    new_formatted_content = f"""
<b>{id}.{tea_name}</b>

<i>"{content}"</i>

{quote_agile}
"""
                    # Удаляем предыдущее сообщение
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                    
                    # Создаем новую клавиатуру с одной кнопкой
                    keyboard = types.InlineKeyboardMarkup()
                                     
                    # Кнопка для открытия URL
                    url_button = types.InlineKeyboardButton(text="Cсылка :)", url=link)
                    keyboard.add(url_button)

                    if image:
                        # Отправляем новое сообщение с картинкой, текстом и новой клавиатурой
                        bot.send_photo(call.message.chat.id, image, caption=new_formatted_content, parse_mode='HTML', reply_markup=keyboard)
                    else:
                        # Отправляем новое сообщение с текстом и новой клавиатурой
                        bot.send_message(call.message.chat.id, new_formatted_content, parse_mode='HTML', reply_markup=keyboard)
                    add_select_all_data_tea(call.from_user.id, id)

                else:
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Содержимое не найдено.")
            else:
                bot.send_message(call.message.chat.id, "Неизвестная команда.")
    except Exception as e:
        logging.error(f"Ошибка в обработчике нажатия на кнопку: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")   

# Функция для обработки команды /my_commands
def my_commands(message, bot):
    try:
        user_id = message.from_user.id
        keyboard = types.InlineKeyboardMarkup()
        try_delete_message(bot, message.chat.id, 'keyboard')
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')

        if is_allowed_user(user_id):
            # keyboard.add(types.InlineKeyboardButton("Профиль", callback_data='my_profile'))
            keyboard.add(types.InlineKeyboardButton("Новый чай", callback_data='new_tea'))
            keyboard.add(types.InlineKeyboardButton("Случайный чай", callback_data='tea_random'))
            # keyboard.add(types.InlineKeyboardButton("Помощь", callback_data='help'))
            keyboard.add(types.InlineKeyboardButton("Статистика (All users)", callback_data='get_users_data'))
            keyboard.add(types.InlineKeyboardButton("Статистика (Users)", callback_data='get_unique_users_data'))
            keyboard.add(types.InlineKeyboardButton("Статистика (Ачивки)", callback_data='get_users_achievements_data'))
            
        else:
            # keyboard.add(types.InlineKeyboardButton("Профиль", callback_data='my_profile'))
            keyboard.add(types.InlineKeyboardButton("Новый чай", callback_data='new_tea'))
            keyboard.add(types.InlineKeyboardButton("Случайный чай", callback_data='tea_random'))
            # keyboard.add(types.InlineKeyboardButton("Помощь", callback_data='help'))

        keyboard.add(types.InlineKeyboardButton("Отмена", callback_data='cancel'))

        sent_message = bot.send_message(message.chat.id, "Выберите команду:", reply_markup=keyboard)
        save_message_id(message.chat.id, 'command', sent_message.message_id)

    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /my_commands: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик неопознанных команд
def unknown_command(message, bot):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        bot.send_message(message.chat.id, "Простите, такой команды нет. Используйте /help для получения справки.")
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
    except Exception as e:
        logging.error(f"Ошибка в обработчике неопознанной команды: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /edit_profile
def edit_profile(message, bot):
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
def create_age(message, bot):
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
def create_gender(message, bot):
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
def create_favorite_tea(message, bot):
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
                # close_connection(conn)
                buttons = [types.InlineKeyboardButton(f"{tea[0]}.{tea[1]}", callback_data=f'tea_{tea[0]}') for tea in teas]
                buttons.append(types.InlineKeyboardButton("Отмена", callback_data='cancel'))
                for button in buttons:
                    keyboard.add(button)
        sent_message = bot.send_message(message.chat.id, "Выберите подходящий вариант", reply_markup=keyboard)
        save_message_id(message.chat.id, 'command', message.message_id)
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /create_favorite_tea: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")
    finally:
        conn.close()

# Обработчик команды /create_evaluation
def create_evaluation(message, bot):
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
def my_profile(message, bot):
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
                if user_data:
                    age, gender, favorite_tea, evaluation, count_achievements = user_data
                    with conn.cursor() as cur:
                        cur.execute('''
                            SELECT tea_name FROM bot_content WHERE id = %s
                        ''', (favorite_tea,))
                        favorite_tea_name = cur.fetchone()[0] if favorite_tea else "не указан"
                        # close_connection(conn)
                    profile_text = f"Ваш возраст - {age}\nВаш пол - {gender}\nВаш любимый чай - {favorite_tea_name}\nВаша оценка чай-бота - {'⭐️' * evaluation}\nВаши достижения - {count_achievements}"
                    keyboard = types.InlineKeyboardMarkup()
                    buttons = [
                        types.InlineKeyboardButton("Изменить данные о себе", callback_data='edit_profile'),
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
    finally:
        conn.close()



# Обработчик команды /tea_random
def tea_random(message, bot):
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
                content, image, tea_name, quote_agile, question, link, id = get_content_by_id_commands(content_id)
                
                if content:
                    formatted_content = f"""
<i>"{content}"</i>

"""
                    if image:
                        bot.send_photo(message.chat.id, image, caption=formatted_content, parse_mode='HTML')
                    else:
                        bot.send_message(message.chat.id, formatted_content, parse_mode='HTML')
                    # Сохранение записи в таблицу users
                    add_user_data(message.from_user.id, message.from_user.username, content_id)
                    # close_connection(conn)
                else:
                    bot.send_message(message.chat.id, "Содержимое не найдено.")
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /tea_random: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")
    finally:
        conn.close()
