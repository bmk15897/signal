"""
slack.py — Slack integration
Sends formatted signal alerts via incoming webhook.
Provides both a Railtracks node (used by pipeline.py) and a plain function (used by main.py).
"""

import os
import requests
from typing import List
from pydantic import BaseModel
import railtracks as rt


# ---------------------------------------------------------------------------
# Railtracks node (used by pipeline.py)
# ---------------------------------------------------------------------------

class SlackAlertInput(BaseModel):
    channel_hint: str
    classification: str
    urgency: int
    customer: str
    company: str
    text: str
    actions_taken: List[str] = []


class SlackAlertOutput(BaseModel):
    ok: bool


@rt.function_node
async def send_slack_alert(alert: SlackAlertInput) -> SlackAlertOutput:
    """
    Send a formatted signal alert to Slack via incoming webhook.
    """
    urgency_emoji = "🔴" if alert.urgency >= 8 else "🟡" if alert.urgency >= 5 else "🟢"
    actions_text = "\n".join(f"• {a}" for a in alert.actions_taken) or "• Logged to memory"

    payload = {
        "text": f"{urgency_emoji} Signal Agent: *{alert.classification}* detected",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"{urgency_emoji} *{alert.classification}* from "
                        f"*{alert.customer}* at *{alert.company}*\n"
                        f"Urgency: {alert.urgency}/10 | Channel: {alert.channel_hint}\n"
                        f"_{alert.text[:200]}..._"
                    ),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Actions taken automatically:*\n{actions_text}",
                },
            },
            {"type": "divider"},
        ],
    }

    try:
        r = requests.post(os.environ["SLACK_WEBHOOK_URL"], json=payload, timeout=10)
        r.raise_for_status()
        return SlackAlertOutput(ok=True)
    except Exception as e:
        print(f"[slack] Failed ({e})")
        return SlackAlertOutput(ok=False)


# ---------------------------------------------------------------------------
# Plain functions (used by main.py / Person 2)
# ---------------------------------------------------------------------------

def send_alert(channel_env_key: str, signal: dict, actions: list) -> None:
    """Dict-based interface for use from main.py."""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("SLACK_WEBHOOK_URL environment variable not set")

    requests.post(webhook_url, json={
        "text": f"Signal Agent: *{signal['classification']}* detected",
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text":
                f"*{signal['classification']}* from {signal['customer']} "
                f"at {signal['company']}\n"
                f"Urgency: {signal['urgency']}/10\n"
                f"_{signal['text'][:200]}..._"
            }},
            {"type": "section", "text": {"type": "mrkdwn", "text":
                "*Actions taken automatically:*\n" +
                "\n".join([f"• {a}" for a in actions])
            }},
        ]
    })


def send_test_message() -> dict:
    """Send a test message to verify Slack webhook is working."""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("SLACK_WEBHOOK_URL environment variable not set")

    r = requests.post(webhook_url, json={
        "text": ":rocket: *Signal Agent* is online and ready to process customer signals.",
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text":
                ":rocket: *Signal Agent* is online!\n\n"
                "I'll automatically process customer emails and call recordings and "
                "take engineering action — creating Jira tickets, updating Notion, "
                "and pinging the right Slack channels. No human required."
            }}
        ]
    })
    return {"status": r.status_code, "ok": r.status_code == 200}
