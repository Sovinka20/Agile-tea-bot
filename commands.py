# commands.py

import logging

from telebot import types

from message_utils import save_message_id, try_delete_message


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
        bot.send_message(message.chat.id, 'Этот бот помогает изучать принципы Agile. Используйте команду /new_tea для начала.')
        save_message_id(message.chat.id, 'command', message.message_id)
        try_delete_message(bot, message.chat.id, 'command')
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /help: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик нажатия на кнопку
def button(call, bot, get_content_by_id, add_user_data, try_delete_message, save_message_id):
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

        try_delete_message(bot, call.message.chat.id, 'keyboard')
        try_delete_message(bot, call.message.chat.id, 'command')
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
            keyboard.add(types.InlineKeyboardButton("Начать", callback_data='start'))
            keyboard.add(types.InlineKeyboardButton("Новый чай", callback_data='new_tea'))
            keyboard.add(types.InlineKeyboardButton("Помощь", callback_data='help'))
            # Кнопки для администраторов и модераторов
            keyboard.add(types.InlineKeyboardButton("All users", callback_data='get_users_data'))
            keyboard.add(types.InlineKeyboardButton("Users", callback_data='get_unique_users_data'))
        else:
            # Кнопки для обычных пользователей
            keyboard.add(types.InlineKeyboardButton("Начать", callback_data='start'))
            keyboard.add(types.InlineKeyboardButton("Новый чай", callback_data='new_tea'))
            keyboard.add(types.InlineKeyboardButton("Помощь", callback_data='help'))

                # Добавляем кнопку "Отмена"
        keyboard.add(types.InlineKeyboardButton("Отмена", callback_data='cancel'))


        # Отправляем новое сообщение с клавиатурой
        sent_message = bot.send_message(message.chat.id, "Выберите команду:", reply_markup=keyboard)
        
        # Сохраняем ID нового сообщения
        save_message_id(message.chat.id, 'my_commands', sent_message.message_id)
        try_delete_message(bot, message.chat.id, 'command')


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
