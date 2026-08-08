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
import asyncio
from database import db

async def execute_custom_function(func_name: str, bot, message):
    """Custom funksiyani dinamik ishga tushirish"""
    func_code = await db.get_custom_function(func_name)
    
    if not func_code:
        await message.answer("❌ Funksiya topilmadi!")
        return
    
    try:
        # Xavfsiz namespace yaratish
        namespace = {
            'bot': bot,
            'message': message,
            'asyncio': asyncio,
        }
        
        # Kodni compile va execute qilish
        exec(func_code, namespace)
        
        # Async funksiyani ishga tushirish
        func = namespace.get(func_name)
        if func and asyncio.iscoroutinefunction(func):
            await func(bot, message)
        else:
            await message.answer("❌ Funksiya topilmadi yoki async emas!")
    
    except Exception as e:
        await message.answer(f"❌ Xato: {str(e)}")
        print(f"Error executing {func_name}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
