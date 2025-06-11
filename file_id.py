from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.types import ReplyKeyboardRemove
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
import asyncio
import logging
from config import BOT_TOKEN, OWNER_ID, ADMIN_IDS



bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Отправь мне файл, и я пришлю его file_id.", reply_markup=ReplyKeyboardRemove())

@dp.message()
async def file_id_handler(message: Message):
    if message.document:
        await message.answer(f"`{message.document.file_id}`", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer("Это не документ.")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
