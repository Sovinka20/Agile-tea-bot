import logging

from telebot import types

from utils.helpers import logger

# Словарь для хранения идентификаторов сообщений с командами и клавиатурой
message_ids = {}

def try_delete_message(bot, chat_id, message_type):
    """
    Пытается удалить сообщение бота в указанном чате по типу сообщения.

    :param bot: Экземпляр бота.
    :param chat_id: ID чата, в котором находится сообщение.
    :param message_type: Тип сообщения (например, 'command').
    """
    if chat_id in message_ids and message_type in message_ids[chat_id]:
        message_id = message_ids[chat_id][message_type]
        try:
            bot.delete_message(chat_id=chat_id, message_id=message_id)
            del message_ids[chat_id][message_type]
            logger.info(f"Сообщение {message_id} типа '{message_type}' для чата {chat_id} успешно удалено.")
        except types.ApiException as e:
            if e.error_code == 400 and 'message to delete not found' in e.description:
                logger.warning(f"Сообщение уже удалено или не найдено: {e.error_code} - {e.description}")
                del message_ids[chat_id][message_type]
            else:
                logger.error(f"Ошибка удаления сообщения: {e.error_code} - {e.description}")
    else:
        logger.warning(f"Сообщение типа '{message_type}' для чата {chat_id} не найдено в словаре message_ids.")

def save_message_id(chat_id, message_type, message_id):
    """
    Сохраняет идентификатор сообщения в словаре message_ids.

    :param chat_id: ID чата, в котором находится сообщение.
    :param message_type: Тип сообщения (например, 'command').
    :param message_id: Идентификатор сообщения.
    """
    if chat_id not in message_ids:
        message_ids[chat_id] = {}
    message_ids[chat_id][message_type] = message_id
    logger.info(f"Сообщение {message_id} для чата {chat_id} сохранено в словаре с типом '{message_type}'.")
