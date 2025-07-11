import re
import asyncio
import logging
from asyncio import sleep
from datetime import datetime

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatAction, ParseMode
from aiogram.types.input_file import FSInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.filters import Command, or_f, StateFilter
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
    BotCommand, BotCommandScopeDefault)

from db import (
    check_user_role, add_user_role, add_course, add_lesson, update_homework_status,
    update_course_title, update_course_description, get_all_courses, get_next_lesson,
    update_lesson_title, update_lesson_video, delete_course_and_lessons, notify_admin_about_homework,
    update_lesson_homework, update_lesson_extra_material_file, get_user_by_id, get_next_course_for_user,
    update_lesson_extra_material_link, delete_lesson_by_id, UserLesson, Lesson, get_course_by_lesson,
    get_lessons_by_course, get_course_by_id, approve_course_by_id, save_homework, save_user_topic_id,
    update_course_lesson_count, initialize_user_lessons, get_available_courses_for_user, get_user_by_topic_id,
    get_first_lesson, create_or_update_user_lesson, submit_homework, approve_homework, get_user_topic_id,
    send_homework_for_redo, get_lesson_workbook, get_lesson_extra_materials, get_user_lesson_in_progress,
    check_homework, SessionLocal, get_first_course, get_lesson_by_id, update_user_lesson_status,
    save_recommendation_letter, User, )

from config import (
    BOT_TOKEN, OWNER_ID, ADMIN_IDS, ADMIN_ESTER,
    ADMINISTRATION, ALL_ADMINS, ADMIN_GROUP_ID)

from welcome_message import welcome_parts
from utils import ensure_topic, generate_topics_for_old_users

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
pending_requests = {}
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)
dev_id = 6774411424


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_activity.log"),
        # logging.StreamHandler()  # ← вывод в терминал
    ]
)
logging.info("🔁 Logger initialized")

class MessageLoggerMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        if isinstance(event, Message):
            from_user = event.from_user.id
            if event.text:
                logging.info(f"[IN] From {from_user} | Text: {event.text}")
            elif event.photo:
                logging.info(f"[IN] From {from_user} | Photo received")
            elif event.document:
                logging.info(f"[IN] From {from_user} | Document: {event.document.file_name}")
        return await handler(event, data)


@dp.message(Command("logs"))
async def send_logs(message: Message):
    if message.from_user.id == 6774411424:
        await message.answer_document(FSInputFile("bot_activity.log"))
    else:
        await message.answer("⛔ Рухсат йўқ.")


print(f'Bot started ')
@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    role = check_user_role(message.from_user.id)
    if role == "owner":
        await message.answer( f"Вы уже авторизованы. Ваша роль: {role}",
        )
    elif role == "admin":
        await message.answer(f"Вы уже авторизованы. Ваша роль: {role}")
    elif role == "user":
        await message.answer(f"Сиз аллақачон рўйхатдан ўтгансиз. Сиз катнашувчисиз")
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Ruxsat so'rash", callback_data="request_access")]
        ])
        await message.answer(
            f"Салом, {message.from_user.full_name}! Илтимос, маъмуриятдан рухсат сўранг.",
            reply_markup=kb
        )
    # await bot.delete_my_commands(scope=BotCommandScopeDefault())

@dp.message(Command("get_topic_id"))
async def get_topic_id(message: Message):
    if message.is_topic_message:
        await message.answer(f"📌 Топик ID: <code>{message.message_thread_id}</code>", parse_mode="HTML")
    else:
        await message.answer("❗ Бу буйруқни топик ичида юборинг.")

user_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/feedback")],
    ],
    resize_keyboard=True
)

@dp.message(Command("menu"))
async def show_menu(message: Message):
    user_id = message.from_user.id
    if user_id in tuple(ADMINISTRATION.values()):
        text = (
            "<b>Меню владельца:</b>\n"
            "/add_course — добавить курс\n"
            "/edit_course — редактировать курс\n"
            "/delete_course — удалить курс\n"
            "/add_lesson — добавить урок\n"
            "/delete_lesson — удалить урок\n"
            "/courses — просмотр курсов\n"
            "/sync_lessons — синхронизировать количество уроков\n"
            "/menu — показать это меню\n"
        )
        await message.answer(text)
    else:
        role = check_user_role(user_id)
        if role == "user":
            text = (
                "<b>Фойдаланувчи менюси::</b>\n"
                "/feedback — маъмуриятга совол юбориш\n"
                "/menu — менюни кўрсатиш\n"
            )
            await message.answer(text, reply_markup=ReplyKeyboardRemove())
        else:
            await message.answer("Сизда рухсат йўқ. Илтимос, рухсатни маъмуриятдан сўранг.")


async def on_startup(dispatcher):
    await sync_lessons_auto()
async def sync_lessons_auto():
    courses = get_all_courses()
    for course in courses:
        actual_count = len(get_lessons_by_course(course["id"]))
        if course["lesson_count"] != actual_count:
            update_course_lesson_count(course["id"], actual_count)

async def send_welcome_message(bot: Bot, user_id: int):
    for part in welcome_parts:
        await bot.send_chat_action(user_id, ChatAction.TYPING)
        await asyncio.sleep(1.5)
        await bot.send_message(user_id, part)
        await asyncio.sleep(3)

class AccessRequest(StatesGroup):
    waiting_for_name = State()
@dp.callback_query(F.data == "request_access")
async def handle_request_access(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Илтимос, рухсат сўраш учун тўлиқ исмингизни киритинг:")
    await state.set_state(AccessRequest.waiting_for_name)
    await callback.answer()
@dp.message(AccessRequest.waiting_for_name)

@dp.message(AccessRequest.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    fio = message.text.strip()
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name

    add_user_role(user_id, fio, username, "none")
    await state.update_data(fio=fio, username=username)

    # 🔹 Создаём топик для этого юзера
    topic_id = get_user_topic_id(user_id)
    if not topic_id:
        topic_id = await ensure_topic(bot, user_id, fio, username)
        save_user_topic_id(user_id, topic_id)

    kb_2 = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сделать участником", callback_data=f"make_user_{user_id}")],
        [InlineKeyboardButton(text="Отклонить", callback_data=f"decline_{user_id}")],
        [InlineKeyboardButton(text="📜 Запросить тавсиянома", callback_data=f"request_letter_{user_id}")]
    ])
    
    await bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        message_thread_id=topic_id,
        text=f"🔔 Запрос на доступ от {fio} (@{username})\nID: <code>{user_id}</code>",
        reply_markup=kb_2,
        parse_mode="HTML"
    )

    await message.answer("✅ Сизнинг сўровингиз маъмуриятга юборилди, тасдиқни кутинг.")
    await state.clear()

class RecommendationLetter(StatesGroup):
    waiting_for_text = State()
    waiting_for_photo = State()

@dp.callback_query(F.data.startswith("request_letter_"))
async def request_letter(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[2])
    await state.update_data(letter_user_id=user_id)

    await bot.send_message(
        chat_id=user_id,
        text=(
            "Худонинг тинчлиги бўлсин.\n"
            "Онлайн академияда ўқишингиз учун, чўпонингизга тавсиянома ёздириб, бизга юборинг.\n\n"
            "<b>Тавсияномада қуйидаги маълумотлар бўлиши мақсадга мувофиқ:</b>\n"
            "1. Исм фамилиянгиз\n"
            "2. Вилоят/шаҳар номи\n"
            "3. Чўпонингиз исми\n"
            "4. Жамоатингиз номи\n"
            "5. Матн намунаси: “Мен «______» номли Жамоатнинг чўпони ______ жамоат аъзоси _____________ нинг Онлайн Академияда ўқишига розилик билдираман”. Имзо. Сана\n\n"
            "👇 Қуйидагилардан бирини танланг:"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Тавсиянома (текст)", callback_data="letter_text"),
                InlineKeyboardButton(text="📷 Тавсиянома (фото)", callback_data="letter_photo")
            ]
        ]),
        parse_mode="HTML"
    )

    await callback.answer("Запрос отправлен пользователю.")
    await callback.message.answer("Запрос отправлен пользователю.")

