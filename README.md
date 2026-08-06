# 📬 Mail Reply Assistant

Python + SQLite + Streamlit app that checks your inbox over IMAP, drafts a
reply for each email — either from rule-based templates or, optionally, a
free Google Gemini API key — lets you edit it, and sends it over SMTP.

Everything happens on one screen: enter your email + app password, click
Connect, and your inbox appears right below.

## Optional: AI-generated replies

By default, replies come from the rule-based template engine in
`reply_suggester.py` (free, no setup, fully offline). If you'd rather have
replies drafted by an actual language model:

1. Get a free API key (no credit card) at
   [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Paste it into the **"🤖 AI-generated replies"** section on the Connect
   card, then click Connect
3. New emails you fetch from then on will be drafted by Gemini instead of
   a template; use **"🤖 Regenerate with AI"** on any existing email to
   redraft it

Leave the field blank and nothing changes — the app works exactly as
before. Every draft, AI or template, still shows in an editable box for
you to review before **Send Reply** — this app never sends anything
without you clicking Send yourself.

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

That's it — no `.env` file required. Enter your Gmail address and App
Password directly in the app when it opens (see **Gmail App Password**
below if you don't have one). They're kept only in your browser session —
never written to the database or to disk.

*(Optional, for local development only: copy `.env.example` to `.env` and
fill in your details if you'd like the login form to pre-fill automatically
each time you run the app.)*

### Gmail App Password
Gmail blocks your normal account password for this kind of access. You need
a 16-character **App Password** instead:
1. Google Account → **Security**
2. Turn on **2-Step Verification** (required for App Passwords)
3. Search **"App Passwords"** in account settings, create one
4. Paste the 16-character code into the app's password field

Other providers (Outlook, Yahoo, etc.) — expand **"Advanced"** in the app
to change the IMAP/SMTP server addresses.

## Project structure

| File | Responsibility |
|---|---|
| `app.py` | Single-page Streamlit UI — connect form + inbox (fetch, review, edit, send) |
| `config.py` | Optional `.env` defaults, used only to pre-fill the login form locally |
| `db.py` | SQLite schema + CRUD for the `emails` table; every row is scoped to an `account_email` so different accounts never mix results, and dedup is per-account by `message_id` |
| `mail_fetcher.py` | IMAP connection; parses sender/subject/body from raw email bytes, handles multipart and encoded headers |
| `reply_suggester.py` | Rule-based intent detection (keyword matching) + reply templates |
| `mail_sender.py` | SMTP sending, threads the reply via `In-Reply-To`/`References` headers |

## How it works

1. Enter your email and app password in the **Connect your email** box,
   click **Connect**
2. Click **Check for New Mail** — connects over IMAP, fetches recent
   (unread by default) emails
3. Each email's subject+body is scanned against keyword lists per intent
   (Meeting Request, Job/Application, Invoice/Payment, Complaint/Issue,
   Thank You, Question/Inquiry, Promotional/Unsubscribe, or General)
4. A matching template is filled in with the sender's first name and shown
   as an editable draft
5. Edit as needed, then **Send Reply** — sends over SMTP and marks the
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

- Credentials are held only in Streamlit's `session_state` for the current
  browser tab — never written to the database, never logged, cleared when
  you close or refresh the tab.
- If you deploy this publicly (e.g. Streamlit Community Cloud), anyone with
  the link can type in *their own* credentials and use it as a mini mail
  client — your own credentials are never exposed, but there's no login
  wall stopping others from using the tool itself. Fine for a demo/resume
  project; add real authentication before using it for anything sensitive.
- The database scopes stored emails by `account_email`, so multiple people
  using the same deployed app won't see each other's inbox contents.
