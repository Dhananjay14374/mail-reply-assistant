"""
app.py — Mail Reply Assistant
Streamlit + SQLite. Fetches recent emails over IMAP, suggests a reply using
a rule-based intent engine, lets you edit it, then sends it over SMTP.

Run with:  streamlit run app.py
"""
import streamlit as st

import config
import db
import mail_fetcher
import mail_sender
import reply_suggester

st.set_page_config(page_title="Mail Reply Assistant", page_icon="📬", layout="wide")
db.init_db()

st.title("📬 Mail Reply Assistant")

page = st.sidebar.radio("Navigate", ["Inbox", "Setup & Help"])

# ============================================================ INBOX
if page == "Inbox":
    if not config.is_configured():
        st.warning(
            "No email account configured yet. Go to **Setup & Help** in the sidebar "
            "for step-by-step instructions."
        )
    else:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            unseen_only = st.checkbox("Only fetch unread emails", value=True)
        with col2:
            limit = st.number_input("Max to fetch", min_value=1, max_value=50, value=10)
        with col3:
            st.write("")
            st.write("")
            fetch_clicked = st.button("📥 Check for New Mail", type="primary")

        if fetch_clicked:
            with st.spinner("Connecting to your inbox..."):
                try:
                    new_emails = mail_fetcher.fetch_recent_emails(
                        limit=int(limit), unseen_only=unseen_only
                    )
                    added = 0
                    for e in new_emails:
                        intent, draft = reply_suggester.suggest_reply(
                            e["sender_name"], e["subject"], e["body"]
                        )
                        before = len(db.get_emails())
                        db.save_email(
                            e["message_id"], e["sender_name"], e["sender_email"],
                            e["subject"], e["body"], e["received_date"],
                            intent, draft,
                        )
                        after = len(db.get_emails())
                        added += (after - before)
                    st.success(f"Fetched {len(new_emails)} email(s), {added} new.")
                except Exception as exc:
                    st.error(f"Couldn't fetch mail: {exc}")

        st.divider()

        status_filter = st.radio(
            "Show", ["pending", "replied", "skipped", "all"], horizontal=True
        )
        emails = db.get_emails(status=None if status_filter == "all" else status_filter)

        if not emails:
            st.info("No emails here yet. Click 'Check for New Mail' above to fetch some.")
        else:
            for e in emails:
                badge = {"pending": "🟡", "replied": "✅", "skipped": "⏭️"}.get(e["status"], "")
                with st.expander(
                    f"{badge} **{e['subject'] or '(no subject)'}** — from {e['sender_name']} "
                    f"· *{e['intent']}* · {e['received_date']}"
                ):
                    st.caption("Original message:")
                    st.text(e["body"][:1000] + ("..." if len(e["body"]) > 1000 else ""))

                    reply_text = st.text_area(
                        "Suggested reply (edit before sending)",
                        value=e["suggested_reply"],
                        height=180,
                        key=f"reply_{e['id']}",
                    )

                    b1, b2, b3 = st.columns([1, 1, 3])
                    with b1:
                        if st.button("✉️ Send Reply", key=f"send_{e['id']}"):
                            try:
                                mail_sender.send_reply(
                                    e["sender_email"], e["subject"], reply_text,
                                    in_reply_to=e["message_id"],
                                )
                                db.update_reply_text(e["id"], reply_text)
                                db.mark_status(e["id"], "replied")
                                st.success("Reply sent!")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Failed to send: {exc}")
                    with b2:
                        if st.button("⏭️ Skip", key=f"skip_{e['id']}"):
                            db.update_reply_text(e["id"], reply_text)
                            db.mark_status(e["id"], "skipped")
                            st.rerun()

# ============================================================ SETUP & HELP
elif page == "Setup & Help":
    st.header("Setup & Help")

    st.markdown("""
This app connects to your inbox over **IMAP** (to read mail) and **SMTP** (to send
replies). Credentials live in a local `.env` file — never typed into this UI or
committed to source control.

### 1. Create a `.env` file
In the project folder, copy `.env.example` to `.env` and fill in your details:
```
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_16_char_app_password
IMAP_SERVER=imap.gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
```

### 2. Gmail users: generate an App Password
Gmail blocks your normal password for this kind of access. You need a
**16-character App Password** instead:
1. Go to your Google Account → **Security**
2. Turn on **2-Step Verification** if it isn't already on (required for App Passwords)
3. Search for **"App Passwords"** in your Google Account settings
4. Create one (name it e.g. "Mail Assistant"), copy the 16-character code
5. Paste it as `EMAIL_PASSWORD` in your `.env` — not your real Gmail password

### 3. Other providers
Change `IMAP_SERVER` / `SMTP_SERVER` accordingly, e.g.:
- **Outlook/Microsoft 365:** `outlook.office365.com` (IMAP), `smtp.office365.com` (SMTP)
- **Yahoo:** `imap.mail.yahoo.com`, `smtp.mail.yahoo.com`

### 4. Restart the app
After saving `.env`, restart Streamlit (`Ctrl+C` then `streamlit run app.py` again)
so the new settings are picked up.
""")

    st.divider()
    if config.is_configured():
        st.success(f"Configured for: {config.EMAIL_ADDRESS}")
    else:
        st.warning("Not configured yet — no `.env` file found or it's missing values.")

st.sidebar.divider()
st.sidebar.caption("Built with Python, SQLite & Streamlit")
