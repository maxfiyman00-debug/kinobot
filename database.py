import asyncpg
from config import DATABASE_URL

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        if not DATABASE_URL:
            print("ERROR: DATABASE_URL topilmadi. Baza ishlamaydi! .env faylni tekshiring.")
            return
        self.pool = await asyncpg.create_pool(DATABASE_URL)
        await self.create_tables()

    async def create_tables(self):
        async with self.pool.acquire() as conn:
            # Foydalanuvchilar jadvali
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    full_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Kinolar jadvali
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS movies (
                    code TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    file_id TEXT,
                    is_series BOOLEAN DEFAULT FALSE,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Kanallar jadvali (Majburiy obuna uchun)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS channels (
                    channel_id BIGINT PRIMARY KEY,
                    url TEXT,
                    title TEXT
                )
            ''')
            # Qo'shimcha adminlar jadvali
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    user_id BIGINT PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    # --- Foydalanuvchilar ---
    async def add_user(self, user_id: int, full_name: str):
        if not self.pool: return
        async with self.pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO users (id, full_name) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING',
                user_id, full_name
            )

    async def count_users(self):
        if not self.pool: return 0
        async with self.pool.acquire() as conn:
            return await conn.fetchval('SELECT COUNT(*) FROM users')
            
    async def get_all_users(self):
        if not self.pool: return []
        async with self.pool.acquire() as conn:
            return await conn.fetch('SELECT id FROM users')

    # --- Kinolar ---
    async def add_movie(self, code: str, name: str, description: str, file_id: str, is_series: bool = False):
        if not self.pool: return
        async with self.pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO movies (code, name, description, file_id, is_series) VALUES ($1, $2, $3, $4, $5) ON CONFLICT (code) DO UPDATE SET name=$2, description=$3, file_id=$4',
                code, name, description, file_id, is_series
            )

    async def get_movie(self, code: str):
        if not self.pool: return None
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('SELECT * FROM movies WHERE code = $1', code)
            
    async def update_movie_name(self, code: str, new_name: str):
        if not self.pool: return
        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE movies SET name = $1 WHERE code = $2', new_name, code)
            
    async def update_movie_description(self, code: str, new_desc: str):
        if not self.pool: return
        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE movies SET description = $1 WHERE code = $2', new_desc, code)

    async def update_movie_code(self, old_code: str, new_code: str):
        if not self.pool: return
        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE movies SET code = $1 WHERE code = $2', new_code, old_code)

    # --- Kanallar ---
    async def add_channel(self, channel_id: int, url: str, title: str):
        if not self.pool: return
        async with self.pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO channels (channel_id, url, title) VALUES ($1, $2, $3) ON CONFLICT (channel_id) DO NOTHING',
                channel_id, url, title
            )

    async def remove_channel(self, channel_id: int):
        if not self.pool: return
        async with self.pool.acquire() as conn:
            await conn.execute('DELETE FROM channels WHERE channel_id = $1', channel_id)

    async def get_channels(self):
        if not self.pool: return []
        async with self.pool.acquire() as conn:
            return await conn.fetch('SELECT * FROM channels')

    # --- Adminlar ---
    async def add_admin(self, user_id: int):
        if not self.pool: return
        async with self.pool.acquire() as conn:
            await conn.execute('INSERT INTO admins (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING', user_id)

    async def remove_admin(self, user_id: int):
        if not self.pool: return
        async with self.pool.acquire() as conn:
            await conn.execute('DELETE FROM admins WHERE user_id = $1', user_id)

    async def get_admins(self):
        if not self.pool: return []
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('SELECT user_id FROM admins')
            return [row['user_id'] for row in rows]
# Custom funksiyalar
async def add_custom_function(self, name: str, code: str):
    """Yangi custom funksiya qo'shish"""
    if not self.pool: return False
    try:
        async with self.pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO custom_functions (name, code) VALUES ($1, $2)',
                name, code
            )
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def get_custom_function(self, name: str):
    """Custom funksiyani olish"""
    if not self.pool: return None
    async with self.pool.acquire() as conn:
        return await conn.fetchval(
            'SELECT code FROM custom_functions WHERE name = $1 AND is_active = TRUE',
            name
        )

async def get_all_custom_functions(self):
    """Barcha custom funksiyalarni olish"""
    if not self.pool: return []
    async with self.pool.acquire() as conn:
        rows = await conn.fetch('SELECT name, code FROM custom_functions WHERE is_active = TRUE')
        return rows

async def delete_custom_function(self, name: str):
    """Custom funksiyani o'chirish"""
    if not self.pool: return False
    async with self.pool.acquire() as conn:
        await conn.execute('DELETE FROM custom_functions WHERE name = $1', name)
    return True
db = Database()
