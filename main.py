import re
from config import BOT_TOKEN, OWNER_ID, ADMIN_IDS
from aiogram.filters import Command
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.state import StatesGroup, State
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup
from db import ( 
    check_user_role, add_user_role, add_course, add_lesson, 
    update_course_title, update_course_description, get_all_courses,
    update_lesson_title, update_lesson_video, delete_course_and_lessons,
    update_lesson_homework, update_lesson_material, delete_lesson_by_id, 
    get_lessons_by_course, get_course_by_id, approve_course_by_id)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
pending_requests = {}

@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    role = check_user_role(message.from_user.id)
    if role == "owner":
        await message.answer( f"Вы уже авторизованы. Ваша роль: {role}",
        )
    elif role in ["user", "admin"]:
        await message.answer(f"Вы уже авторизованы. Ваша роль: {role}")
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Запросить доступ", callback_data="request_access")]
        ])
        await message.answer(
            f"Привет, {message.from_user.full_name}! Пожалуйста, запроси доступ у администрации.",
            reply_markup=kb
        )

@dp.message(Command("menu"))
async def menu_command(message: Message):
    user_id = message.from_user.id
    if user_id == OWNER_ID:
        text = (
            "<b>Меню владельца:</b>\n"
            "/add_course — добавить курс\n"
            "/edit_course — редактировать курс\n"
            "/delete_course — удалить курс\n"
            "/add_lesson — добавить урок\n"
            "/delete_lesson — удалить урок\n"
            "/courses — просмотр курсов\n"
            "/menu — показать это меню\n"
        )
    elif user_id in ADMIN_IDS:
        text = (
            "<b>Меню администратора:</b>\n"
            "/courses — просмотр курсов\n"
            "/menu — показать это меню\n"
        )
    else:
        # Проверяем, есть ли пользователь в базе и его роль
        role = check_user_role(user_id)
        if role == "user":
            text = (
                "<b>Меню пользователя:</b>\n"
                "Вам доступен только просмотр курсов.\n"
                "/courses — просмотр курсов\n"
                "/menu — показать это меню\n"
            )
        else:
            text = (
                "У вас нет доступа. Пожалуйста, запросите доступ у администрации."
            )
    await message.answer(text)


class AccessRequest(StatesGroup):
    waiting_for_name = State()
@dp.callback_query(F.data == "request_access")
async def handle_request_access(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Пожалуйста, введите ваше ФИО для запроса доступа:")
    await state.set_state(AccessRequest.waiting_for_name)
    await callback.answer()
@dp.message(AccessRequest.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    fio = message.text.strip()
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name

    await state.update_data(fio=fio, username=username)
    pending_requests[user_id] = {"fio": fio, "username": username}
    kb_1 = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сделать админом", callback_data=f"make_admin_{user_id}")],
        [InlineKeyboardButton(text="Сделать участником", callback_data=f"make_user_{user_id}")],
        [InlineKeyboardButton(text="Отклонить", callback_data=f"decline_{user_id}")]
    ])
    kb_2 = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сделать участником", callback_data=f"make_user_{user_id}")],
        [InlineKeyboardButton(text="Отклонить", callback_data=f"decline_{user_id}")]
    ])
    
    for admin_id in ADMIN_IDS + [OWNER_ID]:
        kb = kb_1 if admin_id == OWNER_ID else kb_2
        await bot.send_message(
            admin_id,
            f"🔔 Запрос на доступ от {fio} (@{username})\nID: <code>{user_id}</code>",
            reply_markup=kb
        )
    await message.answer("✅ Ваш запрос отправлен администрации, дождитесь подтверждения.")
    await state.clear()
