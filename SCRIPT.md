# Signal — Demo Run Book
## Hackathon Demo: Multimodal Frontier — Mar 28, 2026 @ 5:00 PM PT

---

## 1. DEMO AUDIO — Record This Exact Script

Record a 25–35 second MP3. Use your phone's Voice Memos app or any recorder.
Save as: `demo/bug_call.mp3`

> **Read this out loud into your phone:**
>
> *"Hi, this is Sarah from Acme Corp. I'm calling because our entire data export
> feature is completely broken. Every time we try to export to CSV it crashes with
> a 500 error. This is blocking our entire finance team from running their
> end-of-month reports. We have a board meeting on Friday and we need this
> fixed immediately. This is critical."*

**Why this works:** Gemini will classify it as BUG, urgency 9/10, customer "Sarah",
company "Acme Corp". That triggers: Jira P1 + Slack #engineering.

**Alternative — use this pre-written text trigger** if audio isn't ready in time:
```bash
curl -s -X POST http://localhost:8080/monitor \
  -H "Content-Type: application/json" \
  -d '{"type":"email","text":"Hi, this is Sarah from Acme Corp. Our data export is completely broken — CSV export crashes with a 500 error every time. Our finance team is blocked for end-of-month reports. This needs to be fixed immediately."}'
```

---

## 2. PRE-DEMO CHECKLIST (Do this 20 minutes before)