@dp.callback_query(F.data == "letter_text")
async def wait_letter_text(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📝 Илтимос, тавсияномани матн кўринишида ёзинг:")
    await state.set_state(RecommendationLetter.waiting_for_text)
    await callback.answer()

@dp.callback_query(F.data == "letter_photo")
async def wait_letter_photo(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📷 Илтимос, тавсиянома сурат кўринишида юборинг:")
    await state.set_state(RecommendationLetter.waiting_for_photo)
    await callback.answer()

@dp.message(RecommendationLetter.waiting_for_text)
async def handle_letter_text(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("letter_user_id", message.from_user.id)

    text = message.text
    save_recommendation_letter(user_id, text, None)

    topic_id = get_user_topic_id(user_id)

    await bot.send_message(
        ADMIN_GROUP_ID,
        f"📜 <b>Тавсиянома (текст)</b>\n👤 {message.from_user.full_name}\n\n{text}",
        message_thread_id=topic_id,
        parse_mode="HTML"
    )
    await message.answer("✅ Тавсиянома қабул қилинди.")
    await state.clear()

@dp.message(RecommendationLetter.waiting_for_photo)
async def handle_letter_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("letter_user_id", message.from_user.id)

    file_id = message.photo[-1].file_id
    save_recommendation_letter(user_id, None, file_id)

    topic_id = get_user_topic_id(user_id)

    await bot.send_photo(
        ADMIN_GROUP_ID,
        file_id,
        caption=f"📜 <b>Тавсиянома (фото)</b>\n👤 {message.from_user.full_name}",
        message_thread_id=topic_id,
        parse_mode="HTML"
    )
    await message.answer("✅ Тавсиянома қабул қилинди.")
    await state.clear()

class UserRegistration:
        
    def __init__(self, bot):
        self.bot = bot
        self.lesson_flow = LessonFlow(bot)
    
    async def approve_user(self, callback: CallbackQuery):
        await callback.answer()

        user_id = int(callback.data.split("_")[2])


        user = get_user_by_id(user_id)
        fio = user.fio if user else "Без ФИО"
        username = user.username if user else ""

        add_user_role(user_id, fio, username, "user")

        # 🔄 Проверяем и создаём топик (на всякий случай)
        topic_id = get_user_topic_id(user_id)
        if not topic_id:
            topic_id = await ensure_topic(self.bot, user_id, fio, username)
            save_user_topic_id(user_id, topic_id)

        # ✅ Отправка пользователю
        await self.bot.send_message(
            user_id, 
            f"🎉 Табриклаймиз! Сиз талабалар рўйхатидасиз, {fio}.",
            protect_content=True
        )

        # ✅ Отправка админу
        if callback.from_user.id == OWNER_ID:
            await callback.message.answer(f"✅ Вы предоставили доступ пользователю {fio}.")
        else:
            await self.bot.send_message(
                OWNER_ID,
                f"👤 Админ {callback.from_user.full_name} предоставил доступ {fio}"
            )
            await callback.message.answer(f"✅ Пользователь {fio} добавлен как участник.")

        await send_welcome_message(self.bot, user_id)

        # ✅ Инициализация первого урока
        course = get_first_course()
        lessons = get_lessons_by_course(course["id"])
        if lessons:
            first_lesson = lessons[0]
            create_or_update_user_lesson(user_id, first_lesson["id"], "in_progress")
            
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🚀 Бошлаш", 
                    callback_data=f"start_lesson_{first_lesson['id']}"
                )]
            ])
            await self.bot.send_message(
                user_id, 
                "Дарсни бошлаш учун тугмани босинг:", 
                reply_markup=kb,
                protect_content=True
            )

class HomeworkType(StatesGroup):
    choosing_type = State()
    waiting_for_text = State()
    waiting_for_file = State()
    waiting_for_photo = State()

class LessonFlow:
    def __init__(self, bot):
        self.bot = bot

    async def start_lesson(self, user_id: int, lesson_id: int):
        lesson = get_lesson_by_id(lesson_id)
        if not lesson:
            await self.bot.send_message(user_id, "Дарс топилмади.")
            return

        if lesson.get("workbook"):
            await self.bot.send_document(user_id, document=lesson["workbook"], protect_content=True)
                    
        if lesson.get("video_file_id"):
            try:
                await self.bot.send_video(
                    user_id,
                    video=lesson["video_file_id"],
                    caption="🎥 Дарс видеоси:",
                    protect_content=True
                )
            except TelegramBadRequest as e:
                await self.bot.send_message(user_id, "❗ Видео юбориб бўлмади. Илтимос, админга хабар беринг.")
                for admin_id in tuple(ADMINISTRATION.values()):
                    await self.bot.send_message(
                        admin_id,
                        f"❌ Видео юборишда хато:\n"
                        f"👤 Фойдаланувчи: [{user_id}](tg://user?id={user_id})\n"
                        f"📚 Дарс ID: {lesson['id']}\n"
                        f"🎬 video_file_id: {lesson['video_file_id']}\n"
                        f"💥 Хатолик: {e.message}",
                        parse_mode="Markdown"
                    )

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="📺 Кўрилди",
                    callback_data=f"video_watched_{lesson_id}"
                )]
            ])
            await self.bot.send_message(
                user_id,
                "Агар видеони кўрган бўлсангиз, тугмани босинг:",
                reply_markup=keyboard,
                protect_content=True
            )
            update_user_lesson_status(user_id, lesson_id, "video_not_watched")
        else:
            await self.bot.send_message(user_id, "Видео мавжуд эмас.", protect_content=True)

    async def handle_video_watched(self, callback: CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        lesson_id = int(callback.data.split("_")[-1])
        lesson = get_lesson_by_id(lesson_id)

        update_user_lesson_status(user_id, lesson_id, "video_watched")

        if lesson.get("homework"):
            await self.bot.send_message(
                user_id, 
                f"📚 Уй вазифаси: {lesson['homework']}",
                protect_content=True
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="📝 Текст", callback_data=f"homework_text_{lesson_id}"),
                    InlineKeyboardButton(text="📄 Файл", callback_data=f"homework_file_{lesson_id}"),
                    InlineKeyboardButton(text="📷 Фото", callback_data=f"homework_photo_{lesson_id}")
                ]
            ])
            await self.bot.send_message(
                user_id,
                "Қандай шаклда уй вазифасини юбормоқчисиз?",
                reply_markup=kb,
                protect_content=True
            )

    async def choose_homework_text(self, callback: CallbackQuery, state: FSMContext):
        lesson_id = int(callback.data.split("_")[-1])
        await state.update_data(lesson_id=lesson_id)
        await callback.message.answer("📝 Илтимос, матн кўринишида уй вазифасини ёзинг:")
        await state.set_state(HomeworkType.waiting_for_text)
        await callback.answer()

    async def choose_homework_file(self, callback: CallbackQuery, state: FSMContext):
        lesson_id = int(callback.data.split("_")[-1])
        await state.update_data(lesson_id=lesson_id)
        await callback.message.answer("📄 Илтимос, файлни юборинг:")
        await state.set_state(HomeworkType.waiting_for_file)
        await callback.answer()

    async def choose_homework_photo(self, callback: CallbackQuery, state: FSMContext):
        lesson_id = int(callback.data.split("_")[-1])
        await state.update_data(lesson_id=lesson_id)
        await callback.message.answer("📷 Илтимос, расмни юборинг:")
        await state.set_state(HomeworkType.waiting_for_photo)
        await callback.answer()

    async def receive_homework_text(self, message: Message, state: FSMContext):
        data = await state.get_data()
        user_id = message.from_user.id
        lesson_id = data["lesson_id"]

        save_homework(user_id, lesson_id, message.text, None)
        update_user_lesson_status(user_id, lesson_id, "submitted")

        await message.answer("✅ Матн қабул қилинди.")
        await notify_admin_about_homework(self.bot, user_id, lesson_id, text=message.text)
        await state.clear()
        lesson = get_lesson_by_id(lesson_id)

        if lesson.get("extra_material_link"):
            await self.bot.send_message(user_id, f"📎 Қўшимча ҳавола:\n{lesson['extra_material_link']}", protect_content=True)

        if lesson.get("extra_material_file"):
            await self.bot.send_document(user_id, document=lesson["extra_material_file"], protect_content=True)

    async def receive_homework_file(self, message: Message, state: FSMContext):
        data = await state.get_data()
        user_id = message.from_user.id
        lesson_id = data["lesson_id"]

        file_id = message.document.file_id
        save_homework(user_id, lesson_id, None, file_id)
        update_user_lesson_status(user_id, lesson_id, "submitted")

        await message.answer("✅ Файл қабул қилинди.", protect_content=True)
        await notify_admin_about_homework(self.bot, user_id, lesson_id, file_id=file_id)
        await state.clear()
        lesson = get_lesson_by_id(lesson_id)

        if lesson.get("extra_material_link"):
            await self.bot.send_message(user_id, f"📎 Қўшимча ҳавола:\n{lesson['extra_material_link']}", protect_content=True)

        if lesson.get("extra_material_file"):
            await self.bot.send_document(user_id, document=lesson["extra_material_file"], protect_content=True)

    async def receive_homework_photo(self, message: Message, state: FSMContext):
        data = await state.get_data()
        user_id = message.from_user.id
        lesson_id = data["lesson_id"]

        photo_id = message.photo[-1].file_id
        save_homework(user_id, lesson_id, None, photo_id)
        update_user_lesson_status(user_id, lesson_id, "submitted")

        await message.answer("✅ Расм қабул қилинди.")
        await notify_admin_about_homework(self.bot, user_id, lesson_id, file_id=photo_id)
        await state.clear()

        lesson = get_lesson_by_id(lesson_id)
        if lesson.get("extra_material_link"):
            await self.bot.send_message(user_id, f"📎 Қўшимча ҳавола:\n{lesson['extra_material_link']}", protect_content=True)
        if lesson.get("extra_material_file"):
            await self.bot.send_document(user_id, document=lesson["extra_material_file"], protect_content=True)