@dp.callback_query(F.data.startswith("make_user_"))
async def make_user(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    req = pending_requests.pop(user_id, None)
    fio = req["fio"] if req else "Без ФИО"
    username = req["username"] if req else ""

    add_user_role(user_id, fio, username, "user")
    await bot.send_message(user_id, f"🎉 Поздравляем! Вы в списке учащихся, {fio}.")

    if callback.from_user.id == OWNER_ID:
        await callback.message.answer(f"✅ Вы предоставили доступ пользователю {fio}.")
    else:
        await bot.send_message(OWNER_ID, f"👤 Админ {callback.from_user.full_name} предоставил доступ пользователю {fio}.")
        await callback.message.answer(f"✅ Пользователь {fio} добавлен как участник.")
    await callback.answer()
@dp.callback_query(F.data.startswith("make_admin_"))
async def make_admin(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    req = pending_requests.pop(user_id, None)
    fio = req["fio"] if req else "Без ФИО"
    username = req["username"] if req else ""

    add_user_role(user_id, fio, username, "admin")
    await bot.send_message(user_id, f"🎉 Добро пожаловать в команду, админ {fio}!")

    if callback.from_user.id == OWNER_ID:
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
    waiting_for_lesson_count = State()
    waiting_for_lesson_title = State()
    waiting_for_lesson_video = State()
    waiting_for_homework = State()
    waiting_for_extra_material = State()
@dp.message(Command("add_course"))
async def start_course_creation(message: Message, state: FSMContext):
    if message.from_user.id != OWNER_ID:
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

    lessons.append({"title": message.text.strip(), "video": None, "homework": None, "extra_material": None})
    await state.update_data(lessons=lessons)
    await message.answer("Теперь отправьте видеофайл к этому занятию:")
    await state.set_state(CourseCreation.waiting_for_lesson_video)
@dp.message(CourseCreation.waiting_for_lesson_video, F.video)
async def process_lesson_video(message: Message, state: FSMContext):
    data = await state.get_data()
    lesson_index = data["lesson_index"]
    lessons = data["lessons"]

    lessons[lesson_index]["video"] = message.video.file_id
    await state.update_data(lessons=lessons)
    await message.answer("Теперь отправьте домашнее заданием:")
    await state.set_state(CourseCreation.waiting_for_homework)
@dp.message(CourseCreation.waiting_for_homework)
async def process_homework_text(message: Message, state: FSMContext):
    await state.update_data(homework=message.text.strip())
    await message.answer("Отправьте дополнительный материал в формате .docx (если есть) или напишите «-», чтобы пропустить:")
    await state.set_state(CourseCreation.waiting_for_extra_material)
@dp.message(CourseCreation.waiting_for_extra_material)
async def process_additional_material(message: Message, state: FSMContext):
    if message.text and message.text.strip() == "-":
        await state.update_data(additional_material=None)
        await finalize_homework(message, state)
    elif message.document and message.document.file_name.endswith(".docx"):
        await state.update_data(additional_material=message.document.file_id)
        await finalize_homework(message, state)
    else:
        await message.answer("Пожалуйста, отправьте .docx файл или напишите «-» для пропуска.")
async def finalize_homework(message: Message, state: FSMContext):
    data = await state.get_data()
    lesson_index = data["lesson_index"]
    lessons = data["lessons"]

    # Обновляем текущий урок
    lessons[lesson_index]["homework"] = data.get("homework")
    lessons[lesson_index]["extra_material"] = data.get("additional_material")

    await state.update_data(lessons=lessons)

    # Проверяем, все ли уроки введены
    if lesson_index + 1 < data["lesson_total"]:
        await state.update_data(lesson_index=lesson_index + 1, homework=None, additional_material=None)
        await message.answer(f"Введите название занятия {lesson_index + 2} из {data['lesson_total']}:")
        await state.set_state(CourseCreation.waiting_for_lesson_title)
    else:
        await save_course_to_db(message.from_user.id, state)
        await state.clear()

def get_lesson_buttons(course_id):
    lessons = get_lessons_by_course(course_id)
    return [
        [InlineKeyboardButton(text=f"Урок {i+1}", callback_data=f"view_lesson_{course_id}_{i}")]
        for i in range(len(lessons))
    ]
async def save_course_to_db(user_id: int, state: FSMContext):     
    data = await state.get_data()
    approved = False
    lesson_count = data["lesson_total"]

    course_id = add_course(
        data["title"], data["description"], lesson_count, user_id, approved
    )

    for lesson in data["lessons"]:
        add_lesson(course_id, lesson["title"], lesson["video"], lesson["homework"], lesson["extra_material"])

    await bot.send_message(user_id, f"✅ Курс \"{data['title']}\" сохранён (статус: на модерации).")

    lesson_buttons = get_lesson_buttons(course_id)

    action_buttons = [[
        InlineKeyboardButton(text="✅ Завершить", callback_data=f"approve_course_{course_id}"),
        InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_course_{course_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_course_{course_id}")
    ]]

    markup = InlineKeyboardMarkup(inline_keyboard=lesson_buttons + action_buttons)

    await bot.send_message(
        OWNER_ID,
        "Проверьте созданный курс и завершите создание курса.",
        reply_markup=markup
    )

@dp.callback_query(F.data.startswith("view_lesson_"))
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

    await callback.message.answer(f"<b>Домашнее задание:</b> {lesson.get('homework', '-')}")

    extra = lesson.get("extra_materials") or lesson.get("extra_material")
    if extra:
        try:
            await callback.message.answer_document(extra)
        except Exception:
            await callback.message.answer(f"Доп. материал не найден: {extra}")

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
    if callback.from_user.id != OWNER_ID:  # исправлено!
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
    if message.from_user.id != OWNER_ID:
        await message.answer("Нет доступа.")
        return
    course_id = int(callback.data.split("_")[-1])
    await state.update_data(edit_course_id=course_id)    
    await callback.message.answer("Введите новое название курса:")
    await state.set_state(EditCourse.waiting_for_title)
@dp.callback_query(F.data.regexp(r"^edit_course_desc_\d+$"))
async def edit_course_desc(callback: CallbackQuery, state: FSMContext):
    if message.from_user.id != OWNER_ID:
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
    waiting_for_extra_material = State()
@dp.callback_query(F.data.startswith("add_lesson_"))
async def add_lesson_to_course(callback: CallbackQuery, state: FSMContext):
    user_id = message.from_user.id
    if user_id == OWNER_ID:
        course_id = int(callback.data.split("_")[-1])
        await state.update_data(add_lesson_course_id=course_id)
        await callback.message.edit_text("Введите название нового урока:")
        await state.set_state(AddLesson.waiting_for_title)
    else:
        await callback.message.answer("Нет доступа к этой функции.")
        return

@dp.message(AddLesson.waiting_for_title)
async def add_lesson_title(message: Message, state: FSMContext):
    await state.update_data(new_lesson_title=message.text.strip())
    await message.answer("Отправьте видео для нового урока:")
    await state.set_state(AddLesson.waiting_for_video)
@dp.message(AddLesson.waiting_for_video, F.video)
async def add_lesson_video(message: Message, state: FSMContext):
    await state.update_data(new_lesson_video=message.video.file_id)
    await message.answer("Введите домашнее задание для нового урока:")
    await state.set_state(AddLesson.waiting_for_homework)
@dp.message(AddLesson.waiting_for_homework)
async def add_lesson_homework(message: Message, state: FSMContext):
    await state.update_data(new_lesson_homework=message.text.strip())
    await message.answer("Отправьте дополнительный материал (.docx) или напишите «-», чтобы пропустить:")
    await state.set_state(AddLesson.waiting_for_extra_material)
@dp.message(AddLesson.waiting_for_extra_material)
async def add_lesson_material(message: Message, state: FSMContext):
    data = await state.get_data()
    course_id = data["add_lesson_course_id"]
    title = data["new_lesson_title"]
    video = data["new_lesson_video"]
    homework = data["new_lesson_homework"]
    if message.text and message.text.strip() == "-":
        extra = None
    elif message.document and message.document.file_name.endswith(".docx"):
        extra = message.document.file_id
    else:
        await message.answer("Пожалуйста, отправьте .docx файл или напишите «-».")
        return
    add_lesson(course_id, title, video, homework, extra)
    await message.answer("Новый урок добавлен.")
    await edit_course_menu(message, course_id)
    await state.clear()

class AddLessonGlobal(StatesGroup):
    waiting_for_course = State()
@dp.message(Command("add_lesson"))
async def add_lesson_command(message: Message, state: FSMContext):
    if message.from_user.id != OWNER_ID:
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
    if message.from_user.id != OWNER_ID:
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
    if message.from_user.id != OWNER_ID:
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
    waiting_for_extra_material = State()
@dp.callback_query(F.data.startswith("choose_lesson_edit_"))
async def choose_lesson_edit(callback: CallbackQuery, state: FSMContext):
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
        [InlineKeyboardButton(text="Доп. материал", callback_data=f"edit_lesson_material_{lesson_id}")],
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
@dp.callback_query(F.data.regexp(r"^edit_lesson_material_\d+$"))
async def edit_lesson_material(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Отправьте новый .docx файл или напишите «-», чтобы удалить материал:")
    await state.set_state(EditLesson.waiting_for_extra_material)

class EditCourseGlobal(StatesGroup):
    waiting_for_course = State()
@dp.message(Command("edit_course"))
async def edit_course_command(message: Message, state: FSMContext):
    if message.from_user.id != OWNER_ID:
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
@dp.message(EditLesson.waiting_for_extra_material)
async def update_lesson_material_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    if message.text and message.text.strip() == "-":
        update_lesson_material(data["edit_lesson_id"], None)
        await message.answer("Дополнительный материал удалён.")
    elif message.document and message.document.file_name.endswith(".docx"):
        update_lesson_material(data["edit_lesson_id"], message.document.file_id)
        await message.answer("Дополнительный материал обновлён.")
    else:
        await message.answer("Пожалуйста, отправьте .docx файл или напишите «-» для удаления.")
        return
    await edit_lesson_menu(message, data["edit_lesson_id"], data["edit_course_id"])
    await state.clear()

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    course_id = data.get("edit_course_id")
    await state.clear()
    if course_id:
        course = get_course_by_id(course_id)
        lessons = get_lessons_by_course(course_id)
        lesson_buttons = [
            [InlineKeyboardButton(text=lesson["title"], callback_data=f"view_lesson_simple_{lesson['id']}")]
            for lesson in lessons
        ]
        action_buttons = [[
            InlineKeyboardButton(text="✅ Завершить", callback_data=f"approve_course_{course_id}"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_course_{course_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_course_{course_id}")
        ]]
        kb = InlineKeyboardMarkup(inline_keyboard=lesson_buttons + action_buttons)
        text = (
            f"<b>Курс:</b> {course['title']}\n"
            f"<b>Описание:</b> {course['description']}\n\n"
            "Выберите урок для просмотра или завершите создание курса."
        )
        await callback.message.edit_text(text, reply_markup=kb)
    else:
        await callback.message.edit_text("Главное меню. Используйте команды или кнопки для работы с ботом.")
@dp.callback_query(F.data.regexp(r"^edit_course_\d+$"))
async def back_to_edit_course(callback: CallbackQuery, state: FSMContext):
    course_id = int(callback.data.split("_")[-1])
    await edit_course(callback, state)
@dp.callback_query(F.data.regexp(r"^choose_lesson_edit_\d+$"))

async def back_to_choose_lesson_edit(callback: CallbackQuery, state: FSMContext):
    course_id = int(callback.data.split("_")[-1])
    await choose_lesson_edit(callback, state)

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
        [InlineKeyboardButton(text="Доп. материал", callback_data=f"edit_lesson_material_{lesson_id}")],
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
    if user_id != OWNER_ID and user_id not in ADMIN_IDS:
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
    user_id = callback.from_user.id  # исправлено!
    if user_id != OWNER_ID and user_id not in ADMIN_IDS:
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
    extra = lesson.get("extra_materials") or lesson.get("extra_material")
    if extra:
        try:
            await callback.message.answer_document(extra)
        except Exception:
            text += f"\nДоп. материал не найден: {extra}"
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
    if user_id != OWNER_ID and user_id not in ADMIN_IDS:
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


@dp.callback_query()
async def debug_callback(callback: CallbackQuery):
    print("DEBUG callback.data:", callback.data)
    await callback.answer()

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))