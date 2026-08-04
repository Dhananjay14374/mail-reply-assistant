"""
reply_suggester.py — Rule-based intent detection and reply-template engine.

This is a transparent keyword system (like categorizer.py in the expense
tracker project), not a machine-learning model: each email's subject+body is
scanned for keyword patterns per intent, and a matching template is filled
in and returned. It's deterministic, free, and easy to extend — add a
keyword or a new intent block and it's picked up automatically.

To upgrade this to real AI later: replace suggest_reply()'s body with a
call to an LLM API (e.g. the Anthropic or OpenAI SDK), passing the email
text and asking for a drafted reply. Everything else (storage, UI, sending)
stays the same.
"""

INTENT_KEYWORDS = {
    "Meeting Request": [
        "meeting", "schedule a call", "are you available", "calendar",
        "zoom", "google meet", "catch up", "set up a time", "book a slot",
    ],
    "Job/Application": [
        "resume", "cv", "application", "position", "interview",
        "hiring", "job opening", "opportunity", "candidate",
    ],
    "Invoice/Payment": [
        "invoice", "payment due", "bill", "receipt", "amount owed",
        "outstanding balance", "please pay",
    ],
    "Complaint/Issue": [
        "issue", "problem", "not working", "broken", "disappointed",
        "refund", "complaint", "doesn't work", "error occurred",
    ],
    "Thank You": [
        "thank you", "thanks so much", "much appreciated", "grateful",
    ],
    "Question/Inquiry": [
        "could you", "can you tell me", "question", "wondering",
        "clarify", "how do i", "what is the", "any update",
    ],
    "Promotional/Unsubscribe": [
        "unsubscribe", "limited time", "% off", "special offer",
        "act now", "exclusive deal",
    ],
}

DEFAULT_INTENT = "General"

REPLY_TEMPLATES = {
    "Meeting Request": (
        "Hi {name},\n\n"
        "Thanks for reaching out. I'd be happy to meet — could you share a "
        "couple of times that work for you, or send over a calendar invite?\n\n"
        "Best,\n[Your Name]"
    ),
    "Job/Application": (
        "Hi {name},\n\n"
        "Thank you for reaching out regarding this opportunity. I've reviewed "
        "the details and I'm interested in learning more. Could we set up a "
        "time to discuss further?\n\n"
        "Best regards,\n[Your Name]"
    ),
    "Invoice/Payment": (
        "Hi {name},\n\n"
        "Thanks for sending this over. I'll review the invoice and confirm "
        "payment shortly. Please let me know if there's a specific deadline.\n\n"
        "Best,\n[Your Name]"
    ),
    "Complaint/Issue": (
        "Hi {name},\n\n"
        "I'm sorry to hear you're running into this issue. Could you share a "
        "few more details (screenshots, when it started, etc.) so I can look "
        "into it right away?\n\n"
        "Best,\n[Your Name]"
    ),
    "Thank You": (
        "Hi {name},\n\n"
        "You're very welcome — glad it was helpful! Let me know if there's "
        "anything else you need.\n\n"
        "Best,\n[Your Name]"
    ),
    "Question/Inquiry": (
        "Hi {name},\n\n"
        "Thanks for your question. Let me look into this and get back to you "
        "with a full answer shortly.\n\n"
        "Best,\n[Your Name]"
    ),
    "Promotional/Unsubscribe": (
        "This looks like a promotional email — no reply drafted. "
        "You can unsubscribe using the link in the original message if you'd like."
    ),
    "General": (
        "Hi {name},\n\n"
        "Thanks for your email. I'll take a look and get back to you soon.\n\n"
        "Best,\n[Your Name]"
    ),
}


def detect_intent(subject: str, body: str) -> str:
    text = f"{subject or ''} {body or ''}".lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return intent
    return DEFAULT_INTENT


def suggest_reply(sender_name: str, subject: str, body: str):
    """Return (intent, draft_reply_text) for a given email."""
    intent = detect_intent(subject, body)
    first_name = (sender_name or "there").split()[0] if sender_name else "there"
    template = REPLY_TEMPLATES.get(intent, REPLY_TEMPLATES[DEFAULT_INTENT])
    draft = template.format(name=first_name)
    return intent, draft