registration = UserRegistration(bot)
lesson_flow = LessonFlow(bot)

@dp.callback_query(F.data.startswith("start_lesson_"))
async def cb_start_lesson(callback: CallbackQuery):
    lesson_id = int(callback.data.split("_")[-1])
    await lesson_flow.start_lesson(callback.from_user.id, lesson_id)
    await callback.answer()

@dp.callback_query(F.data.startswith("video_watched_"))
async def cb_video_watched(callback: CallbackQuery, state: FSMContext):
    await lesson_flow.handle_video_watched(callback, state)
    await callback.answer()

@dp.callback_query(F.data.startswith("homework_text_"))
async def cb_homework_text(callback: CallbackQuery, state: FSMContext):
    await lesson_flow.choose_homework_text(callback, state)

@dp.callback_query(F.data.startswith("homework_file_"))
async def cb_homework_file(callback: CallbackQuery, state: FSMContext):
    await lesson_flow.choose_homework_file(callback, state)

@dp.callback_query(F.data.startswith("homework_photo_"))
async def cb_homework_photo(callback: CallbackQuery, state: FSMContext):
    await lesson_flow.choose_homework_photo(callback, state)

@dp.message(HomeworkType.waiting_for_text)
async def msg_homework_text(message: Message, state: FSMContext):
    await lesson_flow.receive_homework_text(message, state)

@dp.message(HomeworkType.waiting_for_file, F.document)
async def msg_homework_file(message: Message, state: FSMContext):
    await lesson_flow.receive_homework_file(message, state)

@dp.message(HomeworkType.waiting_for_photo, F.photo)
async def msg_homework_photo(message: Message, state: FSMContext):
    await lesson_flow.receive_homework_photo(message, state)

@dp.callback_query(F.data.startswith("make_user_"))
async def make_user_handler(callback: CallbackQuery):
    await registration.approve_user(callback)

async def notify_admin_about_homework(bot, user_or_id, lesson_id, text=None, file_id=None):
    if isinstance(user_or_id, int):
        user = await bot.get_chat(user_or_id)
    else:
        user = user_or_id

    user_id = user.id

    full_name = user.full_name or f"ID {user.id}"
    username = f"(@{user.username})" if user.username else ""
    user_link = f"<a href='tg://user?id={user.id}'>{full_name}</a> {username}"

    lesson = get_lesson_by_id(lesson_id)
    lesson_title = lesson.get("title", f"ID {lesson_id}")

    caption = (
        f"📥 <b>Янги уй вазифаси!</b>\n"
        f"👤 Фойдаланувчи: {user_link}\n"
        f"📚 Дарс: <b>{lesson_title}</b>\n"
    )

    if text:
        safe_text = text.replace("<", "&lt;").replace(">", "&gt;")
        caption += f"\n📝 Жавоб:\n{safe_text}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_hw_{user_id}_{lesson_id}"),
            InlineKeyboardButton(text="🔁 На доработку", callback_data=f"redo_hw_{user_id}_{lesson_id}")
        ]
    ])

    topic_id = get_user_topic_id(user_id)
    if topic_id:
        try:
            if file_id:
                if file_id.startswith("AgAC"):  # Telegram photo_id prefix
                    await bot.send_photo(
                        chat_id=ADMIN_GROUP_ID,
                        message_thread_id=topic_id,
                        photo=file_id,
                        caption=caption,
                        parse_mode="html",
                        reply_markup=keyboard
                    )
                else:
                    await bot.send_document(
                        chat_id=ADMIN_GROUP_ID,
                        message_thread_id=topic_id,
                        document=file_id,
                        caption=caption,
                        parse_mode="html",
                        reply_markup=keyboard
                    )
            else:
                await bot.send_message(
                    chat_id=ADMIN_GROUP_ID,
                    message_thread_id=topic_id,
                    text=caption,
                    parse_mode="html",
                    reply_markup=keyboard
                )
        except Exception as e:
            print(f"❗ Ошибка при отправке: {e}")


class HomeworkStates(StatesGroup):
    awaiting_redo_comment = State()
@dp.callback_query(F.data.startswith("approve_hw_"))
async def approve_hw_handler(callback: CallbackQuery):
    parts = callback.data.split("_")
    user_id = int(parts[2])
    lesson_id = int(parts[3])

    approve_homework(user_id, lesson_id)

    # Обновим текст у админа
    try:
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n✅ Одобрено.",
            parse_mode="Markdown"
        )
    except Exception:
        await callback.message.answer("✅ Одобрено.")

    next_lesson = get_next_lesson(user_id, lesson_id)

    if next_lesson:
        # Если это просто следующий урок текущего курса — продолжаем как обычно
        create_or_update_user_lesson(user_id, next_lesson["id"], "in_progress")

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="➡️ Кейинги дарс",
                callback_data=f"start_lesson_{next_lesson['id']}"
            )]
        ])
        await callback.bot.send_message(
            user_id,
            f"📚 Кейинги дарс тайёр: {next_lesson['title']}",
            reply_markup=kb
        )

    else:
        # Уроков больше нет — проверим, есть ли следующий курс
        current_course = get_course_by_lesson(lesson_id)
        next_course = get_next_course_for_user(user_id, current_course["id"])

        if next_course:
            lessons = get_lessons_by_course(next_course["id"])
            if lessons:
                first_lesson = lessons[0]
                create_or_update_user_lesson(user_id, first_lesson["id"], "in_progress")

                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="🚀 Янги курсни бошлаш",
                        callback_data=f"start_lesson_{first_lesson['id']}"
                    )]
                ])
                await callback.bot.send_message(
                    user_id,
                    f"🎓 Табриклаймиз! Сиз янги курсга ўтдингиз: {next_course['title']}",
                    reply_markup=kb
                )
                
    await callback.answer("Урок одобрен. Следующий урок открыт.")
