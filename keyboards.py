from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import KeyboardButton, InlineKeyboardButton


def main_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text="Отправить новость"))
    return keyboard.as_markup(resize_keyboard=True)

def admin_keyboard(news_id: int):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✅ Одобрить", callback_data=f"approve:{news_id}")
    keyboard.button(text="❌ Отклонить", callback_data=f"reject:{news_id}")
    keyboard.button(text="🚫 Заблокировать", callback_data=f"block:{news_id}")
    return keyboard.as_markup()
