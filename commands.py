import logging

from telebot import types

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
def try_delete_message(bot, chat_id, message_type):
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
def start(message, bot, try_delete_message):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        keyboard = types.InlineKeyboardMarkup()
        bot.send_message(message.chat.id, 'Добро пожаловать в чай-бот принципов Agile!', reply_markup=keyboard)
        message_ids[message.chat.id] = {'command': message.message_id}
        try_delete_message(bot, message.chat.id, 'command')
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /start: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /new_tea
def new_tea(message, bot, try_delete_message):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        keyboard = create_keyboard()
        sent_message = bot.send_message(message.chat.id, 'Выберите номер:', reply_markup=keyboard)
        message_ids[message.chat.id] = {'command': message.message_id, 'keyboard': sent_message.message_id}
        try_delete_message(bot, message.chat.id, 'command')
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /new_tea: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик команды /help
def help(message, bot, try_delete_message):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        bot.send_message(message.chat.id, 'Этот бот помогает изучать принципы Agile. Используйте команду /new_tea для начала.')
        message_ids[message.chat.id] = {'command': message.message_id}
        try_delete_message(bot, message.chat.id, 'command')
    except Exception as e:
        logging.error(f"Ошибка в обработчике команды /help: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик нажатия на кнопку
def button(call, bot, get_content_by_id, add_user_data, try_delete_message):
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
        new_tea(call.message, bot, try_delete_message)
    except Exception as e:
        logging.error(f"Ошибка в обработчике нажатия на кнопку: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик неопознанных команд
def unknown_command(message, bot, try_delete_message):
    try:
        try_delete_message(bot, message.chat.id, 'keyboard')
        bot.send_message(message.chat.id, "Простите, такой команды нет. Используйте /help для получения справки.")
        message_ids[message.chat.id] = {'command': message.message_id}
        try_delete_message(bot, message.chat.id, 'command')
    except Exception as e:
        logging.error(f"Ошибка в обработчике неопознанной команды: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")