@dp.callback_query(F.data.startswith("redo_hw_"))
async def redo_hw_prompt(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    await state.update_data(user_id=int(parts[2]), lesson_id=int(parts[3]))

    await callback.message.answer("✏️ Илтимос, изоҳ қолдиринг (сабаб):")
    await state.set_state(HomeworkStates.awaiting_redo_comment)
    print(f"1. [FSM] Current state: {await state.get_data()}")
    await callback.answer()
@dp.message(StateFilter(HomeworkStates.awaiting_redo_comment))
async def redo_hw_comment_handler(message: Message, state: FSMContext):

    data = await state.get_data()
    print(f"2. [FSM] Current state: {data}")
    user_id = data["user_id"]
    lesson_id = data["lesson_id"]
    comment = message.text

    send_homework_for_redo(user_id, lesson_id, comment)

    await message.bot.send_message(
        user_id,
        f"🔁 Уй вазифангиз қайта юбориш учун қайтарилди.\n💬 Изоҳ: {comment}"
    )

    await message.answer("📨 Фойдаланувчига хабар юборилди.")
    await state.clear()


@dp.message(Command("sync_lessons"))
async def sync_lessons_count(message: Message):
    user_id = message.from_user.id
    if user_id not in tuple(ADMINISTRATION.values()):
        await message.answer("Нет доступа.")
        return

    courses = get_all_courses()
    fixed = 0
    for course in courses:
        actual_count = len(get_lessons_by_course(course["id"]))
        if course["lesson_count"] != actual_count:
            update_course_lesson_count(course["id"], actual_count)
            fixed += 1

    await message.answer(f"Синхронизация завершена.\nОбновлено курсов: {fixed}")

@dp.callback_query(F.data.startswith("make_admin_"))
async def make_admin(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    req = pending_requests.pop(user_id, None)
    fio = req["fio"] if req else "Без ФИО"
    username = req["username"] if req else ""

    add_user_role(user_id, fio, username, "admin")
    await bot.send_message(user_id, f"🎉 Добро пожаловать в команду, админ {fio}!")

    if callback.from_user.id in tuple(ADMINISTRATION.values()):
        await callback.message.answer(f"✅ Вы предоставили доступ пользователю {fio}.")
    else:
        await bot.send_message(OWNER_ID, f"👤 Админ {callback.from_user.full_name} предоставил доступ пользователю {fio}.")
        await callback.message.answer(f"✅ Пользователь {fio} назначен админом.")
    await callback.answer()
@dp.callback_query(F.data.regexp(r"^decline_\d+$"))
async def decline_request(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    req = pending_requests.pop(user_id, None)
    fio = req["fio"] if req else f"ID {user_id}"
    await bot.send_message(user_id, "❌ Ваш запрос на доступ отклонён, обратитесь к администации.")
    await callback.message.answer(f"❌ Запрос от пользователя {fio} отклонён.")
    await callback.answer()

    
class CourseCreation(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_number_course = State()
    waiting_for_lesson_count = State()
    waiting_for_lesson_title = State()
    waiting_for_lesson_video = State()
    waiting_for_homework = State()
    waiting_for_extra_material_link = State()
    waiting_for_extra_material_file = State()
@dp.message(Command("add_course"))
async def start_course_creation(message: Message, state: FSMContext):
    logging.info(f"Received /add_course from {message.from_user.id}")
    user_id = message.from_user.id
    if user_id not in tuple(ADMINISTRATION.values()):
        await message.answer("Нет доступа.")
        return
    await state.clear()
    await message.answer("Введите название курса:")
    await state.set_state(CourseCreation.waiting_for_title)
@dp.message(CourseCreation.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer("Введите описание курса (можно пропустить, отправив «-»):")
    await state.set_state(CourseCreation.waiting_for_description)
@dp.message(CourseCreation.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    description = message.text.strip()
    if description == "-":
        description = ""
    await state.update_data(description=description)
    await message.answer("Введите номер курса по счету (например, 1, 2, 3...):")
    await state.set_state(CourseCreation.waiting_for_number_course)
@dp.message(CourseCreation.waiting_for_number_course)
async def process_number_course(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 1:
        await message.answer("Введите корректный номер курса (целое число).")
        return
    await state.update_data(number_course=int(message.text))
    await message.answer("Введите количество занятий:")
    await state.set_state(CourseCreation.waiting_for_lesson_count)
@dp.message(CourseCreation.waiting_for_lesson_count)
async def process_lesson_count(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 1:
        await message.answer("Введите корректное число.")
        return
    count = int(message.text)
    await state.update_data(lesson_total=count, lessons=[], lesson_index=0)
    await message.answer(f"Введите название занятия 1 из {count}:")
    await state.set_state(CourseCreation.waiting_for_lesson_title)
@dp.message(CourseCreation.waiting_for_lesson_title)
async def process_lesson_title(message: Message, state: FSMContext):
    data = await state.get_data()
    lesson_index = data["lesson_index"]
    lessons = data["lessons"]

    lessons.append({
        "title": message.text.strip(),
        "video": None,
        "homework": None,
        "extra_material_file": None,
        "extra_material_link": None
    })
    await state.update_data(lessons=lessons)
    await message.answer("Теперь отправьте видеофайл к этому занятию или «-» для пропуска.")
    await state.set_state(CourseCreation.waiting_for_lesson_video)
@dp.message(CourseCreation.waiting_for_lesson_video)
async def process_lesson_video(message: Message, state: FSMContext):
    if message.text and message.text.strip() == "-":
        data = await state.get_data()
        lesson_index = data["lesson_index"]
        lessons = data["lessons"]
        lessons[lesson_index]["video"] = None
        await state.update_data(lessons=lessons)

        await message.answer("Теперь отправьте домашнее задание:")
        await state.set_state(CourseCreation.waiting_for_homework)
        return

    if not message.video:
        await message.answer("Отправьте видеофайл или «-» для пропуска.")
        return

    data = await state.get_data()
    lesson_index = data["lesson_index"]
    lessons = data["lessons"]

    lessons[lesson_index]["video"] = message.video.file_id
    await state.update_data(lessons=lessons)

    await message.answer("Теперь отправьте домашнее задание:")
    await state.set_state(CourseCreation.waiting_for_homework)
@dp.message(CourseCreation.waiting_for_homework)
async def process_homework_text(message: Message, state: FSMContext):
    data = await state.get_data()
    lesson_index = data["lesson_index"]
    lessons = data["lessons"]

    lessons[lesson_index]["homework"] = message.text.strip()
    await state.update_data(lessons=lessons)
    await message.answer("Отправьте ссылку на дополнительный материал (если есть) или «-», чтобы пропустить:")
    await state.set_state(CourseCreation.waiting_for_extra_material_link)  
@dp.message(CourseCreation.waiting_for_extra_material_link)
async def ask_extra_material_link(message: Message, state: FSMContext):
    data = await state.get_data()
    lesson_index = data["lesson_index"]
    lessons = data["lessons"]

    if message.text and message.text.strip() == "-":
        lessons[lesson_index]["extra_material_link"] = None
    else:
        lessons[lesson_index]["extra_material_link"] = message.text.strip()
    await state.update_data(lessons=lessons)
    await message.answer("Отправьте файл (.docx, .pdf и т.д.) или «-» для пропуска:")
    await state.set_state(CourseCreation.waiting_for_extra_material_file)
@dp.message(CourseCreation.waiting_for_extra_material_file)
async def process_extra_material_file(message: Message, state: FSMContext):
    data = await state.get_data()
    lessons = data["lessons"]
    lesson_index = data["lesson_index"]

    file_id = None
    if message.document:
        file_id = message.document.file_id
    elif message.text and message.text.strip() == "-":
        file_id = None
    else:
        await message.answer("Отправьте файл или «-» для пропуска.")
        return

    lessons[lesson_index]["extra_material_file"] = file_id
    await state.update_data(lessons=lessons)

    await finalize_homework(message, state)
async def finalize_homework(message: Message, state: FSMContext):
    data = await state.get_data()
    lesson_index = data["lesson_index"]
    lessons = data["lessons"]

    await state.update_data(lessons=lessons)

    if lesson_index + 1 < data["lesson_total"]:
        await state.update_data(
            lesson_index=lesson_index + 1,
            homework=None,
            extra_material_link=None,
            extra_material_file=None
        )
        await message.answer(f"Введите название занятия {lesson_index + 2} из {data['lesson_total']}:")
        await state.set_state(CourseCreation.waiting_for_lesson_title)
    else:
        await save_course_to_db(message.from_user.id, state)
        await state.clear()

def get_lesson_buttons(course_id):
    lessons = get_lessons_by_course(course_id)
    return [
        [InlineKeyboardButton(text=f"Урок {i+1}: {lesson['title']}", callback_data=f"view_lesson_{course_id}_{i}")]
        for i, lesson in enumerate(lessons)
    ]
async def save_course_to_db(user_id: int, state: FSMContext):
    data = await state.get_data()
    approved = False
    lesson_count = data["lesson_total"]

    course_id = add_course(
        data["title"], 
        data["description"], 
        lesson_count, 
        user_id, 
        approved, 
        data.get("number_course") 
    )

    for lesson in data["lessons"]:
        add_lesson(
            course_id,
            lesson["title"],
            lesson.get("video") or lesson.get("video_file_id"),             
            lesson["homework"],
            lesson["extra_material_file"],
            lesson["extra_material_link"]
        )

    await bot.send_message(user_id, f"✅ Курс \"{data['title']}\" сохранён (статус: на модерации).")

    lesson_buttons = get_lesson_buttons(course_id)

    action_buttons = [[
        InlineKeyboardButton(text="✅ Завершить", callback_data=f"approve_course_{course_id}"),
        InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_course_{course_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_course_{course_id}")
    ]]

    markup = InlineKeyboardMarkup(inline_keyboard=lesson_buttons + action_buttons)

    topic_id = get_user_topic_id(user_id)
    if topic_id:
        await bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            message_thread_id=topic_id,
            text="Проверьте созданный курс и завершите создание курса.",
            reply_markup=markup
        )


@dp.callback_query(F.data.regexp(r"^view_lesson_\d+_\d+$"))
async def view_lesson(callback: CallbackQuery):
    _, _, course_id, lesson_idx = callback.data.split("_")
    lessons = get_lessons_by_course(int(course_id))
    idx = int(lesson_idx)
    if idx < 0 or idx >= len(lessons):
        await callback.message.answer("Урок не найден.")
        return

    lesson = lessons[idx]
    await callback.message.answer(f"<b>№{idx+1}: {lesson['title']}</b>")

    video_id = lesson.get("video_file_id") or lesson.get("video")
    if video_id:
        try:
            await callback.message.answer_video(video_id)
        except Exception:
            await callback.message.answer(f"Видео не найдено: {video_id}")

    homework = lesson.get('homework') or "-"
    await callback.message.answer(f"<b>Домашнее задание:</b> {homework}")

    extra_file = lesson.get("extra_material_file")
    extra_link = lesson.get("extra_material_link") or "-"
    if extra_file:
        try:
            await callback.message.answer_document(extra_file)
        except Exception:
            await callback.message.answer(f"Файл доп. материала не найден: {extra_file}")
    await callback.message.answer(f"<b>Ссылка на доп. материал:</b> {extra_link or '-'}")

    await callback.answer()
@dp.callback_query(F.data.startswith("approve_course_"))
async def approve_course(callback: CallbackQuery):
    course_id = int(callback.data.split("_")[-1])
    approve_course_by_id(course_id)
    await callback.message.edit_text("✅ Курс успешно завершён и опубликован.")
    await callback.answer()
@dp.callback_query(F.data.startswith("decline_course_"))
async def decline_course(callback: CallbackQuery):
    course_id = int(callback.data.split("_")[-1])
    delete_course_and_lessons(course_id)
    await callback.message.edit_text("❌ Курс и все связанные уроки удалены.")
    await callback.answer()

@dp.callback_query(F.data.regexp(r"^edit_course_\d+$"))
async def edit_course(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in tuple(ADMINISTRATION.values()):  # исправлено!
        await callback.message.answer("Нет доступа.")
        return
    course_id = int(callback.data.split("_")[-1])
    await state.update_data(edit_course_id=course_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Название/описание", callback_data=f"edit_course_info_{course_id}")],
        [InlineKeyboardButton(text="Добавить урок", callback_data=f"add_lesson_{course_id}")],
        [InlineKeyboardButton(text="Удалить урок", callback_data=f"delete_lesson_{course_id}")],
        [InlineKeyboardButton(text="Редактировать урок", callback_data=f"choose_lesson_edit_{course_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])
    try:
        await callback.message.edit_text("Что вы хотите отредактировать?", reply_markup=kb)
    except Exception as e:
        if "message is not modified" in str(e):
            await callback.answer("Вы уже находитесь в этом меню.", show_alert=False)
        else:
            raise
    await callback.answer()

@dp.callback_query(F.data.regexp(r"^edit_course_info_\d+$"))
async def edit_course_info(callback: CallbackQuery, state: FSMContext):
    course_id = int(callback.data.split("_")[-1])
    await state.update_data(edit_course_id=course_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Название", callback_data=f"edit_course_title_{course_id}")],
        [InlineKeyboardButton(text="Описание", callback_data=f"edit_course_desc_{course_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"edit_course_{course_id}")]
    ])
    try:
        await callback.message.edit_text("Что вы хотите изменить?", reply_markup=kb)
    except Exception as e:
        if "message is not modified" in str(e):
            await callback.answer("Вы уже находитесь в этом меню.", show_alert=False)
        else:
            raise
    await callback.answer()

class EditCourse(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
@dp.callback_query(F.data.regexp(r"^edit_course_title_\d+$"))
async def edit_course_title(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in tuple(ADMINISTRATION.values()):
        await message.answer("Нет доступа.")
        return
    course_id = int(callback.data.split("_")[-1])
    await state.update_data(edit_course_id=course_id)    
    await callback.message.answer("Введите новое название курса:")
    await state.set_state(EditCourse.waiting_for_title)
@dp.callback_query(F.data.regexp(r"^edit_course_desc_\d+$"))
async def edit_course_desc(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in tuple(ADMINISTRATION.values()):
        await message.answer("Нет доступа.")
        return
    course_id = int(callback.data.split("_")[-1])
    await state.update_data(edit_course_id=course_id)
    await callback.message.answer("Введите новое описание курса:")
    await state.set_state(EditCourse.waiting_for_description)
@dp.message(EditCourse.waiting_for_title)
async def update_course_title_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    if "edit_course_id" not in data:
        await message.answer("Ошибка: не выбран курс для редактирования. Начните заново через меню.")
        await state.clear()
        return
    update_course_title(data["edit_course_id"], message.text.strip())
    await message.answer("Название курса обновлено.")
    course = get_course_by_id(data["edit_course_id"])
    await message.answer(f"<b>Новое название курса:</b> {course['title']}\n<b>Описание:</b> {course['description']}")
    await edit_course_menu(message, data["edit_course_id"])
    await state.clear()
@dp.message(EditCourse.waiting_for_description)
async def update_course_description_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    if "edit_course_id" not in data:
        await message.answer("Ошибка: не выбран курс для редактирования. Начните заново через меню.")
        await state.clear()
        return
    update_course_description(data["edit_course_id"], message.text.strip())
    await message.answer("Описание курса обновлено.")
    course = get_course_by_id(data["edit_course_id"])
    await message.answer(f"<b>Название курса:</b> {course['title']}\n<b>Новое описание:</b> {course['description']}")
    await edit_course_menu(message, data["edit_course_id"])
    await state.clear()

class AddLesson(StatesGroup):
    waiting_for_title = State()
    waiting_for_video = State()
    waiting_for_homework = State()
    waiting_for_extra_material_link = State()
    waiting_for_extra_material_file = State()
@dp.callback_query(F.data.startswith("add_lesson_"))
async def add_lesson_to_course(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id in tuple(ADMINISTRATION.values()):
        course_id = int(callback.data.split("_")[-1])
        await state.update_data(add_lesson_course_id=course_id)
        await callback.message.edit_text("Введите название нового урока:")
        await state.set_state(AddLesson.waiting_for_title)
    else:
        await callback.message.answer("Нет доступа к этой функции.")
@dp.message(AddLesson.waiting_for_title)
async def add_lesson_title(message: Message, state: FSMContext):
    await state.update_data(new_lesson_title=message.text.strip())
    await message.answer("Отправьте видео для нового урока или «-»:")
    await state.set_state(AddLesson.waiting_for_video)
@dp.message(AddLesson.waiting_for_video)
async def add_lesson_video(message: Message, state: FSMContext):
    if message.text and message.text.strip() == "-":
        video = None
    elif message.video:
        video = message.video.file_id
    else:
        await message.answer("Отправьте видеофайл или «-».")
        return
    await state.update_data(new_lesson_video=video)
    await message.answer("Введите домашнее задание:")
    await state.set_state(AddLesson.waiting_for_homework)
@dp.message(AddLesson.waiting_for_homework)
async def add_lesson_homework(message: Message, state: FSMContext):
    await state.update_data(new_lesson_homework=message.text.strip())
    await message.answer("Отправьте ссылку на доп. материал или «-»:")
    await state.set_state(AddLesson.waiting_for_extra_material_link)
@dp.message(AddLesson.waiting_for_extra_material_link)
async def add_lesson_link(message: Message, state: FSMContext):
    link = message.text.strip()
    if link == "-":
        link = None
    await state.update_data(new_lesson_extra_link=link)
    await message.answer("Отправьте файл доп. материала (.docx, .pdf) или «-»:")
    await state.set_state(AddLesson.waiting_for_extra_material_file)
@dp.message(AddLesson.waiting_for_extra_material_file)
async def add_lesson_file(message: Message, state: FSMContext):
    if message.document:
        file_id = message.document.file_id
    elif message.text and message.text.strip() == "-":
        file_id = None
    else:
        await message.answer("Отправьте файл или «-».")
        return

    data = await state.get_data()
    add_lesson(
        data["add_lesson_course_id"],
        data["new_lesson_title"],
        data["new_lesson_video"],
        data["new_lesson_homework"],
        extra_material_link=data.get("new_lesson_extra_link"),
        extra_material_file=file_id
    )
    await message.answer("Урок добавлен.")
    await edit_course_menu(message, data["add_lesson_course_id"])
    await state.clear()

class AddLessonGlobal(StatesGroup):
    waiting_for_course = State()
@dp.message(Command("add_lesson"))
async def add_lesson_command(message: Message, state: FSMContext):
    if message.from_user.id not in tuple(ADMINISTRATION.values()):
        await message.answer("Нет доступа.")
        return
    courses = get_all_courses()
    if not courses:
        await message.answer("Нет доступных курсов.")
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=course["title"], callback_data=f"add_lesson_choose_{course['id']}")]
            for course in courses
        ]
    )
    await message.answer("Выберите курс для добавления урока:", reply_markup=kb)
    await state.set_state(AddLessonGlobal.waiting_for_course)
@dp.callback_query(F.data.startswith("add_lesson_choose_"), AddLessonGlobal.waiting_for_course)
async def add_lesson_choose_course(callback: CallbackQuery, state: FSMContext):
    course_id = int(callback.data.split("_")[-1])
    await state.clear()
    await state.update_data(add_lesson_course_id=course_id)
    await callback.message.edit_text("Введите название нового урока:")
    await state.set_state(AddLesson.waiting_for_title)

@dp.callback_query(F.data.startswith("delete_lesson_"))
async def delete_lesson_from_course(callback: CallbackQuery, state: FSMContext):
    course_id = int(callback.data.split("_")[-1])
    lessons = get_lessons_by_course(course_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lesson["title"], callback_data=f"confirm_delete_lesson_{lesson['id']}_{course_id}")]
        for lesson in lessons
    ] + [[InlineKeyboardButton(text="⬅️ Назад", callback_data=f"edit_course_{course_id}")]])
    await callback.message.edit_text("Выберите урок для удаления:", reply_markup=kb)
    await callback.answer()
@dp.callback_query(F.data.regexp(r"^confirm_delete_lesson_\d+_\d+$"))
async def confirm_delete_lesson(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    lesson_id = int(parts[-2])
    course_id = int(parts[-1])
    delete_lesson_by_id(lesson_id)
    await callback.message.answer("Урок удалён.")
    await edit_course_menu(callback.message, course_id)

class DeleteLessonGlobal(StatesGroup):
    waiting_for_course = State()
    waiting_for_lesson = State()
@dp.message(Command("delete_lesson"))
async def delete_lesson_command(message: Message, state: FSMContext):
    if message.from_user.id not in tuple(ADMINISTRATION.values()):
        await message.answer("Нет доступа.")
        return
    courses = get_all_courses()
    if not courses:
        await message.answer("Нет доступных курсов.")
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=course["title"], callback_data=f"delete_lesson_choose_course_{course['id']}")]
            for course in courses
        ]
    )
    await message.answer("Выберите курс для удаления урока:", reply_markup=kb)
    await state.set_state(DeleteLessonGlobal.waiting_for_course)
@dp.callback_query(F.data.startswith("delete_lesson_choose_course_"), DeleteLessonGlobal.waiting_for_course)
async def delete_lesson_choose_course(callback: CallbackQuery, state: FSMContext):
    course_id = int(callback.data.split("_")[-1])
    lessons = get_lessons_by_course(course_id)
    if not lessons:
        await callback.message.edit_text("В этом курсе нет уроков.")
        await state.clear()
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=lesson["title"], callback_data=f"delete_lesson_choose_{lesson['id']}_{course_id}")]
            for lesson in lessons
        ]
    )
    await state.update_data(delete_course_id=course_id)
    await callback.message.edit_text("Выберите урок для удаления:", reply_markup=kb)
    await state.set_state(DeleteLessonGlobal.waiting_for_lesson)
@dp.callback_query(F.data.startswith("delete_lesson_choose_"), DeleteLessonGlobal.waiting_for_lesson)
async def delete_lesson_choose_lesson(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    lesson_id = int(parts[-2])
    course_id = int(parts[-1])
    delete_lesson_by_id(lesson_id)
    await callback.message.edit_text("Урок удалён.")
    await state.clear()

class DeleteCourseGlobal(StatesGroup):
    waiting_for_course = State()
@dp.message(Command("delete_course"))
async def delete_course_command(message: Message, state: FSMContext):
    if message.from_user.id not in tuple(ADMINISTRATION.values()):
        await message.answer("Нет доступа.")
        return
    courses = get_all_courses()
    if not courses:
        await message.answer("Нет доступных курсов.")
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=course["title"], callback_data=f"delete_course_choose_{course['id']}")]
            for course in courses
        ]
    )
    await message.answer("Выберите курс для удаления:", reply_markup=kb)
    await state.set_state(DeleteCourseGlobal.waiting_for_course)
