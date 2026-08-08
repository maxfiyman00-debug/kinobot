from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, CommandObject

from database import db
from keyboards import user_main_kb, subscribe_kb
from config import MAIN_ADMIN_ID

router = Router()


async def check_subscription(bot: Bot, user_id: int):
    """Foydalanuvchi barcha majburiy kanallarga obuna bo'lganini tekshiradi.
    Obuna bo'lmagan kanallar ro'yxatini qaytaradi."""
    channels = await db.get_channels()
    unsubscribed = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch['channel_id'], user_id=user_id)
            if member.status in ['left', 'kicked']:
                unsubscribed.append(ch)
        except Exception:
            # Bot kanalda admin emas yoki kanal ID noto'g'ri — adminga xabar beramiz
            try:
                await bot.send_message(
                    MAIN_ADMIN_ID,
                    f"⚠️ <b>DIQQAT! Kanalni tekshirishda xatolik yuz berdi!</b>\n\n"
                    f"📢 Kanal: {ch['title']} ({ch['url']})\n"
                    f"❌ Xatolik: Bot kanalda admin emas yoki havola eskirgan.\n"
                    f"Iltimos, tekshirib ko'ring!"
                )
            except Exception:
                pass
    return unsubscribed


@router.message(CommandStart())
async def start_cmd(message: Message, command: CommandObject, bot: Bot):
    await db.add_user(message.from_user.id, message.from_user.full_name)

    movie_code = command.args

    unsubscribed = await check_subscription(bot, message.from_user.id)
    if unsubscribed:
        text = "Filmni ko'rish yoki botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:"
        if movie_code:
            text += "\n\n<i>Obuna bo'lgach, kinoni ko'rish uchun yana havolaga kiring yoki kodni yuboring!</i>"
        await message.answer(text, reply_markup=subscribe_kb(unsubscribed))
        return

    if movie_code:
        movie = await db.get_movie(movie_code)
        if movie:
            caption = f"🎬 <b>{movie['name']}</b>\n\n📝 {movie['description']}\n\n🆔 Kod: <b>{movie['code']}</b>"
            try:
                await message.answer_video(video=movie['file_id'], caption=caption)
            except Exception:
                await message.answer_document(document=movie['file_id'], caption=caption)
        else:
            await message.answer("❌ Bunday kodli kino topilmadi.")
    else:
        await message.answer(
            "Xush kelibsiz! Kinolarni qidirish uchun kodni yuboring yoki quyidagi tugmadan foydalaning.",
            reply_markup=user_main_kb()
        )


@router.callback_query(F.data == "check_sub")
async def check_sub_callback(call: CallbackQuery, bot: Bot):
    unsubscribed = await check_subscription(bot, call.from_user.id)
    if unsubscribed:
        await call.answer("Hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
    else:
        await call.message.delete()
        await call.message.answer("✅ Obuna tasdiqlandi! Kino kodini yuborishingiz mumkin.", reply_markup=user_main_kb())


@router.message(F.text == "🔍 Kino qidirish")
async def search_btn(message: Message):
    await message.answer("Kino kodini yuboring:")


@router.message(F.text)
async def search_movie(message: Message, bot: Bot):
    if message.text.startswith('/'):
        return

    if message.text.isdigit():
        unsubscribed = await check_subscription(bot, message.from_user.id)
        if unsubscribed:
            await message.answer("Botdan foydalanish uchun kanallarga obuna bo'ling:", reply_markup=subscribe_kb(unsubscribed))
            return
        movie = await db.get_movie(message.text.strip())
        if movie:
            caption = f"🎬 <b>{movie['name']}</b>\n\n📝 {movie['description']}\n\n🆔 Kod: <b>{movie['code']}</b>"
            try:
                await message.answer_video(video=movie['file_id'], caption=caption)
            except Exception:
                await message.answer_document(document=movie['file_id'], caption=caption)
        else:
            await message.answer("❌ Bunday kodli kino topilmadi.")
