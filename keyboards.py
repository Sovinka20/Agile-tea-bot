# FILE: keyboards.py
# ROLE: Фабрика inline-клавиатур
# DEPENDS: telebot
# COMMANDS: (нет)
from telebot import types

def create_tea_keyboard():
    """Клавиатура для выбора чая (1–12)."""
    keyboard = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(1, 13)]
    for i in range(0, len(buttons), 3):
        keyboard.row(*buttons[i:i+3])
    return keyboard
