"""
email_reply.py — Draft customer reply emails via GPT-4o.
Does NOT send email — returns a draft string for Person 2 to send via their email provider.
Used for CHURN_RISK signals where a human-sounding reply is needed immediately.
"""

import os
import json
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


async def generate_reply(classification_result: dict, actions_taken: str = "") -> dict:
    """Convenience wrapper. Returns {'subject', 'body', 'to_name', 'to_company'}."""
    result = await draft_reply(DraftReplyInput(
        customer=classification_result["customer"],
        company=classification_result["company"],
        classification=classification_result["classification"],
        original_text=classification_result["text"],
        actions_taken=actions_taken,
    ))
    return result.model_dump()
