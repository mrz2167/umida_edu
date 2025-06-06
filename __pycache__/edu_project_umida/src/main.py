import re
from config import BOT_TOKEN, OWNER_ID, ADMIN_IDS
from aiogram.filters import Command
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from db import check_user_role

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    role = check_user_role(message.from_user.id)
    if role == "owner":
        await show_owner_menu(message)
    else:
        await message.answer("Вы не имеете доступа к меню владельца.")

async def show_owner_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Управление курсами", callback_data="manage_courses")],
        [InlineKeyboardButton(text="Управление пользователями", callback_data="manage_users")],
        [InlineKeyboardButton(text="Выход", callback_data="exit_owner_menu")]
    ])
    await message.answer("Добро пожаловать в меню владельца!", reply_markup=kb)

@dp.callback_query(F.data == "manage_courses")
async def manage_courses(callback: CallbackQuery):
    await callback.message.answer("Здесь вы можете управлять курсами.")
    await callback.answer()

@dp.callback_query(F.data == "manage_users")
async def manage_users(callback: CallbackQuery):
    await callback.message.answer("Здесь вы можете управлять пользователями.")
    await callback.answer()

@dp.callback_query(F.data == "exit_owner_menu")
async def exit_owner_menu(callback: CallbackQuery):
    await callback.message.answer("Вы вышли из меню владельца.")
    await callback.answer()

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))