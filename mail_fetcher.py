"""
mail_fetcher.py — Connects over IMAP and pulls recent emails from the inbox.
"""
import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr

import config


def connect():
    imap = imaplib.IMAP4_SSL(config.IMAP_SERVER)
    imap.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
    return imap


def _decode(value):
    """Decode a possibly-encoded email header (handles non-ASCII subjects/names)."""
    if not value:
        return ""
    parts = decode_header(value)
    decoded_str = ""
    for text, encoding in parts:
        if isinstance(text, bytes):
            decoded_str += text.decode(encoding or "utf-8", errors="ignore")
        else:
            decoded_str += text
    return decoded_str


def _get_body(msg) -> str:
    """Extract the plain-text body from a (possibly multipart) email.message.Message."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in disposition:
                try:
                    return part.get_payload(decode=True).decode(errors="ignore")
                except Exception:
                    continue
        return ""
    try:
        return msg.get_payload(decode=True).decode(errors="ignore")
    except Exception:
        return ""


def fetch_recent_emails(limit=10, unseen_only=True):
    """Return a list of dicts for the most recent emails in INBOX."""
    imap = connect()
    imap.select("INBOX")

    criteria = "UNSEEN" if unseen_only else "ALL"
    status, data = imap.search(None, criteria)
    ids = data[0].split()
    ids = ids[-limit:] if limit else ids

    emails = []
    for eid in reversed(ids):  # newest first
        status, msg_data = imap.fetch(eid, "(RFC822)")
        if status != "OK" or not msg_data or msg_data[0] is None:
            continue
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)

        message_id = msg.get("Message-ID") or f"noid-{eid.decode()}"
        subject = _decode(msg.get("Subject"))
        sender_name, sender_email = parseaddr(msg.get("From"))
        sender_name = _decode(sender_name) or sender_email
        received_date = msg.get("Date", "")
        body = _get_body(msg).strip()

        emails.append({
            "message_id": message_id,
            "sender_name": sender_name,
            "sender_email": sender_email,
            "subject": subject,
            "body": body,
            "received_date": received_date,
        })

    imap.close()
    imap.logout()
    return emails
