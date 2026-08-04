"""
config.py — Loads mail account settings from a local .env file.

Never hardcode credentials in code. Copy .env.example to .env and fill in
your own values; .env is git-ignored so your password never gets committed.
"""
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")  # Gmail: use an App Password, not your normal password

IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))


def is_configured() -> bool:
    return bool(EMAIL_ADDRESS and EMAIL_PASSWORD)
