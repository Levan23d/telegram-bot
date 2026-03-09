import sqlite3

from config import CRM_DB


def init_crm_db():
    conn = sqlite3.connect(CRM_DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS fans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            model_name TEXT,
            interests TEXT,
            notes TEXT,
            total_spent REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fan_id INTEGER,
            item_name TEXT,
            amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fan_id) REFERENCES fans(id)
        )
    """)

    conn.commit()
    conn.close()


def add_fan_db(username, model_name, interests, notes):
    conn = sqlite3.connect(CRM_DB)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO fans (username, model_name, interests, notes)
        VALUES (?, ?, ?, ?)
        """,
        (username, model_name, interests, notes)
    )

    conn.commit()
    fan_id = cur.lastrowid
    conn.close()
    return fan_id


def add_purchase_db(fan_id, item_name, amount):
    conn = sqlite3.connect(CRM_DB)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO purchases (fan_id, item_name, amount)
        VALUES (?, ?, ?)
        """,
        (fan_id, item_name, amount)
    )

    cur.execute(
        """
        UPDATE fans
        SET total_spent = total_spent + ?
        WHERE id = ?
        """,
        (amount, fan_id)
    )

    conn.commit()
    conn.close()


def fan_exists(fan_id):
    conn = sqlite3.connect(CRM_DB)
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM fans WHERE id = ?", (fan_id,))
    row = cur.fetchone()

    conn.close()
    return row is not None


def get_fan_by_id(fan_id):
    conn = sqlite3.connect(CRM_DB)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, username, model_name, interests, notes, total_spent, created_at
        FROM fans
        WHERE id = ?
        """,
        (fan_id,)
    )
    row = cur.fetchone()

    conn.close()
    return row


def search_fans(query):
    conn = sqlite3.connect(CRM_DB)
    cur = conn.cursor()

    q = query.strip().lower()
    results = []

    if q.isdigit():
        cur.execute(
            """
            SELECT id, username, model_name, interests, notes, total_spent, created_at
            FROM fans
            WHERE id = ?
            """,
            (int(q),)
        )
        row = cur.fetchone()
        if row:
            results.append(row)
    else:
        q_no_at = q.lstrip("@")
        cur.execute(
            """
            SELECT id, username, model_name, interests, notes, total_spent, created_at
            FROM fans
            WHERE lower(username) LIKE ?
               OR lower(replace(username, '@', '')) LIKE ?
            ORDER BY id DESC
            """,
            (f"%{q}%", f"%{q_no_at}%")
        )
        results = cur.fetchall()

    conn.close()
    return results


def resolve_fan_id(query):
    q = query.strip()

    if q.isdigit():
        fan = get_fan_by_id(int(q))
        if fan:
            return fan[0]
        return None

    results = search_fans(q)
    if not results:
        return None

    return results[0][0]


def get_crm_stats():
    conn = sqlite3.connect(CRM_DB)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM fans")
    fans_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM purchases")
    purchases_count = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(total_spent), 0) FROM fans")
    total_sum = cur.fetchone()[0]

    conn.close()
    return fans_count, purchases_count, total_sum
