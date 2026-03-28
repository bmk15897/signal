"""
Signal — FastAPI backend
Person 2 owns this file (API routes and webhook receivers only).
"""

import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# ---------------------------------------------------------------------------
# In-process SSE broadcast bus
# ---------------------------------------------------------------------------

_sse_queues: list[asyncio.Queue] = []


def broadcast(event: dict) -> None:
    """Broadcast an activity event to all connected SSE clients."""
    payload = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        **event,
    }
    for q in list(_sse_queues):
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            pass


# ---------------------------------------------------------------------------
# Test event loop — fires every 5 s so the feed is visible before the
# real pipeline is wired up.  Disable by setting DEMO_TEST_EVENTS=false.
# ---------------------------------------------------------------------------

_TEST_SEQUENCE = [
    {"stage": "SYSTEM",     "type": "info",    "message": "Signal Agent ready — waiting for input"},
    {"stage": "TRANSCRIBE", "type": "info",    "message": "Transcribing audio… (demo event)"},
    {"stage": "CLASSIFY",   "type": "info",    "message": "Classifying signal: BUG detected"},
    {"stage": "CLASSIFY",   "type": "success", "message": "Classification complete",
     "meta": {"type": "BUG", "urgency": "8", "customer": "Jane Smith", "company": "Acme Corp"}},
    {"stage": "MEMORY",     "type": "info",    "message": "Searching Senso for similar signals…"},
    {"stage": "MEMORY",     "type": "warning", "message": "4 similar signals found from other customers",
     "meta": {"frequency": "4"}},
    {"stage": "ROUTE",      "type": "info",    "message": "Routing: BUG urgency=8 + freq=4 → P1 Jira + Slack"},
    {"stage": "JIRA",       "type": "success", "message": "P1 Bug ticket created",
     "meta": {"ticket": "ENG-42", "url": "https://yourco.atlassian.net/browse/ENG-42"}},
    {"stage": "SLACK",      "type": "success", "message": "Alert sent to #engineering"},
    {"stage": "DIGEST",     "type": "success", "message": "CEO digest updated"},
]


async def _test_event_loop() -> None:
    """Cycle through demo events every 5 seconds."""
    await asyncio.sleep(2)  # brief startup delay
    idx = 0
    while True:
        if _sse_queues:  # only fire when someone is connected
            broadcast(_TEST_SEQUENCE[idx % len(_TEST_SEQUENCE)])
            idx += 1
        await asyncio.sleep(5)


# ---------------------------------------------------------------------------
# App lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    demo = os.environ.get("DEMO_TEST_EVENTS", "true").lower() != "false"
    task = asyncio.create_task(_test_event_loop()) if demo else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="Signal Agent", lifespan=lifespan)

frontend_origin = os.environ.get("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------

async def _sse_stream(queue: asyncio.Queue, request: Request) -> AsyncGenerator[str, None]:
    # Connected heartbeat
    hello = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "stage": "SYSTEM",
        "message": "Signal Agent backend connected",
        "type": "info",
    }
    yield f"event: activity\ndata: {json.dumps(hello)}\n\n"

    try:
        while True:
            # Also check if the client has disconnected
            if await request.is_disconnected():
                break
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15.0)
                yield f"event: activity\ndata: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                yield ": ping\n\n"
    finally:
        _sse_queues.remove(queue)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "clients": len(_sse_queues)}


@app.get("/alerts/stream")
async def alerts_stream(request: Request):
    """SSE stream of agent activity events."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=200)
    _sse_queues.append(queue)
    return StreamingResponse(
        _sse_stream(queue, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """Receive an audio file and trigger the signal pipeline."""
    contents = await file.read()

    broadcast({
        "stage": "SYSTEM",
        "type": "info",
        "message": f"Received file: {file.filename} ({len(contents):,} bytes)",
    })

    try:
        from backend.pipeline import run_pipeline  # noqa: PLC0415
        asyncio.create_task(
            run_pipeline(
                {"type": "audio", "content": contents, "filename": file.filename},
                broadcast=broadcast,
            )
        )
    except ImportError:
        broadcast({
            "stage": "SYSTEM",
            "type": "warning",
            "message": "Pipeline not yet wired — file received, standing by",
        })

    return {"status": "accepted", "filename": file.filename}


@app.post("/webhook/email")
async def webhook_email(request: Request):
    """Inbound email webhook (SendGrid / Mailgun)."""
    body = await request.json()

    broadcast({
        "stage": "SYSTEM",
        "type": "info",
        "message": f"Email received from {body.get('from', 'unknown')}",
    })

    try:
        from backend.pipeline import run_pipeline  # noqa: PLC0415
        asyncio.create_task(
            run_pipeline(
                {"type": "email", "content": body.get("text", ""), "raw": body},
                broadcast=broadcast,
            )
        )
    except ImportError:
        broadcast({
            "stage": "SYSTEM",
            "type": "warning",
            "message": "Pipeline not yet wired — email received, standing by",
        })

    return {"status": "accepted"}


@app.post("/monitor")
async def monitor(request: Request):
    """Manual trigger for demo use — POST raw signal text."""
    body = await request.json()

    broadcast({
        "stage": "SYSTEM",
        "type": "info",
        "message": "Manual signal trigger received",
    })

    try:
        from backend.pipeline import run_pipeline  # noqa: PLC0415
        asyncio.create_task(
            run_pipeline(
                {"type": "email", "content": body.get("text", ""), "raw": body},
                broadcast=broadcast,
            )
        )
    except ImportError:
        broadcast({
            "stage": "SYSTEM",
            "type": "warning",
            "message": "Pipeline not yet wired — trigger received, standing by",
        })

    return {"status": "accepted"}


@app.get("/digest")
async def get_digest():
    """Return the current CEO digest."""
    try:
        from backend.agents.digest import get_current_digest  # noqa: PLC0415
        return await get_current_digest()
    except ImportError:
        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "summary": "No signals processed yet.",
            "signal_counts": {},
            "top_themes": [],
            "churn_risks": [],
            "actions_taken": 0,
        }


@app.get("/signals")
async def get_signals():
    """Return all processed signals."""
    return {"signals": []}
