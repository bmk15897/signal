"""
Signal — FastAPI backend
Person 2 owns this file (API routes and webhook receivers only).
"""

import asyncio
import json
import os
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI, File, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Load .env from project root before anything else touches env vars
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Make `from agents.xxx import` work when uvicorn is launched from project root
sys.path.insert(0, os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# In-process SSE broadcast bus + recent event buffer
# ---------------------------------------------------------------------------

_sse_queues: list[asyncio.Queue] = []
_event_buffer: list[dict] = []   # last 50 events, replayed to new clients
_BUFFER_SIZE = 50


def broadcast(event: dict) -> None:
    """Broadcast an activity event to all connected SSE clients."""
    payload = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        **event,
    }
    # Keep a rolling buffer so new clients can see recent events
    _event_buffer.append(payload)
    if len(_event_buffer) > _BUFFER_SIZE:
        _event_buffer.pop(0)

    for q in list(_sse_queues):
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            pass


# ---------------------------------------------------------------------------
# Demo test event loop — cycles through fake pipeline events every 5s.
# Enabled by default; disable with DEMO_TEST_EVENTS=false in .env.
# ---------------------------------------------------------------------------

_TEST_SEQUENCE = [
    {"stage": "SYSTEM",     "type": "info",    "message": "Signal Agent ready — waiting for input"},
    {"stage": "TRANSCRIBE", "type": "info",    "message": "Transcribing audio… (demo event)"},
    {"stage": "CLASSIFY",   "type": "info",    "message": "Classifying signal: BUG detected"},
    {"stage": "CLASSIFY",   "type": "success", "message": "Classification complete",
     "meta": {"type": "BUG", "urgency": "8", "customer": "Jane Smith", "company": "Acme Corp"}},
    {"stage": "MEMORY",     "type": "info",    "message": "Searching Senso for similar signals…"},
    {"stage": "MEMORY",     "type": "warning", "message": "4 similar signals found",
     "meta": {"frequency": "4"}},
    {"stage": "ROUTE",      "type": "info",    "message": "Routing: BUG urgency=8 + freq=4 → P1 Jira + Slack"},
    {"stage": "JIRA",       "type": "success", "message": "P1 Bug ticket created",
     "meta": {"ticket": "ENG-42", "url": "https://yourco.atlassian.net/browse/ENG-42"}},
    {"stage": "SLACK",      "type": "success", "message": "Alert sent to #engineering"},
    {"stage": "DIGEST",     "type": "success", "message": "CEO digest updated"},
]


async def _test_event_loop() -> None:
    await asyncio.sleep(2)
    idx = 0
    while True:
        if _sse_queues:
            broadcast(_TEST_SEQUENCE[idx % len(_TEST_SEQUENCE)])
            idx += 1
        await asyncio.sleep(5)


# ---------------------------------------------------------------------------
# App lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    demo = os.environ.get("DEMO_TEST_EVENTS", "false").lower() != "false"
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
    hello = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "stage": "SYSTEM",
        "message": "Signal Agent backend connected",
        "type": "info",
    }
    yield f"event: activity\ndata: {json.dumps(hello)}\n\n"

    # Replay recent events so the feed is populated even if pipeline already ran
    for past_event in list(_event_buffer):
        yield f"event: activity\ndata: {json.dumps(past_event)}\n\n"

    try:
        while True:
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


def _run_pipeline_task(coro):
    """Create a task that logs exceptions to the activity feed instead of swallowing them."""
    async def wrapper():
        try:
            await coro
        except Exception as e:
            import traceback
            broadcast({
                "stage": "SYSTEM",
                "type": "error",
                "message": f"Pipeline error: {e}",
                "meta": {"traceback": traceback.format_exc()[-300:]},
            })
            print(f"[pipeline] ERROR: {traceback.format_exc()}")
    asyncio.create_task(wrapper())


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """Receive an audio file and trigger the signal pipeline."""
    import base64
    contents = await file.read()

    broadcast({
        "stage": "SYSTEM",
        "type": "info",
        "message": f"Received file: {file.filename} ({len(contents):,} bytes)",
    })

    try:
        from pipeline import run_pipeline  # noqa: PLC0415
        # Pipeline expects base64-encoded string for audio type
        _run_pipeline_task(run_pipeline(
            {"type": "audio", "content": base64.b64encode(contents).decode(), "filename": file.filename},
            broadcast=broadcast,
        ))
    except ImportError as e:
        broadcast({"stage": "SYSTEM", "type": "error", "message": f"Import error: {e}"})

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
        from pipeline import run_pipeline  # noqa: PLC0415
        _run_pipeline_task(run_pipeline(
            {"type": "email", "content": body.get("text", ""), "raw": body},
            broadcast=broadcast,
        ))
    except ImportError as e:
        broadcast({"stage": "SYSTEM", "type": "error", "message": f"Import error: {e}"})

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
        from pipeline import run_pipeline  # noqa: PLC0415
        _run_pipeline_task(run_pipeline(
            {"type": body.get("type", "email"), "content": body.get("text", body.get("content", "")), "raw": body},
            broadcast=broadcast,
        ))
    except ImportError as e:
        broadcast({"stage": "SYSTEM", "type": "error", "message": f"Import error: {e}"})

    return {"status": "accepted"}


@app.get("/search")
async def search_signals(q: str = Query(..., description="Search query")):
    """Search Senso KB — used by the CEO chat assistant."""
    try:
        from agents.memory import search_memory, SearchInput  # noqa: PLC0415
        result = await search_memory(SearchInput(
            key_phrases=q.split()[:5],
            classification="",
        ))
        return {
            "query": q,
            "frequency": result.frequency,
            "results": result.related_signals,
        }
    except Exception as e:
        return {"query": q, "frequency": 0, "results": [], "error": str(e)}


@app.get("/digest")
async def get_digest():
    """Return the current CEO digest."""
    try:
        from agents.digest import generate_digest  # noqa: PLC0415
        return generate_digest()
    except Exception as e:
        return {
            "markdown": f"Digest unavailable: {e}",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "signal_count": 0,
        }


@app.get("/signals")
async def get_signals():
    """Return all processed signals."""
    return {"signals": []}
