# FILE: handlers/commands.py
# ROLE: Пользовательские команды
# DEPENDS: services/, utils/, keyboards.py
# COMMANDS:
#   /start (все) – приветствие и регистрация пользователя
#   /new_tea (все) – выбрать чай из списка (1–12)
#   /help (все) – показать справку
#   /my_achievements (все) – показать полученные достижения
#   /tea_random (все) – случайный чай с полной карточкой и кнопками
#   /my_commands (все) – главное меню команд
#   /edit_profile (все) – редактировать профиль (возраст, пол, любимый чай, оценка)
#   /create_age (все) – установить возраст
#   /create_gender (все) – установить пол
#   /create_favorite_tea (все) – установить любимый чай
#   /create_evaluation (все) – оценить бота (1–5 звёзд)
#   /my_profile (все) – показать профиль пользователя
import io
from telebot.types import InputFile
import logging
import os

import psycopg2
from telebot import types

from utils.message_utils import save_message_id, try_delete_message
from utils.helpers import (close_connection, get_current_date, is_allowed_user, logger,
                   open_connection)

# Получение переменных окружения
DATABASE_URL = os.getenv('DATABASE_URL')


# Функция для получения содержимого по id из таблицы bot_content
def get_content_by_id_commands(content_id):
    """
    Получает содержимое из таблицы bot_content по ID.

    :param content_id: ID содержимого.
    :return: Кортеж с данными (content, image, tea_name, quote_agile, question, link, id).
    """
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT content, image, tea_name, quote_agile, question, link, id FROM bot_content WHERE id = %s', (content_id,))
                result = cur.fetchone()
                return result if result else (None, None, None, None, None, None, None)
    except Exception as e:
        logger.error(f"Ошибка при выполнении SQL-запроса: {e}")
        return (None, None, None, None, None, None, None)
