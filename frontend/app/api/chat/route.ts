import { openai } from "@ai-sdk/openai";
import { frontendTools } from "@assistant-ui/react-ai-sdk";
import {
  JSONSchema7,
  streamText,
  convertToModelMessages,
  type UIMessage,
} from "ai";

const SYSTEM = `You are the Signal intelligence assistant. You help CEOs and product leaders
understand patterns in customer signals — bugs, feature requests, churn risks, and praise —
that have been automatically captured by the Signal agent.

Answer questions about customer trends, recurring issues, top feature requests, and churn risks
based on what the agent has processed. Be concise and action-oriented. If you don't have data
on something, say so rather than making it up.`;

export async function POST(req: Request) {
  const {
    messages,
    system,
    tools,
  }: {
    messages: UIMessage[];
    system?: string;
    tools?: Record<string, { description?: string; parameters: JSONSchema7 }>;
  } = await req.json();

  const result = streamText({
    model: openai("gpt-4o"),
    messages: await convertToModelMessages(messages),
    system: system ?? SYSTEM,
    tools: {
      ...frontendTools(tools ?? {}),
    },
  });

  return result.toUIMessageStreamResponse();
}