@dp.callback_query(F.data.startswith("delete_course_choose_"), DeleteCourseGlobal.waiting_for_course)
async def delete_course_choose(callback: CallbackQuery, state: FSMContext):
    course_id = int(callback.data.split("_")[-1])
    delete_course_and_lessons(course_id)
    await callback.message.edit_text("Курс и все его уроки удалены.")
    await state.clear()

class EditLesson(StatesGroup):
    waiting_for_title = State()
    waiting_for_video = State()
    waiting_for_homework = State()
    waiting_for_extra_material_file = State()
    waiting_for_extra_material_link = State()
@dp.callback_query(F.data.startswith("choose_lesson_edit_"))
async def choose_lesson_edit(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in tuple(ADMINISTRATION.values()):
        await callback.answer("Нет доступа.", show_alert=True)
        return

    course_id = int(callback.data.split("_")[-1])
    lessons = get_lessons_by_course(course_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lesson["title"], callback_data=f"edit_lesson_{lesson['id']}_{course_id}")]
        for lesson in lessons
    ] + [[InlineKeyboardButton(text="⬅️ Назад", callback_data=f"edit_course_{course_id}")]])
    await callback.message.edit_text("Выберите урок для редактирования:", reply_markup=kb)
    await callback.answer()
@dp.callback_query(F.data.regexp(r"^edit_lesson_\d+_\d+$"))
async def edit_lesson(callback: CallbackQuery, state: FSMContext):
    _, _, lesson_id, course_id = callback.data.split("_")
    await state.update_data(edit_lesson_id=int(lesson_id), edit_course_id=int(course_id))
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Название", callback_data=f"edit_lesson_title_{lesson_id}")],
        [InlineKeyboardButton(text="Видео", callback_data=f"edit_lesson_video_{lesson_id}")],
        [InlineKeyboardButton(text="Домашнее задание", callback_data=f"edit_lesson_homework_{lesson_id}")],
        [InlineKeyboardButton(text="Файл доп. материала", callback_data=f"edit_lesson_extra_file_{lesson_id}")],
        [InlineKeyboardButton(text="Ссылка на доп. материал", callback_data=f"edit_lesson_extra_link_{lesson_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"choose_lesson_edit_{course_id}")]
    ])
    await callback.message.edit_text("Что редактировать в уроке?", reply_markup=kb)
    await callback.answer()
