import sqlite3
from config import DATABASE_NAME


def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    # whitelist
    c.execute("CREATE TABLE IF NOT EXISTS whitelist (user_id INTEGER)")

    # warnings
    c.execute("CREATE TABLE IF NOT EXISTS warnings (user_id INTEGER, count INTEGER)")

    # settings
    c.execute("CREATE TABLE IF NOT EXISTS settings (guild_id INTEGER, anti_link INTEGER DEFAULT 0)")

    # logs channel
    c.execute("CREATE TABLE IF NOT EXISTS logs (guild_id INTEGER PRIMARY KEY, channel_id INTEGER)")

    conn.commit()
    conn.close()


# ======================
# LOG CHANNEL
# ======================

def set_log_channel(guild_id, channel_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    c.execute(
        "INSERT OR REPLACE INTO logs (guild_id, channel_id) VALUES (?, ?)",
        (guild_id, channel_id)
    )

    conn.commit()
    conn.close()


def get_log_channel(guild_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    c.execute(
        "SELECT channel_id FROM logs WHERE guild_id = ?",
        (guild_id,)
    )

    result = c.fetchone()
    conn.close()

    return result[0] if result else None


# ======================
# WHITELIST
# ======================

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