"""
email_reply.py — Draft and send customer reply emails via GPT-4o + Gmail SMTP.
Used for CHURN_RISK signals where a human-sounding reply is needed immediately.

Required env vars: GMAIL_USER, GMAIL_APP_PASSWORD
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import BaseModel
from openai import OpenAI
import railtracks as rt

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


REPLY_PROMPT = """You are a senior customer success manager writing on behalf of the engineering team.

A customer has sent a signal that requires an immediate, empathetic response.
Write a concise, professional reply that:
- Acknowledges their specific concern (use their exact words)
- Shows urgency and ownership ("I personally...")
- States a concrete next step with a timeframe
- Does NOT make promises you can't keep
- Is 3-5 sentences max — no fluff

Return a JSON object:
{
  "subject": "<reply subject line>",
  "body": "<email body — plain text, no markdown>"
}"""


class DraftReplyInput(BaseModel):
    customer: str
    company: str
    classification: str
    original_text: str
    actions_taken: str = ""


class DraftReplyOutput(BaseModel):
    subject: str
    body: str
    to_name: str
    to_company: str


@rt.function_node
async def draft_reply(input: DraftReplyInput) -> DraftReplyOutput:
    """
    Draft a customer reply email for CHURN_RISK or high-urgency BUG signals.
    Returns subject and body — does not send.
    """
    client = _get_client()

    context = (
        f"Customer: {input.customer} at {input.company}\n"
        f"Signal type: {input.classification}\n"
        f"Their message: {input.original_text}\n"
    )
    if input.actions_taken:
        context += f"Actions already taken: {input.actions_taken}\n"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": REPLY_PROMPT},
            {"role": "user", "content": context},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
    )

    result = json.loads(response.choices[0].message.content)
    return DraftReplyOutput(
        subject=result["subject"],
        body=result["body"],
        to_name=input.customer,
        to_company=input.company,
    )


def send_email(to_address: str, subject: str, body: str) -> bool:
    """
    Send an email via Gmail SMTP.
    Returns True if sent successfully.
    """
    gmail_user = os.environ["GMAIL_USER"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"].replace(" ", "")

    msg = MIMEMultipart()
    msg["From"] = f"Signal Agent <{gmail_user}>"
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_password)
        server.send_message(msg)

    return True


async def generate_and_send_reply(classification_result: dict,
                                   to_address: str,
                                   actions_taken: str = "") -> dict:
    """
    Draft a reply via GPT-4o and send it via Gmail.
    Returns draft dict with 'subject', 'body', 'sent', 'to_address'.
    """
    reply = await draft_reply(DraftReplyInput(
        customer=classification_result["customer"],
        company=classification_result["company"],
        classification=classification_result["classification"],
        original_text=classification_result["text"],
        actions_taken=actions_taken,
    ))

    sent = False
    try:
        send_email(to_address, reply.subject, reply.body)
        sent = True
        print(f"[email] Sent to {to_address} — {reply.subject}")
    except Exception as e:
        print(f"[email] Send failed ({e}), draft saved")

    return {
        "subject": reply.subject,
        "body": reply.body,
        "to_name": reply.to_name,
        "to_company": reply.to_company,
        "to_address": to_address,
        "sent": sent,
    }
