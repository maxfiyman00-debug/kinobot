from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_admin_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Kontent boshqaruvi")],
            [KeyboardButton(text="📣 Kanallar"), KeyboardButton(text="✉️ Xabar yuborish")],
            [KeyboardButton(text="⚙️ Sozlamalar"), KeyboardButton(text="📊 Statistika")]
        ],
        resize_keyboard=True
    )


def sub_admin_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Kontent boshqaruvi")],
            [KeyboardButton(text="📣 Kanallar"), KeyboardButton(text="✉️ Xabar yuborish")],
            [KeyboardButton(text="📊 Statistika")]
        ],
        resize_keyboard=True
    )


def content_management_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Kino yuklash"), KeyboardButton(text="📺 Serial yuklash")],
            [KeyboardButton(text="✏️ Kod tahrirlash"), KeyboardButton(text="📝 Tavsif tahrirlash")],
            [KeyboardButton(text="🏷 Nomini tahrirlash")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )


def settings_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Yangi admin tayinlash"), KeyboardButton(text="➖ Adminni o'chirish")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )


def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )


def user_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔍 Kino qidirish")]],
        resize_keyboard=True
    )


def subscribe_kb(channels):
    buttons = []
    for idx, channel in enumerate(channels):
        buttons.append([InlineKeyboardButton(text=f"➕ {idx+1}-kanalga obuna bo'lish", url=channel['url'])])
    buttons.append([InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def movie_inline_kb(bot_username: str, movie_code: str):
    url = f"https://t.me/{bot_username}?start={movie_code}"
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="▶️ Kinoni ko'rish", url=url)]]
    )


# --- Quyidagilar sizning ro'yxatingizda yo'q edi, lekin admin.py'da kerak bo'lgani
#     uchun qo'shildi (nomlaringizga tegilmadi, faqat yangi funksiyalar qo'shildi) ---

def channels_kb():
    """'📣 Kanallar' bosilganda ochiladigan submenu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Kanal qo'shish"), KeyboardButton(text="➖ Kanal o'chirish")],
            [KeyboardButton(text="📋 Kanallar ro'yxati")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )


def custom_functions_inline(functions):
    """Custom funksiyalarni /execute buyrug'i orqali ro'yxatlash uchun."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"▶️ {f['name']}", callback_data=f"exec_{f['name']}")]
            for f in functions
        ]
    )
