# 📬 Mail Reply Assistant

Python + SQLite + Streamlit app that checks your inbox over IMAP, detects
the intent of each email using a rule-based keyword engine, drafts a reply
from a matching template, lets you edit it, and sends it over SMTP.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Then edit `.env` with your real email and app password (see **Gmail App
Password** below), and run:

```bash
streamlit run app.py
```

### Gmail App Password
Gmail blocks your normal account password for this kind of access. You need
a 16-character **App Password** instead:
1. Google Account → **Security**
2. Turn on **2-Step Verification** (required for App Passwords)
3. Search **"App Passwords"** in account settings, create one
4. Paste the 16-character code into `.env` as `EMAIL_PASSWORD`

Other providers (Outlook, Yahoo, etc.) — just change `IMAP_SERVER` /
`SMTP_SERVER` in `.env`; see in-app **Setup & Help** page for values.

## Project structure

| File | Responsibility |
|---|---|
| `app.py` | Streamlit UI — Inbox page (fetch, review, edit, send) and Setup & Help page |
| `config.py` | Loads credentials from `.env` (never hardcoded, never committed) |
| `db.py` | SQLite schema + CRUD for the `emails` table (dedup by `message_id`) |
| `mail_fetcher.py` | IMAP connection; parses sender/subject/body from raw email bytes, handles multipart and encoded headers |
| `reply_suggester.py` | Rule-based intent detection (keyword matching) + reply templates |
| `mail_sender.py` | SMTP sending, threads the reply via `In-Reply-To`/`References` headers |

## How it works

1. Click **Check for New Mail** — connects over IMAP, fetches recent
   (unread by default) emails
2. Each email's subject+body is scanned against keyword lists per intent
   (Meeting Request, Job/Application, Invoice/Payment, Complaint/Issue,
   Thank You, Question/Inquiry, Promotional/Unsubscribe, or General)
3. A matching template is filled in with the sender's first name and shown
   as an editable draft
4. Edit as needed, then **Send Reply** — sends over SMTP and marks the
   email as `replied` in the database (or **Skip** to mark it handled
   without sending)

## Extending

- Add keywords or new intents in `INTENT_KEYWORDS` / `REPLY_TEMPLATES` in
  `reply_suggester.py` — no other code changes needed.
- **Swap in real AI:** replace the body of `suggest_reply()` in
  `reply_suggester.py` with a call to an LLM API (Anthropic/OpenAI SDK),
  passing the email text and asking for a drafted reply. Storage, UI, and
  sending all stay the same.

## Security notes

- Credentials live only in `.env` (git-ignored) — never typed into the UI,
  never stored in the database.
- This is a **single-user, local tool**: the SQLite file has no
  authentication layer. Don't deploy this publicly with real inbox access
  without adding auth first.
