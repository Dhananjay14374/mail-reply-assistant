"""
app.py — Mail Reply Assistant (single-page version)
"""
import streamlit as st

import ai_reply
import config
import db
import mail_fetcher
import mail_sender
import reply_suggester

st.set_page_config(page_title="Mail Reply Assistant", layout="wide")
db.init_db()

st.title("Mail Reply Assistant")

# ---------------------------------------------------------- session state
defaults = {
    "email_address": config.EMAIL_ADDRESS,
    "email_password": config.EMAIL_PASSWORD,
    "imap_server": config.IMAP_SERVER,
    "smtp_server": config.SMTP_SERVER,
    "smtp_port": config.SMTP_PORT,
    "gemini_api_key": "",
}
for key, val in defaults.items():
    st.session_state.setdefault(key, val)
st.session_state.setdefault(
    "connected", bool(st.session_state.email_address and st.session_state.email_password)
)

# ---------------------------------------------------------- connect form
with st.container(border=True):
    st.subheader("Connect your email")

    c1, c2 = st.columns(2)
    with c1:
        email_input = st.text_input(
            "Email address", value=st.session_state.email_address, placeholder="you@gmail.com"
        )
    with c2:
        password_input = st.text_input(
            "App Password", value=st.session_state.email_password, type="password",
            placeholder="16-character app password",
        )

    with st.expander("⚙️"):
        a1, a2, a3 = st.columns(3)
        with a1:
            imap_input = st.text_input("IMAP server", value=st.session_state.imap_server)
        with a2:
            smtp_input = st.text_input("SMTP server", value=st.session_state.smtp_server)
        with a3:
            smtp_port_input = st.number_input(
                "SMTP port", value=st.session_state.smtp_port, step=1
            )

    with st.expander("AI-generated replies (optional)"):
        st.caption(
            "Leave this blank to keep using the built-in rule-based templates — everything "
            "still works without it. Add a free Google Gemini API key to have replies drafted "
            "by AI instead. Your key is kept only in this browser session, same as your "
            "email password — never written to disk."
        )
        gemini_key_input = st.text_input(
            "Gemini API key", value=st.session_state.gemini_api_key, type="password",
            placeholder="AIza... (get one free at aistudio.google.com/apikey)",
        )
        st.markdown(
            "No credit card needed — sign in with your Google account at "
            "[aistudio.google.com/apikey](https://aistudio.google.com/apikey) and click "
            "\"Create API key\"."
        )

    with st.expander(" Need a Gmail App Password?"):
        st.markdown("""
Gmail blocks your normal password for this kind of access — you need a
16-character **App Password** instead:
1. Google Account → **Security**
2. Turn on **2-Step Verification** (required for App Passwords)
3. Search **"App Passwords"** in your Google Account settings
4. Create one, copy the 16-character code
5. Paste it above — not your normal Gmail password

""")

    if st.button("🔌 Connect", type="primary"):
        st.session_state.email_address = email_input.strip()
        st.session_state.email_password = password_input.strip()
        st.session_state.imap_server = imap_input.strip()
        st.session_state.smtp_server = smtp_input.strip()
        st.session_state.smtp_port = int(smtp_port_input)
        st.session_state.gemini_api_key = gemini_key_input.strip()
        st.session_state.connected = bool(
            st.session_state.email_address and st.session_state.email_password
        )
        if st.session_state.connected:
            st.success(f"Connected as {st.session_state.email_address}")
        else:
            st.error("Enter both an email address and an app password.")

st.divider()

# ---------------------------------------------------------- inbox
if not st.session_state.connected:
    st.info("Enter your email and app password above, then click **Connect** to see your inbox.")
else:
    acct = st.session_state.email_address

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
                    limit=int(limit), unseen_only=unseen_only,
                    email_address=st.session_state.email_address,
                    email_password=st.session_state.email_password,
                    imap_server=st.session_state.imap_server,
                )
                added = 0
                for e in new_emails:
                    intent = reply_suggester.detect_intent(e["subject"], e["body"])
                    draft = None
                    if st.session_state.gemini_api_key:
                        try:
                            draft = ai_reply.generate_ai_reply(
                                st.session_state.gemini_api_key,
                                e["sender_name"], e["subject"], e["body"],
                            )
                        except ai_reply.AIReplyError:
                            draft = None  # fall through to rule-based template below
                    if draft is None:
                        intent, draft = reply_suggester.suggest_reply(
                            e["sender_name"], e["subject"], e["body"]
                        )
                    before = len(db.get_emails(acct))
                    db.save_email(
                        acct, e["message_id"], e["sender_name"], e["sender_email"],
                        e["subject"], e["body"], e["received_date"], intent, draft,
                    )
                    after = len(db.get_emails(acct))
                    added += (after - before)
                st.success(f"Fetched {len(new_emails)} email(s), {added} new.")
            except Exception as exc:
                st.error(f"Couldn't fetch mail — check your email/app password above. ({exc})")

    st.divider()

    status_filter = st.radio("Show", ["pending", "replied", "skipped", "all"], horizontal=True)
    emails = db.get_emails(acct, status=None if status_filter == "all" else status_filter)

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
                    value=e["suggested_reply"], height=180, key=f"reply_{e['id']}",
                )

                b1, b2, b3, b4 = st.columns([1, 1, 1.4, 2.6])
                with b1:
                    if st.button("✉️ Send Reply", key=f"send_{e['id']}"):
                        try:
                            mail_sender.send_reply(
                                e["sender_email"], e["subject"], reply_text,
                                in_reply_to=e["message_id"],
                                email_address=st.session_state.email_address,
                                email_password=st.session_state.email_password,
                                smtp_server=st.session_state.smtp_server,
                                smtp_port=st.session_state.smtp_port,
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
                with b3:
                    if st.session_state.gemini_api_key:
                        if st.button("🤖 Regenerate with AI", key=f"regen_{e['id']}"):
                            try:
                                with st.spinner("Asking Gemini for a draft..."):
                                    new_draft = ai_reply.generate_ai_reply(
                                        st.session_state.gemini_api_key,
                                        e["sender_name"], e["subject"], e["body"],
                                    )
                                db.update_reply_text(e["id"], new_draft)
                                st.session_state.pop(f"reply_{e['id']}", None)
                                st.rerun()
                            except ai_reply.AIReplyError as exc:
                                st.error(f"AI generation failed: {exc}")

st.sidebar.caption(" Created By Dhanankay Kumar")
st.sidebar.caption("🔒 Your password is kept only in this browser session — never saved to disk.")
