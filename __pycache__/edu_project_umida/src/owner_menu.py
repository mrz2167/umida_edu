import re
from aiogram import types
from aiogram.dispatcher import Dispatcher
from db import get_all_courses, delete_course_and_lessons, get_course_by_id

async def owner_menu(message: types.Message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Добавить курс", callback_data="add_course"))
    kb.add(types.InlineKeyboardButton(text="Редактировать курс", callback_data="edit_course"))
    kb.add(types.InlineKeyboardButton(text="Удалить курс", callback_data="delete_course"))
    kb.add(types.InlineKeyboardButton(text="Просмотреть курсы", callback_data="view_courses"))
    
    await message.answer("Вы в меню владельца. Выберите действие:", reply_markup=kb)

@dp.callback_query(lambda c: c.data == "view_courses")
async def view_courses(callback: types.CallbackQuery):
    courses = get_all_courses()
    if not courses:
        await callback.message.answer("Нет доступных курсов.")
    else:
        for course in courses:
            await callback.message.answer(f"Курс: {course['title']} (ID: {course['id']})")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "delete_course")
async def delete_course(callback: types.CallbackQuery):
    courses = get_all_courses()
    if not courses:
        await callback.message.answer("Нет доступных курсов для удаления.")
        await callback.answer()
        return

    kb = types.InlineKeyboardMarkup()
    for course in courses:
        kb.add(types.InlineKeyboardButton(text=course['title'], callback_data=f"confirm_delete_{course['id']}"))
    
    kb.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_owner_menu"))
    await callback.message.answer("Выберите курс для удаления:", reply_markup=kb)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("confirm_delete_"))
async def confirm_delete_course(callback: types.CallbackQuery):
    course_id = int(callback.data.split("_")[-1])
    delete_course_and_lessons(course_id)
    await callback.message.answer("Курс успешно удалён.")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_owner_menu")
async def back_to_owner_menu(callback: types.CallbackQuery):
    await owner_menu(callback.message)