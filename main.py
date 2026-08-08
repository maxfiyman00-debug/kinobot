import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import db
from handlers import admin, user

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "bu_yerga_bot_tokenini_yozing":
        print("Bot tokeni kiritilmagan! .env faylni tekshiring.")
        return

    logging.basicConfig(level=logging.INFO)

    bot_props = DefaultBotProperties(parse_mode=ParseMode.HTML)
    bot = Bot(token=BOT_TOKEN, default=bot_props)
    dp = Dispatcher()

    # Baza bilan ulanish
    await db.connect()

    # Routerni ulash
    dp.include_router(admin.router)
    dp.include_router(user.router)

    print("Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
