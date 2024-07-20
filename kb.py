from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

menu = [
    [InlineKeyboardButton(text="🏆 Последние матчи 🏆", callback_data="lastm"),
    InlineKeyboardButton(text="🏃‍♂️ Список игроков 🏃‍♂️", callback_data="players")],
    [InlineKeyboardButton(text="💵 Результаты команды 💵", callback_data="results")]
]
menu = InlineKeyboardMarkup(inline_keyboard=menu)
