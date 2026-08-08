import os
from dotenv import load_dotenv

# .env fayldan ma'lumotlarni o'qiymiz
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MAIN_ADMIN_ID = int(os.getenv("MAIN_ADMIN_ID", "0"))
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not BOT_TOKEN or BOT_TOKEN == "bu_yerga_bot_tokenini_yozing":
    print("DIQQAT: BOT_TOKEN .env faylida kiritilmagan!")
