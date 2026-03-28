/**
 * SSE proxy — forwards the FastAPI /alerts/stream to the browser.
 * Browser connects to same-origin /api/stream, avoiding WSL2 cross-origin issues.
 */

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8080";

export async function GET() {
  let backendRes: Response;
  try {
    backendRes = await fetch(`${BACKEND_URL}/alerts/stream`, {
      headers: { Accept: "text/event-stream" },
      // @ts-expect-error - Node fetch supports duplex
      duplex: "half",
    });
  } catch {
    // Backend not up yet — return a single error event
    const body = `event: activity\ndata: ${JSON.stringify({
      id: "err",
      timestamp: new Date().toISOString(),
      stage: "SYSTEM",
      type: "error",
      message: "Backend not reachable at " + BACKEND_URL,
    })}\n\n`;
    return new Response(body, {
      headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache" },
    });
  }

  return new Response(backendRes.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
