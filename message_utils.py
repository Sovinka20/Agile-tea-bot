# message_utils.py

import logging

from telebot import types

# Словарь для хранения идентификаторов сообщений с командами и клавиатурой
message_ids = {}

def try_delete_message(bot, chat_id, message_type):
    if chat_id in message_ids and message_type in message_ids[chat_id]:
        message_id = message_ids[chat_id][message_type]
        try:
            bot.delete_message(chat_id=chat_id, message_id=message_id)
            del message_ids[chat_id][message_type]
        except types.ApiTelegramException as e:
            if e.error_code == 400 and 'message to delete not found' in e.description:
                logging.warning(f"Сообщение уже удалено или не найдено: {e.error_code} - {e.description} (chat_id: {chat_id}, message_type: {message_type}, message_id: {message_id})")
                del message_ids[chat_id][message_type]  # Удаляем запись из словаря, чтобы избежать повторных попыток удаления
            else:
                logging.error(f"Ошибка удаления сообщения: {e.error_code} - {e.description} (chat_id: {chat_id}, message_type: {message_type}, message_id: {message_id})")
    else:
        logging.warning(f"Сообщение типа '{message_type}' для чата {chat_id} не найдено в словаре message_ids.")

def save_message_id(chat_id, message_type, message_id):
    if chat_id not in message_ids:
        message_ids[chat_id] = {}
    message_ids[chat_id][message_type] = message_id
    logging.info(f"Сообщение {message_id} для чата {chat_id} сохранено в словаре с типом '{message_type}'.")