@dp.callback_query(F.data.regexp(r"^edit_lesson_title_\d+$"))
async def edit_lesson_title(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите новое название урока:")
    await state.set_state(EditLesson.waiting_for_title)
@dp.callback_query(F.data.regexp(r"^edit_lesson_video_\d+$"))
async def edit_lesson_video(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Отправьте новое видео для урока:")
    await state.set_state(EditLesson.waiting_for_video)
@dp.callback_query(F.data.regexp(r"^edit_lesson_homework_\d+$"))
async def edit_lesson_homework(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите новое домашнее задание:")
    await state.set_state(EditLesson.waiting_for_homework)
@dp.callback_query(F.data.regexp(r"^edit_lesson_extra_file_\d+$"))
async def edit_lesson_extra_file(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Отправьте новый файл доп. материала или напишите «-», чтобы удалить файл:")
    await state.set_state(EditLesson.waiting_for_extra_material_file)
@dp.callback_query(F.data.regexp(r"^edit_lesson_extra_link_\d+$"))
async def edit_lesson_extra_link(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите новую ссылку на доп. материал или напишите «-», чтобы удалить ссылку:")
    await state.set_state(EditLesson.waiting_for_extra_material_link)


class EditCourseGlobal(StatesGroup):
    waiting_for_course = State()
@dp.message(Command("edit_course"))
async def edit_course_command(message: Message, state: FSMContext):
    if message.from_user.id not in tuple(ADMINISTRATION.values()):
        await message.answer("Нет доступа.")
        return
    courses = get_all_courses()
    if not courses:
        await message.answer("Нет доступных курсов.")
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=course["title"], callback_data=f"edit_course_choose_{course['id']}")]
            for course in courses
        ]
    )
    await message.answer("Выберите курс для редактирования:", reply_markup=kb)
    await state.set_state(EditCourseGlobal.waiting_for_course)
@dp.callback_query(F.data.regexp(r"^edit_course_choose_\d+$"), EditCourseGlobal.waiting_for_course)
async def edit_course_choose(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in tuple(ADMINISTRATION.values()):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    course_id = int(callback.data.split("_")[-1])
    await state.clear()
    await edit_course_menu(callback.message, course_id)


@dp.message(EditLesson.waiting_for_title)
async def update_lesson_title_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    update_lesson_title(data["edit_lesson_id"], message.text.strip())
    await message.answer("Название урока обновлено.")
    await edit_lesson_menu(message, data["edit_lesson_id"], data["edit_course_id"])
    await state.clear()
@dp.message(EditLesson.waiting_for_video)
async def update_lesson_video_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    if not message.video:
        await message.answer("Пожалуйста, отправьте видеофайл.")
        return
    update_lesson_video(data["edit_lesson_id"], message.video.file_id)
    await message.answer("Видео урока обновлено.")
    await edit_lesson_menu(message, data["edit_lesson_id"], data["edit_course_id"])
    await state.clear()
@dp.message(EditLesson.waiting_for_homework)
async def update_lesson_homework_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    update_lesson_homework(data["edit_lesson_id"], message.text.strip())
    await message.answer("Домашнее задание обновлено.")
    await edit_lesson_menu(message, data["edit_lesson_id"], data["edit_course_id"])
    await state.clear()
@dp.message(EditLesson.waiting_for_extra_material_file)
async def update_lesson_extra_material_file_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    if message.text and message.text.strip() == "-":
        update_lesson_extra_material_file(data["edit_lesson_id"], None)
        await message.answer("Файл доп. материала удалён.")
    elif message.document:
        update_lesson_extra_material_file(data["edit_lesson_id"], message.document.file_id)
        await message.answer("Файл доп. материала обновлён.")
    else:
        await message.answer("Пожалуйста, отправьте файл или напишите «-» для удаления.")
        return
    await edit_lesson_menu(message, data["edit_lesson_id"], data["edit_course_id"])
    await state.clear()
@dp.message(EditLesson.waiting_for_extra_material_link)
async def update_lesson_extra_material_link_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    if message.text and message.text.strip() == "-":
        update_lesson_extra_material_link(data["edit_lesson_id"], None)
        await message.answer("Ссылка на доп. материал удалена.")
    else:
        update_lesson_extra_material_link(data["edit_lesson_id"], message.text.strip())
        await message.answer("Ссылка на доп. материал обновлена.")
    await edit_lesson_menu(message, data["edit_lesson_id"], data["edit_course_id"])
    await state.clear()


@dp.callback_query(F.data == "back_to_courses")
async def back_to_courses(callback: CallbackQuery):
    courses = get_all_courses()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=course["title"], callback_data=f"view_course_{course['id']}")]
            for course in courses
        ]
    )
    try:
        await callback.message.edit_text("Список курсов:", reply_markup=kb)
    except Exception:
        await callback.message.answer("Список курсов:", reply_markup=kb)
    await callback.answer()