### Environment
- [ ] `.env` has all keys set (OPENAI, GEMINI, JIRA, NOTION, SLACK, SENSO, GMAIL)
- [ ] Backend running: `cd /path/to/signal && .venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8080`
- [ ] Frontend running: `cd frontend && npm run dev` (localhost:3000)
- [ ] `DEMO_TEST_EVENTS=false` in `.env` (so fake events don't clutter the feed)

### Pre-warm the memory (makes frequency count more impressive)
Run this once to seed 4 similar past signals in Senso:
```bash
cd backend
for i in 1 2 3 4; do
  python3 -c "
import asyncio
from pipeline import process_signal
asyncio.run(process_signal('email', 'Customer at DataFlow Corp reported CSV export crashing with 500 error. Data pipeline broken.'))
"
  sleep 2
done
```
Now when Sarah's call comes in, Senso will find 4 similar past signals → urgency boost.

### Pre-generate the CEO digest
```bash
curl -s http://localhost:8080/digest | python3 -m json.tool
```
Keep this output in a text file as backup. You'll show it on screen.

### Browser tabs (open in this order, don't close)
1. **Tab 1** — Signal dashboard: `http://localhost:3000`
2. **Tab 2** — Jira project board (your project, open issues view)
3. **Tab 3** — Slack #engineering channel
4. **Tab 4** — Notion roadmap database
5. **Tab 5** — Digest backup (open the text file, or pre-navigate to `/digest` endpoint)

### Verify everything is connected
```bash
curl http://localhost:8080/health
# Should return: {"status":"ok","clients":0}
```

---

## 3. THE 3-MINUTE DEMO SCRIPT

### WORDS TO SAY → WHAT TO DO (side by side)

---

**[0:00 — 0:20] HOOK**

*Say:*
> "Every week, product managers at B2B companies spend hours listening to customer
> calls and reading support emails, figuring out what's broken, what to build, who's
> about to churn. Then they manually file Jira tickets, ping engineering on Slack,
> update the roadmap. We built Signal — an agent that does all of that automatically,
> in real time, without a single human decision."

*Do:* Nothing. Hold eye contact. Let the sentence land.

---

**[0:20 — 0:45] TRIGGER — Upload the call**

*Say:*
> "I have a real customer call recording right here. A customer called in with a
> critical bug report. Watch what happens when I drop it in."

*Do:*
- Switch to **Tab 1** (Signal dashboard)
- Drag `demo/bug_call.mp3` into the upload zone
- Watch the activity feed start firing on the right panel

*Say (while feed animates):*
> "The agent is transcribing the call with Gemini — one multimodal call for both
> transcription and classification. No separate Whisper step. And it's searching
> memory — it found 4 other customers who reported the same issue this month."

*Watch for these events in the feed:*
- `TRANSCRIBE` → "Processing with Gemini 2.5 Flash (multimodal)..."
- `CLASSIFY` → "Classified as BUG (urgency 9/10) — Sarah @ Acme Corp"
- `MEMORY` → "Found 4 similar past signals"
- `ROUTE` → "Actions queued: jira, slack (effective urgency 10/10)"

---

**[0:45 — 1:30] THE ACTIONS**

*Say:*
> "The agent just made a decision — this is a P1 bug with 4 other customers reporting
> the same thing, so urgency is 10 out of 10. It's now creating a Jira ticket..."

*Watch for:*
- `JIRA` → "Ticket SCRUM-XX created — [url]"

*Switch to **Tab 2** (Jira):*
> "Here it is. Created by the agent, not by me. P1 priority, the customer quote is
> in the description, it's labeled signal-agent so we can track everything the
> agent ever touched."

*Switch to **Tab 3** (Slack):*
> "And here's the Slack alert in #engineering. Sent automatically. The on-call
> engineer just got notified without anyone touching a keyboard."

*Say:*
> "Two real engineering actions. Zero human input. About 45 seconds."

---

**[1:30 — 2:00] THE INTELLIGENCE — Digest**

*Switch to **Tab 1**, show digest panel (or navigate to `/digest`):*

*Say:*
> "This is the CEO digest, generated from everything the agent has processed.
> The agent spotted that data export bugs have come up 5 times this month.
> There are 2 active churn risks. The most requested feature has 8 signals.
> No meeting required. The agent built the entire weekly report."

*If digest is empty, show the pre-generated text file backup.*

---

**[2:00 — 2:30] SECOND SIGNAL — Churn risk (optional, if time)**

*Paste this into terminal (or have it pre-typed):*
```bash
curl -s -X POST http://localhost:8080/monitor \
  -H "Content-Type: application/json" \
  -d '{"type":"email","text":"Hi, this is Maria from GlobalOps. We have had serious reliability issues for the past month. We are seriously considering switching to a competitor if things do not improve. We need a response by end of week or we are cancelling our subscription.","sender_email":"maria@globalops.com"}'
```

*Say:*
> "Now watch what happens with a churn risk. A frustrated customer threatening to leave."

*Watch feed for:*
- `CLASSIFY` → "CHURN_RISK (urgency 9/10) — Maria @ GlobalOps"
- `SLACK` → "Alert sent to #cs-team"
- `SYSTEM` → "Reply sent to maria@globalops.com"

*Say:*
> "The agent classified it as churn risk, alerted the customer success team on Slack,
> AND sent an empathetic reply email to Maria — automatically. She got a response
> in under a minute."

---

**[2:30 — 3:00] CLOSE**

*Say:*
> "Signal works on emails, on call recordings, on anything text or audio. Every
> signal is stored in memory so the agent gets smarter — it knows when the same
> issue has come up five times and escalates accordingly.
>
> You could hire an ops person for $80,000 a year to do this manually. Signal
> costs $299 a month. Every B2B company that has customers and engineers needs
> this. That is every B2B company."

*End on the activity feed. Let it sit on screen.*

---

## 4. BACKUP TRIGGER COMMANDS

If the UI breaks or upload doesn't work, run these from terminal. The activity feed
will still fire because broadcast is wired to the SSE queue.

**BUG scenario (Jira P1 + Slack #engineering):**
```bash
curl -s -X POST http://localhost:8080/monitor \
  -H "Content-Type: application/json" \
  -d '{"type":"email","text":"Hi, I am Sarah from Acme Corp. Our entire data export is completely broken. Every time we export to CSV it crashes with a 500 error. This is blocking our entire finance team. This needs to be fixed immediately."}'
```

**CHURN RISK scenario (Slack #cs-team + email reply):**
```bash
curl -s -X POST http://localhost:8080/monitor \
  -H "Content-Type: application/json" \
  -d '{"type":"email","text":"We have been frustrated with reliability issues for the past month. We are seriously considering switching to a competitor. We need a response by end of week or we are cancelling.","sender_email":"maria@globalops.com"}'
```

**FEATURE REQUEST scenario (Notion + Slack #product if freq >= 5):**
```bash
curl -s -X POST http://localhost:8080/monitor \
  -H "Content-Type: application/json" \
  -d '{"type":"email","text":"Love the product overall. One thing I really wish you had is a Zapier integration. We would love to connect it to our CRM automatically. Would make our workflow so much smoother."}'
```

**Force-generate digest:**
```bash
curl -s http://localhost:8080/digest | python3 -m json.tool
```

---

## 5. WHAT HAPPENS AT EACH PIPELINE STAGE

For judges asking technical questions:

| Stage | What runs | Model/API |
|---|---|---|
| TRANSCRIBE | `gemini_processor.py` — uploads audio to Gemini Files API | Gemini 2.5 Flash |
| CLASSIFY | Same Gemini call returns structured JSON classification | Gemini 2.5 Flash |
| MEMORY | `memory.py` — runs `senso search context` via CLI subprocess | Senso + @senso-ai/cli |
| ROUTE | `router.py` — deterministic rules + frequency boost | No LLM |
| JIRA | `jira.py` — deduplicates by company before creating | Jira REST API v3 |
| NOTION | `notion.py` — creates roadmap item | Notion API |
| SLACK | `slack.py` — urgency-colored alerts | Slack Webhooks |
| SYSTEM (email) | `email_reply.py` — drafts reply via GPT-4o, sends via Gmail SMTP | GPT-4o + Gmail |
| SENSO | `memory.py` — ingests signal as .txt into Senso KB | Senso CLI |

**Railtracks** (`railtracks>=1.3.6`) is the agent orchestration layer — every node is
a `@rt.function_node` with typed Pydantic I/O. The pipeline is also exposed as an
`rt.agent_node` for LLM-orchestrated runs.

---

## 6. COMMON FAILURES + INSTANT FIXES

| Symptom | Likely cause | Fix |
|---|---|---|
| Upload fires but no events in feed | Frontend SSE not connected | Hard refresh frontend, check `/health` shows clients > 0 |
| `JIRA failed: 400` | Issue type mismatch | Already fixed — uses "Task" not "Bug" |
| `JIRA failed: 410` | Wrong search endpoint | Already fixed — uses `/rest/api/3/search/jql` |
| Duplicate Jira tickets | Bug in dedup | Already fixed — checks for open signal-agent tickets per company |
| Senso returns frequency=0 | Senso CLI not installed or not logged in | Run `npm install -g @senso-ai/cli && senso login` |
| Email reply not sent | GMAIL_APP_PASSWORD wrong | Use app password from myaccount.google.com/apppasswords, not account password |
| Gemini fails | GEMINI_API_KEY missing or quota | Pipeline auto-falls back to Whisper + GPT-4o |
| Feed shows demo events | DEMO_TEST_EVENTS not set to false | Add `DEMO_TEST_EVENTS=false` to `.env`, restart server |

---

## 7. DEMO DAY TIMELINE

| Time | Action |
|---|---|
| 4:00 PM | All coding stops. Run full pipeline once end to end. |
| 4:05 PM | Seed Senso with 4 past signals (the pre-warm loop above) |
| 4:10 PM | Record demo audio on phone. Save to `demo/bug_call.mp3` |
| 4:15 PM | Run demo script out loud. Time it. Should be ~2:45. |
| 4:20 PM | Open all 5 browser tabs. Arrange on screen. |
| 4:25 PM | Pre-generate digest. Save text to clipboard as backup. |
| 4:30 PM | Devpost submission + Shipables publish |
| 4:45 PM | Second dry run. Fix any awkward transitions. |
| 5:00 PM | Demo. |

---

## 8. SHIPABLES PUBLISH (required before 4:30 PM)

```bash
# From project root
npx @senso-ai/shipables publish
```

The `SKILL.md` file already exists in the project. Run publish once to register it.

---

## 9. NGROK (if deploying to DigitalOcean fails)

```bash
ngrok http 8080
# Copy the https://xxxx.ngrok.io URL
# Update frontend/.env.local: NEXT_PUBLIC_API_URL=https://xxxx.ngrok.io
# Restart frontend
```

---

**If everything breaks:** Open the pre-generated digest text. Walk through it as if
the agent just ran. The intelligence layer is the story — Jira ticket creation is
just one delivery mechanism. The real demo is: *5 customers mentioned the same bug
and the agent figured that out automatically.*
