from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import random
import string

from database import db
from keyboards import main_admin_kb, sub_admin_kb, content_management_kb, settings_kb, cancel_kb, movie_inline_kb
from config import MAIN_ADMIN_ID

router = Router()

class MovieStates(StatesGroup):
    waiting_for_video = State()
    waiting_for_name = State()
    waiting_for_desc = State()

class AdminStates(StatesGroup):
    waiting_for_id_add = State()
    waiting_for_id_remove = State()

class BroadcastStates(StatesGroup):
    waiting_for_msg = State()

async def is_admin(user_id: int):
    if user_id == MAIN_ADMIN_ID:
        return True
    admins = await db.get_admins()
    return user_id in admins

@router.message(Command("admin"))
async def admin_start(message: Message):
    if await is_admin(message.from_user.id):
        if message.from_user.id == MAIN_ADMIN_ID:
            await message.answer("🛡 Asosiy Admin paneliga xush kelibsiz!", reply_markup=main_admin_kb())
        else:
            await message.answer("🛡 Admin paneliga xush kelibsiz!", reply_markup=sub_admin_kb())

@router.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    if message.from_user.id == MAIN_ADMIN_ID:
        await message.answer("Amal bekor qilindi.", reply_markup=main_admin_kb())
    else:
        await message.answer("Amal bekor qilindi.", reply_markup=sub_admin_kb())

@router.message(F.text == "🔙 Orqaga")
async def back_handler(message: Message):
    if message.from_user.id == MAIN_ADMIN_ID:
        await message.answer("Asosiy menyu", reply_markup=main_admin_kb())
    else:
        await message.answer("Asosiy menyu", reply_markup=sub_admin_kb())

# === KONTENT BOSHQARUVI ===
@router.message(F.text == "🎬 Kontent boshqaruvi")
async def content_menu(message: Message):
    if await is_admin(message.from_user.id):
        await message.answer("Kontent boshqaruvi:", reply_markup=content_management_kb())

@router.message(F.text == "📥 Kino yuklash")
async def upload_movie_start(message: Message, state: FSMContext):
    if await is_admin(message.from_user.id):
        await message.answer("Kino (video) faylini yuboring:", reply_markup=cancel_kb())
        await state.set_state(MovieStates.waiting_for_video)

@router.message(MovieStates.waiting_for_video, F.video | F.document)
async def upload_movie_video(message: Message, state: FSMContext):
    file_id = message.video.file_id if message.video else message.document.file_id
    await state.update_data(file_id=file_id)
    await message.answer("Kino nomini yozing:")
    await state.set_state(MovieStates.waiting_for_name)

@router.message(MovieStates.waiting_for_name)
async def upload_movie_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Kino uchun qisqacha tavsif yozing:")
    await state.set_state(MovieStates.waiting_for_desc)

@router.message(MovieStates.waiting_for_desc)
async def upload_movie_desc(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    file_id = data['file_id']
    name = data['name']
    desc = message.text
    
    # 4-6 xonali noyob raqamli kod yaratish
    code = str(random.randint(1000, 99999))
    
    await db.add_movie(code=code, name=name, description=desc, file_id=file_id, is_series=False)
    
    bot_info = await bot.get_me()
    
    caption = f"🎬 Yangi kino yuklandi!\n\n📌 <b>Nom:</b> {name}\n🆔 <b>Kod:</b> {code}\n📝 <b>Tavsif:</b> {desc}"
    await message.answer(caption, reply_markup=movie_inline_kb(bot_info.username, code))
    
    if message.from_user.id == MAIN_ADMIN_ID:
        await message.answer("✅ Kino muvaffaqiyatli saqlandi!", reply_markup=main_admin_kb())
    else:
        await message.answer("✅ Kino muvaffaqiyatli saqlandi!", reply_markup=sub_admin_kb())
    await state.clear()

# === SOZLAMALAR (Faqat Asosiy Admin uchun) ===
@router.message(F.text == "⚙️ Sozlamalar")
async def settings_menu(message: Message):
    if message.from_user.id == MAIN_ADMIN_ID:
        await message.answer("⚙️ Sozlamalar bo'limi:", reply_markup=settings_kb())

@router.message(F.text == "➕ Yangi admin tayinlash")
async def add_admin_start(message: Message, state: FSMContext):
    if message.from_user.id == MAIN_ADMIN_ID:
        await message.answer("Yangi adminning Telegram ID raqamini yuboring:", reply_markup=cancel_kb())
        await state.set_state(AdminStates.waiting_for_id_add)

@router.message(AdminStates.waiting_for_id_add)
async def add_admin_process(message: Message, state: FSMContext):
    try:
        new_id = int(message.text)
        await db.add_admin(new_id)
        await message.answer(f"✅ {new_id} muvaffaqiyatli admin qilib tayinlandi!", reply_markup=main_admin_kb())
        await state.clear()
    except ValueError:
        await message.answer("❌ Faqat raqam yuboring!")

@router.message(F.text == "📊 Statistika")
async def stats_handler(message: Message):
    if await is_admin(message.from_user.id):
        users_count = await db.count_users()
        await message.answer(f"📊 <b>Bot Statistikasi</b>\n\n👥 Jami a'zolar: <b>{users_count}</b> ta")
