"""
email_poller.py — Gmail IMAP inbox poller
Watches bmk15897@gmail.com for new unread emails every 30 seconds.
Feeds each new email into the Signal pipeline automatically.

Person 2: call start_poller(broadcast) as a background task on server startup.
"""

import asyncio
import imaplib
import email
import os
from email.header import decode_header


def _decode(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    decoded, enc = decode_header(value)[0]
    if isinstance(decoded, bytes):
        return decoded.decode(enc or "utf-8", errors="replace")
    return decoded


def _get_email_body(msg) -> str:
    """Extract plain text body from email message."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                return payload.decode("utf-8", errors="replace") if payload else ""
    else:
        payload = msg.get_payload(decode=True)
        return payload.decode("utf-8", errors="replace") if payload else ""
    return ""


def _fetch_new_emails() -> list[dict]:
    """
    Connect to Gmail via IMAP, fetch unread emails, mark them as read.
    Returns list of {from_address, subject, body}.
    """
    gmail_user = os.environ["GMAIL_USER"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"].replace(" ", "")

    results = []
    with imaplib.IMAP4_SSL("imap.gmail.com") as imap:
        imap.login(gmail_user, gmail_password)
        imap.select("INBOX")

        # Only fetch emails received today — avoids processing old unread backlog
        from datetime import datetime
        today = datetime.now().strftime("%d-%b-%Y")
        _, message_ids = imap.search(None, f'(UNSEEN SINCE "{today}")')
        ids = message_ids[0].split()

        for msg_id in ids:
            _, msg_data = imap.fetch(msg_id, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            from_address = _decode(msg.get("From", ""))
            # Extract just the email address from "Name <email@domain.com>"
            if "<" in from_address and ">" in from_address:
                from_address = from_address.split("<")[1].rstrip(">")

            subject = _decode(msg.get("Subject", "(no subject)"))
            body = _get_email_body(msg)

            if not body.strip():
                continue

            # Mark as read
            imap.store(msg_id, "+FLAGS", "\\Seen")

            results.append({
                "from_address": from_address.strip(),
                "subject": subject,
                "body": f"Subject: {subject}\n\n{body}",
            })

    return results


async def poll_once(broadcast=None) -> int:
    """
    Poll Gmail once. Returns number of emails processed.
    """
    from pipeline import process_signal

    try:
        emails = _fetch_new_emails()
    except Exception as e:
        print(f"[poller] IMAP fetch failed: {e}")
        return 0

    for em in emails:
        print(f"[poller] New email from {em['from_address']} — {em['subject']}")
        try:
            from pipeline import _make_broadcast_adapter
            await process_signal(
                signal_type="email",
                content=em["body"],
                stream_callback=_make_broadcast_adapter(broadcast),
                sender_email=em["from_address"],
            )
        except Exception as e:
            print(f"[poller] Pipeline error for {em['from_address']}: {e}")

    return len(emails)


async def start_poller(broadcast=None, interval: int = 30):
    """
    Run the inbox poller indefinitely.
    Person 2 calls this as a FastAPI background task:

        @app.on_event("startup")
        async def startup():
            asyncio.create_task(start_poller(broadcast=broadcast))
    """
    print(f"[poller] Started — watching {os.environ.get('GMAIL_USER')} every {interval}s")
    while True:
        count = await poll_once(broadcast)
        if count:
            print(f"[poller] Processed {count} email(s)")
        await asyncio.sleep(interval)
