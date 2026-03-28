import requests
import os


def send_alert(channel_env_key: str, signal: dict, actions: list) -> None:
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
            }}
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
