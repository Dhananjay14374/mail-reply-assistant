"""
mail_sender.py — Sends a reply email over SMTP.
"""
import smtplib
from email.mime.text import MIMEText

import config


def send_reply(to_email: str, subject: str, body: str, in_reply_to: str = None):
    """Send a plain-text reply. Prefixes 'Re:' on the subject if not already present."""
    msg = MIMEText(body)
    msg["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    msg["From"] = config.EMAIL_ADDRESS
    msg["To"] = to_email
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to

    with smtplib.SMTP_SSL(config.SMTP_SERVER, config.SMTP_PORT) as server:
        server.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
        server.sendmail(config.EMAIL_ADDRESS, [to_email], msg.as_string())
