import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import Message, CallbackQuery

from database import db
from config import MAIN_ADMIN_ID
from keyboards import (
    main_admin_kb, sub_admin_kb, content_management_kb,
    settings_kb, cancel_kb, channels_kb, custom_functions_inline
)

admin_router = Router()

# Oddiy in-memory holat (bot qayta ishga tushsa tozalanadi)
user_states: dict[int, str] = {}
temp_data: dict[int, dict] = {}


def is_admin(user_id: int, admins: list[int]) -> bool:
    return user_id == MAIN_ADMIN_ID or user_id in admins


def menu_kb(user_id: int, admins: list[int]):
    return main_admin_kb() if user_id == MAIN_ADMIN_ID else sub_admin_kb()


async def reset_state(message: Message):
    user_id = message.from_user.id
    user_states.pop(user_id, None)
    temp_data.pop(user_id, None)
    admins = await db.get_admins()
    await message.answer("🏠 Asosiy menyu", reply_markup=menu_kb(user_id, admins))


# ---------------------------------------------------------------------------
# BEKOR QILISH (istalgan input jarayonida ishlaydi)
# ---------------------------------------------------------------------------
@admin_router.message(F.text == "❌ Bekor qilish")
async def cancel_action(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        raise SkipHandler
    await message.answer("❌ Bekor qilindi")
    await reset_state(message)


# ---------------------------------------------------------------------------
# ASOSIY MENYU -> BO'LIMLAR
# ---------------------------------------------------------------------------
@admin_router.message(F.text == "🎬 Kontent boshqaruvi")
async def content_menu(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        raise SkipHandler
    user_states.pop(message.from_user.id, None)
    await message.answer("🎬 Kontent boshqaruvi", reply_markup=content_management_kb())


@admin_router.message(F.text == "📣 Kanallar")
async def channels_menu(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        raise SkipHandler
    user_states.pop(message.from_user.id, None)
    await message.answer("📣 Kanallar boshqaruvi", reply_markup=channels_kb())


@admin_router.message(F.text == "⚙️ Sozlamalar")
async def settings_menu(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        raise SkipHandler
    user_states.pop(message.from_user.id, None)
    await message.answer("⚙️ Sozlamalar", reply_markup=settings_kb())


@admin_router.message(F.text == "🔙 Orqaga")
async def back_to_main(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        raise SkipHandler
    await reset_state(message)


@admin_router.message(F.text == "📊 Statistika")
async def statistics(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        raise SkipHandler

    user_count = await db.count_users()
    movies = await db.execute("SELECT COUNT(*) FROM movies")
    movie_count = movies[0][0] if movies else 0
    channels = await db.get_channels()

    text = (
        "📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Foydalanuvchilar: {user_count}\n"
        f"🎬 Kinolar/seriallar: {movie_count}\n"
        f"📣 Majburiy kanallar: {len(channels)}"
    )
    await message.answer(text)


# ---------------------------------------------------------------------------
# KONTENT BOSHQARUVI: Kino/Serial yuklash
# ---------------------------------------------------------------------------
@admin_router.message(F.text.in_(["📥 Kino yuklash", "📺 Serial yuklash"]))
async def add_content_start(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        raise SkipHandler

    is_series = message.text == "📺 Serial yuklash"
    user_states[message.from_user.id] = "content_code"
    temp_data[message.from_user.id] = {"is_series": is_series}
    label = "Serial" if is_series else "Kino"
    await message.answer(f"{label} kodini kiriting:", reply_markup=cancel_kb())


@admin_router.message(F.text == "✏️ Kod tahrirlash")
async def edit_code_start(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        raise SkipHandler
    user_states[message.from_user.id] = "edit_code_old"
    await message.answer("Joriy (eski) kodni kiriting:", reply_markup=cancel_kb())


@admin_router.message(F.text == "📝 Tavsif tahrirlash")
async def edit_desc_start(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        raise SkipHandler
    user_states[message.from_user.id] = "edit_desc_code"
    await message.answer("Tavsifini o'zgartirmoqchi bo'lgan kino/serial kodini kiriting:", reply_markup=cancel_kb())


@admin_router.message(F.text == "🏷 Nomini tahrirlash")
async def edit_name_start(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        raise SkipHandler
    user_states[message.from_user.id] = "edit_name_code"
    await message.answer("Nomini o'zgartirmoqchi bo'lgan kino/serial kodini kiriting:", reply_markup=cancel_kb())


# ---------------------------------------------------------------------------
# KANALLAR
# ---------------------------------------------------------------------------
@admin_router.message(F.text == "➕ Kanal qo'shish")
async def add_channel_start(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        raise SkipHandler
    user_states[message.from_user.id] = "channel_id"
    temp_data[message.from_user.id] = {}
    await message.answer(
        "Kanal ID sini kiriting (masalan: -1001234567890):\n"
        "Bot kanalda admin bo'lishi shart.",
        reply_markup=cancel_kb()
    )


@admin_router.message(F.text == "➖ Kanal o'chirish")
async def remove_channel_start(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        raise SkipHandler
    user_states[message.from_user.id] = "remove_channel_id"
    await message.answer("O'chiriladigan kanal ID sini kiriting:", reply_markup=cancel_kb())


@admin_router.message(F.text == "📋 Kanallar ro'yxati")
async def list_channels(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        raise SkipHandler
    channels = await db.get_channels()
    if not channels:
        await message.answer("❌ Hozircha majburiy kanallar yo'q")
        return
    text = "📣 <b>Majburiy kanallar</b>\n\n" + "\n".join(
        f"• {ch['title']} — <code>{ch['channel_id']}</code>" for ch in channels
    )
    await message.answer(text)


# ---------------------------------------------------------------------------
# XABAR YUBORISH (BROADCAST)
# ---------------------------------------------------------------------------
@admin_router.message(F.text == "✉️ Xabar yuborish")
async def broadcast_start(message: Message):
    admins = await db.get_admins()
    if not is_admin(message.from_user.id, admins):
        raise SkipHandler
    user_states[message.from_user.id] = "broadcast_text"
    await message.answer("Yuboriladigan xabar matnini kiriting:", reply_markup=cancel_kb())


# ---------------------------------------------------------------------------
# SOZLAMALAR: Admin qo'shish/o'chirish (faqat MAIN_ADMIN_ID)
# ---------------------------------------------------------------------------
@admin_router.message(F.text == "➕ Yangi admin tayinlash")
async def add_admin_start(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        raise SkipHandler
    user_states[message.from_user.id] = "add_admin_id"
    await message.answer("Yangi admin Telegram ID sini kiriting:", reply_markup=cancel_kb())


@admin_router.message(F.text == "➖ Adminni o'chirish")
async def remove_admin_start(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        raise SkipHandler
    user_states[message.from_user.id] = "remove_admin_id"
    await message.answer("O'chiriladigan admin ID sini kiriting:", reply_markup=cancel_kb())


# ---------------------------------------------------------------------------
# CUSTOM FUNKSIYALAR — faqat buyruqlar orqali (MAIN_ADMIN_ID)
# ---------------------------------------------------------------------------
@admin_router.message(Command("addfunction"))
async def add_function_cmd(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Foydalanish: /addfunction funksiya_nomi")
        return
    user_states[message.from_user.id] = f"waiting_func_code:{parts[1].strip()}"
    await message.answer(
        f"'{parts[1].strip()}' uchun to'liq Python kodini yuboring.\n"
        f"Kod ichida shu nomdagi async funksiya bo'lishi shart:\n"
        f"async def {parts[1].strip()}(bot, message):\n    ...",
        reply_markup=cancel_kb()
    )


@admin_router.message(Command("listfunctions"))
async def list_functions_cmd(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        return
    functions = await db.get_all_custom_functions()
    if not functions:
        await message.answer("❌ Custom funksiyalar yo'q")
        return
    await message.answer("📋 Funksiyalar:", reply_markup=custom_functions_inline(functions))


@admin_router.message(Command("delfunction"))
async def del_function_cmd(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Foydalanish: /delfunction funksiya_nomi")
        return
    await db.delete_custom_function(parts[1].strip())
    await message.answer(f"✅ '{parts[1].strip()}' o'chirildi")


@admin_router.message(Command("execute"))
async def execute_command(message: Message, bot: Bot):
    if message.from_user.id != MAIN_ADMIN_ID:
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        functions = await db.get_all_custom_functions()
        if not functions:
            await message.answer("❌ Custom funksiyalar yo'q!")
            return
        await message.answer("📋 Funksiyani tanlang:", reply_markup=custom_functions_inline(functions))
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
    """OGOHLANTIRISH: exec() orqali arbitrar kod ishga tushadi.
    Faqat MAIN_ADMIN_ID chaqira oladi (yuqorida tekshirilgan)."""
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

    # ---- KINO/SERIAL QO'SHISH ----
    if state == "content_code":
        temp_data[user_id]["code"] = message.text.strip()
        user_states[user_id] = "content_name"
        await message.answer("Nomini kiriting:", reply_markup=cancel_kb())

    elif state == "content_name":
        temp_data[user_id]["name"] = message.text.strip()
        user_states[user_id] = "content_description"
        await message.answer("Tavsifini kiriting:", reply_markup=cancel_kb())

    elif state == "content_description":
        temp_data[user_id]["description"] = message.text.strip()
        user_states[user_id] = "content_file"
        await message.answer("Endi video faylni yuboring:", reply_markup=cancel_kb())

    # ---- KOD TAHRIRLASH ----
    elif state == "edit_code_old":
        code = message.text.strip()
        movie = await db.get_movie(code)
        if not movie:
            await message.answer("❌ Bunday kodli kontent topilmadi!")
            await reset_state(message)
            return
        temp_data[user_id] = {"old_code": code}
        user_states[user_id] = "edit_code_new"
        await message.answer("Yangi kodni kiriting:", reply_markup=cancel_kb())

    elif state == "edit_code_new":
        await db.update_movie_code(temp_data[user_id]["old_code"], message.text.strip())
        await message.answer("✅ Kod yangilandi!")
        await reset_state(message)

    # ---- TAVSIF TAHRIRLASH ----
    elif state == "edit_desc_code":
        code = message.text.strip()
        movie = await db.get_movie(code)
        if not movie:
            await message.answer("❌ Bunday kodli kontent topilmadi!")
            await reset_state(message)
            return
        temp_data[user_id] = {"code": code}
        user_states[user_id] = "edit_desc_new"
        await message.answer("Yangi tavsifni kiriting:", reply_markup=cancel_kb())

    elif state == "edit_desc_new":
        await db.update_movie_description(temp_data[user_id]["code"], message.text.strip())
        await message.answer("✅ Tavsif yangilandi!")
        await reset_state(message)

    # ---- NOMINI TAHRIRLASH ----
    elif state == "edit_name_code":
        code = message.text.strip()
        movie = await db.get_movie(code)
        if not movie:
            await message.answer("❌ Bunday kodli kontent topilmadi!")
            await reset_state(message)
            return
        temp_data[user_id] = {"code": code}
        user_states[user_id] = "edit_name_new"
        await message.answer("Yangi nomni kiriting:", reply_markup=cancel_kb())

    elif state == "edit_name_new":
        await db.update_movie_name(temp_data[user_id]["code"], message.text.strip())
        await message.answer("✅ Nomi yangilandi!")
        await reset_state(message)

    # ---- BROADCAST ----
    elif state == "broadcast_text":
        temp_data[user_id] = {"text": message.text}
        user_states[user_id] = "broadcast_confirm"
        await message.answer(
            f"Quyidagi xabar yuborilsinmi?\n\n{message.text}\n\n"
            f"Tasdiqlash uchun /confirm, bekor qilish uchun ❌ Bekor qilish tugmasini bosing."
        )

    elif state == "broadcast_confirm":
        if message.text.strip() == "/confirm":
            users = await db.get_all_users()
            sent = 0
            text = temp_data[user_id]["text"]
            for u in users:
                try:
                    await message.bot.send_message(u["id"], text)
                    sent += 1
                except Exception:
                    pass
            await db.log_broadcast(text, sent)
            await message.answer(f"✅ {sent} ta foydalanuvchiga yuborildi!")
            await reset_state(message)

    # ---- ADMIN QO'SHISH/O'CHIRISH ----
    elif state == "add_admin_id":
        try:
            new_admin_id = int(message.text.strip())
            await db.add_admin(new_admin_id)
            await message.answer(f"✅ {new_admin_id} admin qilib qo'shildi!")
        except ValueError:
            await message.answer("❌ Noto'g'ri ID format!")
        await reset_state(message)

    elif state == "remove_admin_id":
        try:
            rem_id = int(message.text.strip())
            await db.remove_admin(rem_id)
            await message.answer(f"✅ {rem_id} adminlikdan olindi!")
        except ValueError:
            await message.answer("❌ Noto'g'ri ID format!")
        await reset_state(message)

    # ---- KANALLAR ----
    elif state == "channel_id":
        try:
            temp_data[user_id]["channel_id"] = int(message.text.strip())
            user_states[user_id] = "channel_link"
            await message.answer("Kanal invite linkini kiriting:", reply_markup=cancel_kb())
        except ValueError:
            await message.answer("❌ Noto'g'ri ID format!")

    elif state == "channel_link":
        temp_data[user_id]["url"] = message.text.strip()
        user_states[user_id] = "channel_title"
        await message.answer("Kanal nomini kiriting:", reply_markup=cancel_kb())

    elif state == "channel_title":
        data = temp_data[user_id]
        await db.add_channel(data["channel_id"], data["url"], message.text.strip())
        await message.answer("✅ Kanal qo'shildi!")
        await reset_state(message)

    elif state == "remove_channel_id":
        try:
            await db.remove_channel(int(message.text.strip()))
            await message.answer("✅ Kanal o'chirildi!")
        except ValueError:
            await message.answer("❌ Noto'g'ri ID format!")
        await reset_state(message)

    # ---- CUSTOM FUNKSIYA KODI ----
    elif state.startswith("waiting_func_code:"):
        func_name = state.split(":", 1)[1]
        success = await db.add_custom_function(func_name, message.text)
        if success:
            await message.answer(f"✅ '{func_name}' funksiya qo'shildi!\nIshga tushirish: /execute {func_name}")
        else:
            await message.answer("❌ Bu nomda funksiya allaqachon bor yoki xato yuz berdi.")
        user_states.pop(user_id, None)


# ---------------------------------------------------------------------------
# VIDEO FAYL QABUL QILISH (kino/serial qo'shishning oxirgi bosqichi)
# ---------------------------------------------------------------------------
@admin_router.message(F.video)
async def handle_content_file(message: Message):
    user_id = message.from_user.id
    if user_states.get(user_id) != "content_file":
        return

    data = temp_data.get(user_id, {})
    file_id = message.video.file_id

    await db.add_movie(
        code=data.get("code"),
        name=data.get("name"),
        description=data.get("description"),
        file_id=file_id,
        is_series=data.get("is_series", False),
    )
    label = "Serial" if data.get("is_series") else "Kino"
    await message.answer(f"✅ {label} qo'shildi! Kod: {data.get('code')}")
    await reset_state(message)
