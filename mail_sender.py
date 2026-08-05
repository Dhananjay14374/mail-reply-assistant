"""
mail_sender.py — Sends a reply email over SMTP.
"""
import smtplib
from email.mime.text import MIMEText

import config


def send_reply(to_email: str, subject: str, body: str, in_reply_to: str = None,
                email_address: str = None, email_password: str = None,
                smtp_server: str = None, smtp_port: int = None):
    """Send a plain-text reply. Prefixes 'Re:' on the subject if not already present.
    Falls back to .env values (config.py) only if credentials aren't explicitly passed."""
    email_address = email_address or config.EMAIL_ADDRESS
    email_password = email_password or config.EMAIL_PASSWORD
    smtp_server = smtp_server or config.SMTP_SERVER
    smtp_port = smtp_port or config.SMTP_PORT

    msg = MIMEText(body)
    msg["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    msg["From"] = email_address
    msg["To"] = to_email
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to

    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(email_address, email_password)
        server.sendmail(email_address, [to_email], msg.as_string())
