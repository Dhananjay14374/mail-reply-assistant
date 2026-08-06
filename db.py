"""
db.py — SQLite data layer for the Mail Reply Assistant.
"""
import sqlite3

DB_PATH = "mail_assistant.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_email TEXT,
            message_id TEXT,
            sender_name TEXT,
            sender_email TEXT,
            subject TEXT,
            body TEXT,
            received_date TEXT,
            intent TEXT,
            suggested_reply TEXT,
            status TEXT DEFAULT 'pending',   -- pending | replied | skipped
            fetched_at TEXT DEFAULT (datetime('now')),
            UNIQUE(account_email, message_id)
        )
    """)
    # Lightweight migration for databases created before account_email existed.
    try:
        conn.execute("ALTER TABLE emails ADD COLUMN account_email TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.commit()
    conn.close()


def save_email(account_email, message_id, sender_name, sender_email, subject, body,
                received_date, intent, suggested_reply):
    """Insert a new email. Ignored silently if (account_email, message_id) already
    exists — keeps re-checking mail from creating duplicates."""
    conn = get_connection()
    conn.execute("""
        INSERT OR IGNORE INTO emails
            (account_email, message_id, sender_name, sender_email, subject, body,
             received_date, intent, suggested_reply)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (account_email, message_id, sender_name, sender_email, subject, body,
          received_date, intent, suggested_reply))
    conn.commit()
    conn.close()


def get_emails(account_email, status=None):
    """Return emails belonging only to the given account_email."""
    conn = get_connection()
    if status:
        rows = conn.execute(
            "SELECT * FROM emails WHERE account_email=? AND status=? ORDER BY id DESC",
            (account_email, status),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM emails WHERE account_email=? ORDER BY id DESC",
            (account_email,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_reply_text(email_id, new_reply):
    conn = get_connection()
    conn.execute("UPDATE emails SET suggested_reply=? WHERE id=?", (new_reply, email_id))
    conn.commit()
    conn.close()


def mark_status(email_id, status):
    conn = get_connection()
    conn.execute("UPDATE emails SET status=? WHERE id=?", (status, email_id))
    conn.commit()
    conn.close()


def delete_email(email_id):
    conn = get_connection()
    conn.execute("DELETE FROM emails WHERE id=?", (email_id,))
    conn.commit()
    conn.close()
