import asyncio
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import Message, CallbackQuery

from database import db
from config import MAIN_ADMIN_ID
from keyboards import (
    admin_keyboard, secondary_admin_keyboard,
    settings_keyboard, custom_functions_inline
)

admin_router = Router()

# Oddiy in-memory holat (FSM o'rniga sodda dict; bot qayta ishga tushsa tozalanadi)
user_states: dict[int, str] = {}
temp_data: dict[int, dict] = {}


def is_admin(user_id: int, admins: list[int]) -> bool:
    return user_id == MAIN_ADMIN_ID or user_id in admins


# ---------------------------------------------------------------------------
# KINO QO'SHISH
# ---------------------------------------------------------------------------
@admin_router.message(F.text == "🎬 Kino qo'shish")
async def add_movie_start(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        await message.answer("❌ Siz admin emassiz!")
        return
    user_states[message.from_user.id] = "movie_code"
    temp_data[message.from_user.id] = {}
    await message.answer("🎬 Kino kodini kiriting (masalan: 001):")


# ---------------------------------------------------------------------------
# KINO TAHRIRLASH
# ---------------------------------------------------------------------------
@admin_router.message(F.text == "📝 Kino tahrirlash")
async def edit_movie_start(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        await message.answer("❌ Siz admin emassiz!")
        return
    user_states[message.from_user.id] = "edit_movie_code"
    await message.answer("📝 Tahrirlamoqchi bo'lgan kino kodini kiriting:")


# ---------------------------------------------------------------------------
# BROADCAST
# ---------------------------------------------------------------------------
@admin_router.message(F.text == "📢 Xabar yuborish")
async def broadcast_start(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        await message.answer("❌ Siz admin emassiz!")
        return
    user_states[message.from_user.id] = "broadcast_text"
    await message.answer("📢 Yuboriladigan xabar matnini kiriting:")


# ---------------------------------------------------------------------------
# ADMIN QO'SHISH / O'CHIRISH (faqat MAIN_ADMIN_ID)
# ---------------------------------------------------------------------------
@admin_router.message(F.text == "👨‍💼 Admin qo'shish")
async def add_admin_start(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        await message.answer("❌ Faqat asosiy admin!")
        return
    user_states[message.from_user.id] = "add_admin_id"
    await message.answer("👨‍💼 Yangi admin Telegram ID sini kiriting:")


@admin_router.message(F.text == "👤 Admin o'chirish")
async def remove_admin_start(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        await message.answer("❌ Faqat asosiy admin!")
        return
    user_states[message.from_user.id] = "remove_admin_id"
    await message.answer("👤 O'chiriladigan admin ID sini kiriting:")


# ---------------------------------------------------------------------------
# KANALLAR
# ---------------------------------------------------------------------------
@admin_router.message(F.text == "📺 Kanal qo'shish")
async def add_channel_start(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        await message.answer("❌ Siz admin emassiz!")
        return
    user_states[message.from_user.id] = "channel_id"
    temp_data[message.from_user.id] = {}
    await message.answer(
        "📺 Kanal ID sini kiriting (masalan: -1001234567890):\n"
        "ID ni bilish uchun kanalga bot admin qilib qo'ying va @userinfobot orqali forward qiling."
    )


@admin_router.message(F.text == "❌ Kanal o'chirish")
async def remove_channel_start(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        await message.answer("❌ Siz admin emassiz!")
        return
    user_states[message.from_user.id] = "remove_channel_id"
    await message.answer("❌ O'chiriladigan kanal ID sini kiriting:")


# ---------------------------------------------------------------------------
# STATISTIKA
# ---------------------------------------------------------------------------
@admin_router.message(F.text == "📊 Statistika")
async def statistics(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        await message.answer("❌ Siz admin emassiz!")
        return

    user_count = await db.count_users()
    movies = await db.execute("SELECT COUNT(*) FROM movies")
    movie_count = movies[0][0] if movies else 0
    channels = await db.get_channels()

    text = (
        "📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Foydalanuvchilar: {user_count}\n"
        f"🎬 Kinolar: {movie_count}\n"
        f"📺 Majburiy kanallar: {len(channels)}"
    )
    await message.answer(text)


# ---------------------------------------------------------------------------
# SOZLAMALAR / CUSTOM FUNKSIYALAR (faqat MAIN_ADMIN_ID — xavfsizlik uchun)
# ---------------------------------------------------------------------------
@admin_router.message(F.text == "⚙️ Sozlamalar")
async def settings_menu(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        await message.answer("❌ Faqat asosiy admin!")
        return
    await message.answer("⚙️ <b>Sozlamalar paneli</b>", reply_markup=settings_keyboard)


@admin_router.message(F.text == "🔙 Orqaga")
async def back_to_main(message: Message):
    admins = await db.get_admins()
    user_states.pop(message.from_user.id, None)
    if message.from_user.id == MAIN_ADMIN_ID:
        await message.answer("🏠 Asosiy menyu", reply_markup=admin_keyboard)
    elif message.from_user.id in admins:
        await message.answer("🏠 Asosiy menyu", reply_markup=secondary_admin_keyboard)


@admin_router.message(F.text == "➕ Funksiya qo'shish")
async def add_function_name(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        await message.answer("❌ Faqat asosiy admin!")
        return
    user_states[message.from_user.id] = "waiting_func_name"
    await message.answer("📝 Funksiya nomini kiriting (masalan: custom_broadcast):")


@admin_router.message(F.text == "📋 Funksiyalar ro'yxati")
async def list_functions(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        await message.answer("❌ Faqat asosiy admin!")
        return

    functions = await db.get_all_custom_functions()
    if not functions:
        await message.answer("❌ Hozircha custom funksiyalar yo'q")
        return

    await message.answer(
        "⚙️ <b>Custom funksiyalar</b>\n\nIshga tushirish uchun bosing:",
        reply_markup=custom_functions_inline(functions)
    )


@admin_router.message(F.text == "❌ Funksiya o'chirish")
async def delete_function_start(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        await message.answer("❌ Faqat asosiy admin!")
        return
    user_states[message.from_user.id] = "waiting_delete_func"
    await message.answer("❌ O'chirish uchun funksiya nomini kiriting:")


# ---------------------------------------------------------------------------
# /execute — funksiyani buyruq bilan ishga tushirish
# ---------------------------------------------------------------------------
@admin_router.message(Command("execute"))
async def execute_command(message: Message, bot: Bot):
    if message.from_user.id != MAIN_ADMIN_ID:
        await message.answer("❌ Faqat asosiy admin!")
        return

    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        functions = await db.get_all_custom_functions()
        if not functions:
            await message.answer("❌ Custom funksiyalar yo'q!")
            return
        await message.answer(
            "📋 Funksiyani tanlang:",
            reply_markup=custom_functions_inline(functions)
        )
        return

    await run_custom_function(parts[1].strip(), bot, message)


@admin_router.callback_query(F.data.startswith("exec_"))
async def exec_callback(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != MAIN_ADMIN_ID:
        await callback.answer("❌ Faqat asosiy admin!", show_alert=True)
        return

    func_name = callback.data.replace("exec_", "", 1)
    await run_custom_function(func_name, bot, callback.message)
    await callback.answer(f"✅ '{func_name}' ishga tushirildi")


async def run_custom_function(func_name: str, bot: Bot, message: Message):
    """Custom funksiyani xavfsizroq namespace bilan ishga tushiradi.

    OGOHLANTIRISH: exec() orqali arbitrar kod ishga tushadi. Faqat
    MAIN_ADMIN_ID chaqira oladi (yuqorida tekshirilgan). Boshqa hech kimga
    bu buyruq/tugma ko'rinmaydi va ishlamaydi.
    """
    func_code = await db.get_custom_function(func_name)
    if not func_code:
        await message.answer(f"❌ '{func_name}' funksiyasi topilmadi!")
        return

    safe_builtins = {
        "len": len, "str": str, "int": int, "float": float,
        "range": range, "print": print, "list": list, "dict": dict,
        "enumerate": enumerate,
    }
    namespace = {
        "__builtins__": safe_builtins,
        "bot": bot,
        "message": message,
        "db": db,
        "asyncio": asyncio,
    }

    try:
        exec(func_code, namespace)
        func = namespace.get(func_name)
        if func and asyncio.iscoroutinefunction(func):
            await func(bot, message)
        else:
            await message.answer("❌ Funksiya nomi kod ichidagi funksiya nomi bilan mos emas yoki async emas!")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")
        print(f"Error executing custom function '{func_name}': {e}")


# ---------------------------------------------------------------------------
# UMUMIY TEXT HANDLER — holatga qarab ishlaydi (eng oxirida bo'lishi shart)
# ---------------------------------------------------------------------------
@admin_router.message(F.text)
async def handle_admin_text(message: Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    if not state:
        raise SkipHandler  # boshqa handlerga (user.py) o'tadi

    admins = await db.get_admins()
    if not is_admin(user_id, admins):
        raise SkipHandler

    # ---- KINO QO'SHISH ----
    if state == "movie_code":
        temp_data[user_id]["code"] = message.text.strip()
        user_states[user_id] = "movie_name"
        await message.answer("🎬 Kino nomini kiriting:")

    elif state == "movie_name":
        temp_data[user_id]["name"] = message.text.strip()
        user_states[user_id] = "movie_description"
        await message.answer("📝 Kino tavsifini kiriting:")

    elif state == "movie_description":
        temp_data[user_id]["description"] = message.text.strip()
        user_states[user_id] = "movie_file"
        await message.answer("🎞 Endi kino faylini (video) yuboring:")

    elif state == "edit_movie_code":
        code = message.text.strip()
        movie = await db.get_movie(code)
        if not movie:
            await message.answer("❌ Bunday kodli kino topilmadi!")
            user_states.pop(user_id, None)
            return
        temp_data[user_id] = {"old_code": code}
        user_states[user_id] = "edit_movie_new_name"
        await message.answer(f"Joriy nomi: {movie['name']}\nYangi nomini kiriting (o'zgartirmasa /skip):")

    elif state == "edit_movie_new_name":
        if message.text.strip() != "/skip":
            await db.update_movie_name(temp_data[user_id]["old_code"], message.text.strip())
        user_states[user_id] = "edit_movie_new_desc"
        await message.answer("Yangi tavsifini kiriting (o'zgartirmasa /skip):")

    elif state == "edit_movie_new_desc":
        if message.text.strip() != "/skip":
            await db.update_movie_description(temp_data[user_id]["old_code"], message.text.strip())
        await message.answer("✅ Kino yangilandi!")
        user_states.pop(user_id, None)
        temp_data.pop(user_id, None)

    # ---- BROADCAST ----
    elif state == "broadcast_text":
        temp_data[user_id] = {"text": message.text}
        user_states[user_id] = "broadcast_confirm"
        await message.answer(f"Quyidagi xabar yuborilsinmi?\n\n{message.text}\n\nTasdiqlash uchun /confirm, bekor qilish uchun /cancel")

    elif state == "broadcast_confirm":
        if message.text.strip() == "/confirm":
            users = await db.get_all_users()
            sent = 0
            text = temp_data[user_id]["text"]
            from aiogram import Bot as _Bot  # local import to avoid circulars in some setups
            bot_instance = message.bot
            for u in users:
                try:
                    await bot_instance.send_message(u["id"], text)
                    sent += 1
                except Exception:
                    pass
            await db.log_broadcast(text, sent)
            await message.answer(f"✅ {sent} ta foydalanuvchiga yuborildi!")
        else:
            await message.answer("❌ Bekor qilindi")
        user_states.pop(user_id, None)
        temp_data.pop(user_id, None)

    # ---- ADMIN QO'SHISH/O'CHIRISH ----
    elif state == "add_admin_id":
        try:
            new_admin_id = int(message.text.strip())
            await db.add_admin(new_admin_id)
            await message.answer(f"✅ {new_admin_id} admin qilib qo'shildi!")
        except ValueError:
            await message.answer("❌ Noto'g'ri ID format!")
        user_states.pop(user_id, None)

    elif state == "remove_admin_id":
        try:
            rem_id = int(message.text.strip())
            await db.remove_admin(rem_id)
            await message.answer(f"✅ {rem_id} adminlikdan olindi!")
        except ValueError:
            await message.answer("❌ Noto'g'ri ID format!")
        user_states.pop(user_id, None)

    # ---- KANALLAR ----
    elif state == "channel_id":
        try:
            temp_data[user_id]["channel_id"] = int(message.text.strip())
            user_states[user_id] = "channel_link"
            await message.answer("🔗 Kanal invite linkini kiriting:")
        except ValueError:
            await message.answer("❌ Noto'g'ri ID format!")

    elif state == "channel_link":
        temp_data[user_id]["url"] = message.text.strip()
        user_states[user_id] = "channel_title"
        await message.answer("📛 Kanal nomini kiriting:")

    elif state == "channel_title":
        data = temp_data[user_id]
        await db.add_channel(data["channel_id"], data["url"], message.text.strip())
        await message.answer("✅ Kanal qo'shildi!")
        user_states.pop(user_id, None)
        temp_data.pop(user_id, None)

    elif state == "remove_channel_id":
        try:
            await db.remove_channel(int(message.text.strip()))
            await message.answer("✅ Kanal o'chirildi!")
        except ValueError:
            await message.answer("❌ Noto'g'ri ID format!")
        user_states.pop(user_id, None)

    # ---- CUSTOM FUNKSIYALAR ----
    elif state == "waiting_func_name":
        func_name = message.text.strip()
        user_states[user_id] = f"waiting_func_code:{func_name}"
        await message.answer(
            f"📄 '{func_name}' uchun to'liq Python kodini yuboring.\n\n"
            f"Kod ichida albatta shu nomdagi async funksiya bo'lishi shart:\n"
            f"async def {func_name}(bot, message):\n    ..."
        )

    elif state and state.startswith("waiting_func_code:"):
        func_name = state.split(":", 1)[1]
        success = await db.add_custom_function(func_name, message.text)
        if success:
            await message.answer(f"✅ '{func_name}' funksiya qo'shildi!\nIshga tushirish: /execute {func_name}")
        else:
            await message.answer("❌ Bu nomda funksiya allaqachon bor yoki xato yuz berdi.")
        user_states.pop(user_id, None)

    elif state == "waiting_delete_func":
        func_name = message.text.strip()
        await db.delete_custom_function(func_name)
        await message.answer(f"✅ '{func_name}' o'chirildi!")
        user_states.pop(user_id, None)


# ---------------------------------------------------------------------------
# VIDEO FAYL QABUL QILISH (kino qo'shishning oxirgi bosqichi)
# ---------------------------------------------------------------------------
@admin_router.message(F.video)
async def handle_movie_file(message: Message):
    user_id = message.from_user.id
    if user_states.get(user_id) != "movie_file":
        return

    data = temp_data.get(user_id, {})
    file_id = message.video.file_id

    await db.add_movie(
        code=data.get("code"),
        name=data.get("name"),
        description=data.get("description"),
        file_id=file_id,
    )
    await message.answer(f"✅ Kino qo'shildi! Kod: {data.get('code')}")
    user_states.pop(user_id, None)
    temp_data.pop(user_id, None)
