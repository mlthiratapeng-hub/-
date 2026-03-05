import sqlite3
from config import DATABASE_NAME

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS whitelist (user_id INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS warnings (user_id INTEGER, count INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS settings (guild_id INTEGER, anti_link INTEGER DEFAULT 0)")

    conn.commit()
    conn.close()

def add_whitelist(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO whitelist VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def remove_whitelist(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM whitelist WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def is_whitelisted(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM whitelist WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None