# Обработчик команды /my_achievements
def my_achievements(message, bot):
    """
    Отправляет пользователю его достижения с картинками и текстом из БД.
    GIF отображается как анимация через BytesIO с именем файла.
    """
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')

        user_id = message.from_user.id

        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT achievement_id FROM user_achievements WHERE user_id = %s
                ''', (user_id,))
                achievement_ids = [row[0] for row in cur.fetchall()]

                if not achievement_ids:
                    bot.send_message(user_id, "У вас пока нет достижений. Продолжайте выбирать чай!")
                    return

                for ach_id in achievement_ids:
                    cur.execute('''
                        SELECT description, image_achievements
                        FROM achievements
                        WHERE achievement_id = %s
                    ''', (ach_id,))
                    row = cur.fetchone()
                    if row:
                        desc, image_data = row
                        caption = f"{desc}" if desc else f"Достижение #{ach_id}"
                        if image_data:
                            # Ключевой момент: BytesIO + .name
                            gif_file = io.BytesIO(image_data)
                            gif_file.name = f'achievement_{ach_id}.gif'
                            bot.send_animation(user_id, gif_file, caption=caption)
                        else:
                            bot.send_message(user_id, caption)
                    else:
                        bot.send_message(user_id, f"Достижение #{ach_id} (не найдено в базе)")
    except Exception as e:
        logger.exception("Ошибка при отправке достижений")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")
def add_user_data(user_id, username, select_tea):
    """
    Добавляет данные пользователя в таблицу users.

    :param user_id: ID пользователя.
    :param username: Имя пользователя.
    :param select_tea: ID выбранного чая.
    """
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

# Функция для создания клавиатуры с кнопками
def create_keyboard():
    """
    Создает клавиатуру с кнопками для выбора чая.

    :return: Объект клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(1, 13)]
    for i in range(0, len(buttons), 3):
        keyboard.row(*buttons[i:i+3])
    return keyboard

# Обработчик команды /start

def start(message, bot):
    """
    Обработчик команды /start. Отправляет приветственное сообщение.

    :param message: Объект сообщения от пользователя.
    :param bot: Экземпляр бота.
    """
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        keyboard = types.InlineKeyboardMarkup()
        bot.send_message(message.chat.id, 'Добро пожаловать в чай-бот принципов Agile!', reply_markup=keyboard)
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
    except Exception as e:
        logger.error(f"Ошибка в обработчике команды /start: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /new_tea
def new_tea(message, bot):
    """
    Обработчик команды /new_tea. Отправляет клавиатуру для выбора чая.

    :param message: Объект сообщения от пользователя.
    :param bot: Экземпляр бота.
    """
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        keyboard = create_keyboard()
        sent_message = bot.send_message(message.chat.id, 'Выберите номер:', reply_markup=keyboard)
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
    except Exception as e:
        logger.error(f"Ошибка в обработчике команды /new_tea: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /help
def help(message, bot):
    """
    Обработчик команды /help. Отправляет справку по использованию бота.

    :param message: Объект сообщения от пользователя.
    :param bot: Экземпляр бота.
    """
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        bot.send_message(message.chat.id, 'Этот бот помогает изучать принципы Agile. Используйте команду /new_tea или /my_commands для начала.')
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
    except Exception as e:
        logger.error(f"Ошибка в обработчике команды /help: {e}")
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
        logger.error(f"Ошибка подключения к базе данных: {e}")
        exit()
    finally:
        conn.close()


# Обработчик нажатия на кнопку
def button(call, bot):
    """
    Обработчик нажатия на кнопку. Отправляет информацию о выбранном чае.

    :param call: Объект колбэка.
    :param bot: Экземпляр бота.
    """
    try:
        if call.data.isdigit():
            content_id = int(call.data)
            content_data = get_content_by_id_commands(content_id)
            if len(content_data) != 7:
                logger.error(f"Ожидалось 7 значений, получено {len(content_data)}")
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
                my_profile(call.message, bot)
            elif call.data.startswith('change_'):
                content_id = int(call.data.split('_')[1])
                content_data = get_content_by_id_commands(content_id)
                if len(content_data) != 7:
                    logger.error(f"Ожидалось 7 значений, получено {len(content_data)}")
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
        logger.error(f"Ошибка в обработчике нажатия на кнопку: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Функция для обработки команды /my_commands
def my_commands(message, bot):
    """
    Обработчик команды /my_commands. Отправляет клавиатуру с доступными командами.

    :param message: Объект сообщения от пользователя.
    :param bot: Экземпляр бота.
    """
    try:
        user_id = message.from_user.id
        keyboard = types.InlineKeyboardMarkup()
        try_delete_message(bot, message.chat.id, 'keyboard')
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')

        if is_allowed_user(user_id):
            keyboard.add(types.InlineKeyboardButton("Новый чай", callback_data='new_tea'))
            keyboard.add(types.InlineKeyboardButton("Случайный чай", callback_data='tea_random'))
            keyboard.add(types.InlineKeyboardButton("Статистика (All users)", callback_data='get_users_data'))
            keyboard.add(types.InlineKeyboardButton("Статистика (Users)", callback_data='get_unique_users_data'))
            keyboard.add(types.InlineKeyboardButton("Статистика (Ачивки)", callback_data='get_users_achievements_data'))
        else:
            keyboard.add(types.InlineKeyboardButton("Новый чай", callback_data='new_tea'))
            keyboard.add(types.InlineKeyboardButton("Случайный чай", callback_data='tea_random'))

        keyboard.add(types.InlineKeyboardButton("Отмена", callback_data='cancel'))

        sent_message = bot.send_message(message.chat.id, "Выберите команду:", reply_markup=keyboard)
        save_message_id(message.chat.id, 'command', sent_message.message_id)

    except Exception as e:
        logger.error(f"Ошибка в обработчике команды /my_commands: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик неопознанных команд
def unknown_command(message, bot):
    """
    Обработчик неопознанных команд. Отправляет сообщение о неизвестной команде.

    :param message: Объект сообщения от пользователя.
    :param bot: Экземпляр бота.
    """
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        bot.send_message(message.chat.id, "Простите, такой команды нет. Используйте /help для получения справки.")
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
    except Exception as e:
        logger.error(f"Ошибка в обработчике неопознанной команды: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /edit_profile
def edit_profile(message, bot):
    """
    Обработчик команды /edit_profile. Отправляет клавиатуру для редактирования профиля.

    :param message: Объект сообщения от пользователя.
    :param bot: Экземпляр бота.
    """
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
        logger.error(f"Ошибка в обработчике команды /edit_profile: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /create_age
def create_age(message, bot):
    """
    Обработчик команды /create_age. Отправляет клавиатуру для выбора возраста.

    :param message: Объект сообщения от пользователя.
    :param bot: Экземпляр бота.
    """
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
        logger.error(f"Ошибка в обработчике команды /create_age: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /create_gender
def create_gender(message, bot):
    """
    Обработчик команды /create_gender. Отправляет клавиатуру для выбора пола.

    :param message: Объект сообщения от пользователя.
    :param bot: Экземпляр бота.
    """
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
        logger.error(f"Ошибка в обработчике команды /create_gender: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /create_favorite_tea
def create_favorite_tea(message, bot):
    """
    Обработчик команды /create_favorite_tea. Отправляет клавиатуру для выбора любимого чая.

    :param message: Объект сообщения от пользователя.
    :param bot: Экземпляр бота.
    """
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
        keyboard = types.InlineKeyboardMarkup()
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id, tea_name FROM bot_content WHERE id != 0')
                teas = cur.fetchall()
                buttons = [types.InlineKeyboardButton(f"{tea[0]}.{tea[1]}", callback_data=f'tea_{tea[0]}') for tea in teas]
                buttons.append(types.InlineKeyboardButton("Отмена", callback_data='cancel'))
                for button in buttons:
                    keyboard.add(button)
        sent_message = bot.send_message(message.chat.id, "Выберите подходящий вариант", reply_markup=keyboard)
        save_message_id(message.chat.id, 'command', message.message_id)
    except Exception as e:
        logger.error(f"Ошибка в обработчике команды /create_favorite_tea: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /create_evaluation
def create_evaluation(message, bot):
    """
    Обработчик команды /create_evaluation. Отправляет клавиатуру для оценки бота.

    :param message: Объект сообщения от пользователя.
    :param bot: Экземпляр бота.
    """
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
        logger.error(f"Ошибка в обработчике команды /create_evaluation: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /my_profile
def my_profile(message, bot):
    """
    Обработчик команды /my_profile. Отправляет информацию о профиле пользователя.

    :param message: Объект сообщения от пользователя.
    :param bot: Экземпляр бота.
    """
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
                    cur.execute('SELECT tea_name FROM bot_content WHERE id = %s', (favorite_tea,))
                    favorite_tea_name = cur.fetchone()[0] if favorite_tea else "не указан"
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
        logger.error(f"Ошибка в обработчике команды /my_profile: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")
# Обработчик команды /tea_random
def tea_random(message, bot):
    """
    Обработчик команды /tea_random. Отправляет случайный чай.

    :param message: Объект сообщения от пользователя.
    :param bot: Экземпляр бота.
    """
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        save_message_id(abs(message.chat.id), 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id FROM bot_content ORDER BY RANDOM() LIMIT 1')
                content_id = cur.fetchone()[0]
                content, image, tea_name, quote_agile, question, link, id = get_content_by_id_commands(content_id)
                
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
                        bot.send_photo(message.chat.id, image, caption=formatted_content, parse_mode='HTML', reply_markup=keyboard)
                    else:
                        bot.send_message(message.chat.id, formatted_content, parse_mode='HTML', reply_markup=keyboard)
                    # Сохранение записи в таблицу users
                    add_user_data(message.from_user.id, message.from_user.username, content_id)
                else:
                    bot.send_message(message.chat.id, "Содержимое не найдено.")
    except Exception as e:
        logger.error(f"Ошибка в обработчике команды /tea_random: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")
