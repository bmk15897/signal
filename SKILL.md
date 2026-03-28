---
name: signal
description: Autonomous agent that turns customer signals (emails, calls) into engineering actions across Jira, Notion, and Slack — zero human intervention.
version: 0.1.0
categories:
  - ai-ml
  - other
---

# Signal — Autonomous Engineering Action Agent

Processes customer signals (emails, call recordings) and takes autonomous
engineering action across Jira, Notion, and Slack without human intervention.

## When to use
- Process a customer call recording or email automatically
- Create Jira tickets from customer feedback
- Update product roadmap based on customer signals
- Generate CEO digest of customer feedback trends

## Inputs
- Audio file (call recording)
- Email webhook payload

## Outputs
- Jira ticket (bugs and high-frequency feature requests)
- Notion roadmap update (feature requests with 3+ signals)
- Slack notification (routed by signal type)
- CEO digest entry

## Required env vars
OPENAI_API_KEY, SENSO_API_KEY, JIRA_API_TOKEN,
NOTION_API_KEY, SLACK_WEBHOOK_URL, UNKEY_ROOT_KEY