@dp.callback_query(F.data.regexp(r"^edit_course_\d+$"))
async def back_to_edit_course(callback: CallbackQuery, state: FSMContext):
    course_id = int(callback.data.split("_")[-1])
    await edit_course_menu(callback.message, course_id)
    await callback.answer()
@dp.callback_query(F.data.regexp(r"^choose_lesson_edit_\d+$"))
async def back_to_choose_lesson_edit(callback: CallbackQuery, state: FSMContext):
    course_id = int(callback.data.split("_")[-1])
    await choose_lesson_edit(callback, state)
    await callback.answer()
@dp.callback_query(F.data.regexp(r"^edit_course_info_\d+$"))
async def back_to_edit_course_info(callback: CallbackQuery, state: FSMContext):
    course_id = int(callback.data.split("_")[-1])
    await edit_course_menu(callback.message, course_id)
    await callback.answer()

@dp.callback_query(F.data.regexp(r"^delete_lesson_choose_course_\d+$"))
async def back_to_delete_lesson_choose_course(callback: CallbackQuery, state: FSMContext):
    course_id = int(callback.data.split("_")[-1])
    lessons = get_lessons_by_course(course_id)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=lesson["title"], callback_data=f"delete_lesson_choose_{lesson['id']}_{course_id}")]
            for lesson in lessons
        ]
    )
    await callback.message.edit_text("Выберите урок для удаления:", reply_markup=kb)
    await callback.answer()
