"""
Quick test — sends a real Slack message to verify the webhook works.
Usage: SLACK_WEBHOOK_URL=https://hooks.slack.com/... python backend/test_slack.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend.integrations.slack import send_test_message, send_alert

print("Sending test message...")
result = send_test_message()
print(f"Result: {result}")

if result["ok"]:
    print("✓ Slack message sent successfully!")
else:
    print(f"✗ Failed with status {result['status']}")
    sys.exit(1)

# Also test send_alert with fake signal data
print("\nSending alert with fake signal...")
send_alert(
    channel_env_key="SLACK_WEBHOOK_URL",
    signal={
        "classification": "BUG",
        "customer": "Jane Smith",
        "company": "Acme Corp",
        "urgency": 8,
        "text": "The export function crashes every time I try to download a CSV with more than 1000 rows. This is blocking our end-of-month reporting.",
    },
    actions=["Created Jira ticket ENG-42 (P1 Bug)", "Notified #engineering on Slack"],
)
print("✓ Alert sent!")
