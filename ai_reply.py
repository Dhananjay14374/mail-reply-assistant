"""
ai_reply.py — Optional AI-generated reply drafts using the Google Gemini API
(free tier: aistudio.google.com, no credit card required).

This is entirely optional. If no API key is provided, the app falls back to
the rule-based templates in reply_suggester.py. When a key IS provided,
this module drafts a reply using Gemini instead of a fixed template — the
intent label itself still comes from the keyword detector, since that's
just used for filtering/display, not for the reply text.

The generated draft is always shown to the user for review/editing before
sending — this module only drafts, it never sends anything itself.
"""
import requests

# Google periodically retires older model names for new API keys — if this
# starts 404ing again in the future ("model X is no longer available to new
# users"), that's the only line that needs updating. Check current model
# names at ai.google.dev/gemini-api/docs/models.
GEMINI_MODEL = "gemini-3.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

PROMPT_TEMPLATE = """You are drafting a short, professional email reply on behalf of the recipient.

Original email:
From: {sender_name}
Subject: {subject}
Body:
{body}

Write a concise, polite reply (3-5 sentences max). Match a professional but warm tone.
Sign off with "[Your Name]" as a placeholder — do not invent a name.
Do not include a subject line. Do not add any preamble like "Here's a draft" —
output ONLY the reply email body text itself, nothing else."""


class AIReplyError(Exception):
    """Raised when the Gemini API call fails or returns something unusable."""
    pass


def generate_ai_reply(api_key: str, sender_name: str, subject: str, body: str) -> str:
    """Call the Gemini API to draft a reply. Raises AIReplyError on any failure
    so the caller can fall back to the rule-based template."""
    if not api_key:
        raise AIReplyError("No API key provided.")

    prompt = PROMPT_TEMPLATE.format(
        sender_name=sender_name or "the sender",
        subject=subject or "(no subject)",
        body=(body or "")[:3000],  # keep prompts reasonably sized
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.6,
            "maxOutputTokens": 800,
            # gemini-3.5-flash always spends some tokens on hidden internal
            # "thinking" before writing the actual reply — without this, that
            # can eat the whole maxOutputTokens budget and leave a truncated,
            # low-quality answer. "low" minimizes that overhead for a
            # simple task like drafting an email reply.
            "thinkingConfig": {"thinkingLevel": "low"},
        },
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

    try:
        resp = requests.post(GEMINI_URL, headers=headers, json=payload, timeout=20)
    except requests.RequestException as exc:
        raise AIReplyError(f"Network error contacting Gemini: {exc}") from exc

    if resp.status_code != 200:
        raise AIReplyError(f"Gemini API returned {resp.status_code}: {resp.text[:200]}")

    try:
        data = resp.json()
        candidate = data["candidates"][0]
        text = candidate["content"]["parts"][0]["text"]
    except (KeyError, IndexError, ValueError) as exc:
        raise AIReplyError(f"Unexpected Gemini response shape: {exc}") from exc

    # If generation got cut off before finishing (e.g. hit the token limit),
    # the partial text is unreliable — better to fail loudly here and fall
    # back to the rule-based template than show a half-finished reply.
    if candidate.get("finishReason") == "MAX_TOKENS":
        raise AIReplyError("Gemini response was cut off (hit the token limit).")

    text = text.strip()
    if not text:
        raise AIReplyError("Gemini returned an empty reply.")
    return text