@dp.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    await menu_command(callback.message)
    await callback.answer()
@dp.message(F.text == "⬅️ Назад")
async def fsm_back_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    course_id = data.get("edit_course_id")
    if course_id:
        await edit_course_menu(message, course_id)
    else:
        await message.answer("Главное меню. Используйте команды или кнопки для работы с ботом.")

async def edit_course_menu(message: Message, course_id: int):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Название/описание", callback_data=f"edit_course_info_{course_id}")],
        [InlineKeyboardButton(text="Добавить урок", callback_data=f"add_lesson_{course_id}")],
        [InlineKeyboardButton(text="Удалить урок", callback_data=f"delete_lesson_{course_id}")],
        [InlineKeyboardButton(text="Редактировать урок", callback_data=f"choose_lesson_edit_{course_id}")],
        [InlineKeyboardButton(text="✅ Завершить", callback_data=f"approve_course_{course_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_course_{course_id}")]
    ])
    try:
        await message.edit_text("Что вы хотите отредактировать?", reply_markup=kb)
    except Exception:
        await message.answer("Что вы хотите отредактировать?", reply_markup=kb)
async def edit_lesson_menu(message: Message, lesson_id: int, course_id: int):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Название", callback_data=f"edit_lesson_title_{lesson_id}")],
        [InlineKeyboardButton(text="Видео", callback_data=f"edit_lesson_video_{lesson_id}")],
        [InlineKeyboardButton(text="Домашнее задание", callback_data=f"edit_lesson_homework_{lesson_id}")],
        [InlineKeyboardButton(text="Файл доп. материала", callback_data=f"edit_lesson_extra_file_{lesson_id}")],
        [InlineKeyboardButton(text="Ссылка на доп. материал", callback_data=f"edit_lesson_extra_link_{lesson_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"choose_lesson_edit_{course_id}")]
    ])
    try:
        await message.edit_text("Что редактировать в уроке?", reply_markup=kb)
    except Exception as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise

@dp.message(Command("courses"))
async def show_courses(message: Message):
    user_id = message.from_user.id
    if user_id not in ALL_ADMINS.values():
        await message.answer("Нет доступа.")
        return
    courses = get_all_courses()
    if not courses:
        await message.answer("Нет доступных курсов.")
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=course["title"], callback_data=f"view_course_{course['id']}")]
            for course in courses
        ]
    )
    await message.answer("Список курсов:", reply_markup=kb)
@dp.callback_query(F.data.regexp(r"^view_lesson_simple_\d+$"))
async def view_lesson_simple(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in ALL_ADMINS.values():
        await callback.answer("Нет доступа.", show_alert=True)
        return
    lesson_id = int(callback.data.split("_")[-1])
    lessons = [lesson for course in get_all_courses() for lesson in get_lessons_by_course(course["id"])]
    lesson = next((l for l in lessons if l["id"] == lesson_id), None)
    if not lesson:
        await callback.message.answer("Урок не найден.")
        return
    text = f"<b>{lesson['title']}</b>"
    video_id = lesson.get("video_file_id") or lesson.get("video")
    if video_id:
        try:
            await callback.message.answer_video(video_id)
        except Exception:
            text += f"\nВидео не найдено: {video_id}"
    text += f"\n\nДомашнее задание: {lesson.get('homework', '-')}"
    extra_file = lesson.get("extra_material_file")
    extra_link = lesson.get("extra_material_link")
    if extra_file:
        try:
            await callback.message.answer_document(extra_file)
        except Exception:
            text += f"\nДоп. материал не найден: {extra_file}"
    if extra_link:
        text += f"\nСсылка на доп. материал: {extra_link}"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_courses")]
        ]
    )
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception as e:
        if "message is not modified" not in str(e):
            raise
@dp.callback_query(F.data.regexp(r"^view_course_\d+$"))
async def view_course(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in ALL_ADMINS.values():
        await callback.answer("Нет доступа.", show_alert=True)
        return
    course_id = int(callback.data.split("_")[-1])
    course = get_course_by_id(course_id)
    lessons = get_lessons_by_course(course_id)
    text = f"<b>{course['title']}</b>\n{course['description']}\n\nУроки:"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=lesson["title"], callback_data=f"view_lesson_simple_{lesson['id']}")]
            for lesson in lessons
        ] + [[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_courses")]]
    )
    await callback.message.edit_text(text, reply_markup=kb)


class Feedback(StatesGroup):
    waiting_for_message = State()

@dp.message(Command("feedback"))
async def start_feedback(message: Message, state: FSMContext):
    await message.answer("✉️ Хабарингизни ёзинг:")
    await state.set_state(Feedback.waiting_for_message)

@dp.message(Feedback.waiting_for_message)
async def process_feedback(message: Message, state: FSMContext):
    user = message.from_user
    user_id = user.id
    fio = user.full_name
    username = user.username or ""
    
    topic_id = get_user_topic_id(user_id)
    if not topic_id:
        topic_id = await ensure_topic(bot, user_id, fio, username)
        save_user_topic_id(user_id, topic_id)

    header = f"📨 Feedback от {fio} (@{username}):"

    # Определяем тип сообщения
    if message.text:
        await bot.send_message(ADMIN_GROUP_ID, header + f"\n\n{message.text}", message_thread_id=topic_id)
    elif message.document:
        await bot.send_document(ADMIN_GROUP_ID, message.document.file_id, caption=header, message_thread_id=topic_id)
    elif message.photo:
        await bot.send_photo(ADMIN_GROUP_ID, message.photo[-1].file_id, caption=header, message_thread_id=topic_id)
    else:
        await message.answer("❗Формат не поддерживается.")

    await message.answer("✅ Хабарингиз маъмуриятга юборилди.")
    await state.clear()

@dp.message(F.chat.id == ADMIN_GROUP_ID, F.is_topic_message)
async def admin_reply_to_user(message: Message):
    user = get_user_by_topic_id(message.message_thread_id)
    if not user:
        return

    text = message.text or message.caption
    if not text:
        return

    try:
        await bot.send_message(user.id, f"💬 Маъмуриятдан:\n{text}")
    except:
        await message.reply("❗ Юбориб бўлмади.")

async def send_bulk_message(bot, user_ids: list[int], text: str):
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, text)
            print(f"✅ Успешно: {user_id}")
        except (TelegramForbiddenError, TelegramBadRequest) as e:
            print(f"🚫 Не удалось {user_id}: {e}")
        await asyncio.sleep(0.4)


# async def send_warning(bot, user_ids: list[int]):
#     text = """Бот фаолиятини янгилади. Дарсларни ўтишда давом этишингиз мумкин."""
#     for user_id in user_ids:
#         try:
#             await bot.send_message(user_id, text)
#             print(f"✅ Юборилди: {user_id}")
#         except (TelegramForbiddenError, TelegramBadRequest) as e:
#             print(f"🚫 Ўтказилди: {user_id} | {e}")
#         await asyncio.sleep(0.3)

# def get_all_user_ids():
#     try:
#         with SessionLocal() as session:
#             return [user.id for user in session.query(User).all()]
#     except Exception as e:
#         print(f"❗ DB error: {e}")
#         return []


async def main():
    dp.message.middleware(MessageLoggerMiddleware())
    await dp.start_polling(bot)

    # user_ids = get_all_user_ids()
    # await send_warning(bot, user_ids)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
