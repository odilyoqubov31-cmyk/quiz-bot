import sqlite3

def init_db():
    conn = sqlite3.connect("quiz_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            score INTEGER DEFAULT 0,
            stars INTEGER DEFAULT 0,
            referred_by INTEGER
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id, name, referred_by=None):
    conn = sqlite3.connect("quiz_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute(
            "INSERT INTO users (user_id, name, referred_by) VALUES (?, ?, ?)",
            (user_id, name, referred_by)
        )
        conn.commit()
        conn.close()
        return True  # Yangi foydalanuvchi
    conn.close()
    return False  # Avval bor edi

def get_user(user_id):
    conn = sqlite3.connect("quiz_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name, score, stars FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_points(user_id, score_add=0, stars_add=0):
    conn = sqlite3.connect("quiz_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users 
        SET score = score + ?, stars = stars + ? 
        WHERE user_id = ?
    """, (score_add, stars_add, user_id))
    conn.commit()
    conn.close()

def get_top_users(limit=5):
    conn = sqlite3.connect("quiz_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, score, stars FROM users ORDER BY score DESC LIMIT ?", (limit,))
    top = cursor.fetchall()
    conn.close()
    return top
