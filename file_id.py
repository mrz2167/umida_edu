from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, OWNER_ID, ADMIN_IDS

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)  # <<< вот это нужно
ADMIN_ID = 6774411424

@router.message(F.document | F.video | F.photo)
async def catch_files(message: Message):
    if message.document:
        file_id = message.document.file_id
        file_type = "📄 Документ"
    elif message.video:
        file_id = message.video.file_id
        file_type = "🎥 Видео"
    else:
        file_id = message.photo[-1].file_id
        file_type = "🖼 Фото"

    await message.send_copy(ADMIN_ID)

    await message.bot.send_message(
        ADMIN_ID,
        f"{file_type} получен от @{message.from_user.username or message.from_user.full_name}\n<b>File ID:</b>\n<code>{file_id}</code>",
        parse_mode="HTML"
    )

    await message.answer("✅ Файл принят и отправлен админу.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
