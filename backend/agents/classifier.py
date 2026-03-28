"""
classifier.py — Signal classification node
Takes transcript text and returns structured classification dict.
"""

import os
import json
from typing import List, Literal
from pydantic import BaseModel
import railtracks as rt
from openai import OpenAI

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


CLASSIFICATION_PROMPT = """You are a customer signal classifier for a B2B SaaS company.

Analyze the following customer message and return a JSON object with exactly these fields:

{
  "classification": "<one of: BUG | FEATURE_REQUEST | CHURN_RISK | PRAISE | QUESTION>",
  "urgency": <integer 1-10>,
  "customer": "<customer name if mentioned, else 'Unknown'>",
  "company": "<company name if mentioned, else 'Unknown'>",
  "key_phrases": ["<phrase1>", "<phrase2>", "<phrase3>"],
  "sentiment": "<one of: positive | negative | neutral>"
}

Classification rules:
- BUG: customer reports something broken or not working as expected
- FEATURE_REQUEST: customer asks for something new or different
- CHURN_RISK: customer expresses frustration or mentions cancelling/leaving/switching
- PRAISE: customer expresses satisfaction or positive feedback
- QUESTION: customer needs information or clarification

Urgency rules:
- CHURN_RISK: always 8-10
- BUG with words like crash, data loss, blocking, can't work: 8-10
- BUG with intermittent/minor issues: 4-7
- FEATURE_REQUEST: 3-6 based on how strongly worded
- PRAISE / QUESTION: 1-3

Return ONLY valid JSON. No markdown, no explanation."""


class ClassifyInput(BaseModel):
    text: str


class ClassifyOutput(BaseModel):
    text: str
    classification: Literal["BUG", "FEATURE_REQUEST", "CHURN_RISK", "PRAISE", "QUESTION"]
    urgency: int
    customer: str
    company: str
    key_phrases: List[str]
    sentiment: Literal["positive", "negative", "neutral"]


@rt.function_node
async def classify(transcription: ClassifyInput) -> ClassifyOutput:
    """
    Classify a customer signal from its transcript text.
    Returns classification type, urgency score, entities, and sentiment.
    """
    text = transcription.text
    client = _get_client()

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": CLASSIFICATION_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    result = json.loads(response.choices[0].message.content)

    return ClassifyOutput(
        text=text,
        classification=result["classification"],
        urgency=int(result["urgency"]),
        customer=result.get("customer", "Unknown"),
        company=result.get("company", "Unknown"),
        key_phrases=result.get("key_phrases", []),
        sentiment=result["sentiment"],
    )
