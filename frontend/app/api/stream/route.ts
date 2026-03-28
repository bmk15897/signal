import { randomUUID } from "crypto";

// Shared in-process event bus for SSE clients
// In production this would be replaced by Redis pub/sub or similar
const clients = new Set<ReadableStreamDefaultController<string>>();

export function broadcastActivity(event: {
  stage: string;
  message: string;
  type: "info" | "success" | "warning" | "error";
  meta?: Record<string, string>;
}) {
  const payload = JSON.stringify({
    id: randomUUID(),
    timestamp: new Date().toISOString(),
    ...event,
  });
  const data = `event: activity\ndata: ${payload}\n\n`;
  for (const ctrl of clients) {
    try {
      ctrl.enqueue(data);
    } catch {
      clients.delete(ctrl);
    }
  }
}

export async function GET() {
  let ctrl!: ReadableStreamDefaultController<string>;

  const stream = new ReadableStream<string>({
    start(controller) {
      ctrl = controller;
      clients.add(controller);

      // Send a connected heartbeat
      const hello = JSON.stringify({
        id: randomUUID(),
        timestamp: new Date().toISOString(),
        stage: "SYSTEM",
        message: "Signal Agent connected — waiting for input",
        type: "info",
      });
      controller.enqueue(`event: activity\ndata: ${hello}\n\n`);

      // Keep-alive ping every 15s
      const ping = setInterval(() => {
        try {
          controller.enqueue(`: ping\n\n`);
        } catch {
          clearInterval(ping);
        }
      }, 15_000);
    },
    cancel() {
      clients.delete(ctrl);
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
