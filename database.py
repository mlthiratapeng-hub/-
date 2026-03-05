import sqlite3
from config import DATABASE_NAME


# =========================
# INIT DATABASE
# =========================

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    # whitelist
    c.execute("""
    CREATE TABLE IF NOT EXISTS whitelist (
        user_id INTEGER PRIMARY KEY
    )
    """)

    # warnings
    c.execute("""
    CREATE TABLE IF NOT EXISTS warnings (
        user_id INTEGER,
        count INTEGER DEFAULT 0
    )
    """)

    # settings
    c.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        guild_id INTEGER PRIMARY KEY,
        anti_link INTEGER DEFAULT 0
    )
    """)

    # logs channel
    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        guild_id INTEGER PRIMARY KEY,
        channel_id INTEGER
    )
    """)

    conn.commit()
    conn.close()


# =========================
# LOG CHANNEL
# =========================

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

    if result:
        return result[0]

    return None


# =========================
# WHITELIST
# =========================

def add_whitelist(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    c.execute(
        "INSERT OR IGNORE INTO whitelist (user_id) VALUES (?)",
        (user_id,)
    )

    conn.commit()
    conn.close()


def remove_whitelist(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    c.execute(
        "DELETE FROM whitelist WHERE user_id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()


def is_whitelisted(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    c.execute(
        "SELECT 1 FROM whitelist WHERE user_id = ?",
        (user_id,)
    )

    result = c.fetchone()

    conn.close()

    return result is not None


# =========================
# WARNINGS
# =========================

def add_warning(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    c.execute(
        "SELECT count FROM warnings WHERE user_id = ?",
        (user_id,)
    )

    data = c.fetchone()

    if data:
        c.execute(
            "UPDATE warnings SET count = count + 1 WHERE user_id = ?",
            (user_id,)
        )
    else:
        c.execute(
            "INSERT INTO warnings (user_id, count) VALUES (?, 1)",
            (user_id,)
        )

    conn.commit()
    conn.close()


def get_warning(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    c.execute(
        "SELECT count FROM warnings WHERE user_id = ?",
        (user_id,)
    )

    data = c.fetchone()

    conn.close()

    if data:
        return data[0]

    return 0


def reset_warning(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    c.execute(
        "DELETE FROM warnings WHERE user_id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()