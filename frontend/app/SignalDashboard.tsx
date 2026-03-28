"use client";

import { AssistantRuntimeProvider } from "@assistant-ui/react";
import {
  useChatRuntime,
  AssistantChatTransport,
} from "@assistant-ui/react-ai-sdk";
import { Thread } from "@/components/assistant-ui/thread";
import { ActivityFeed } from "./components/ActivityFeed";
import { UploadZone } from "./components/UploadZone";
import { DigestPanel } from "./components/DigestPanel";

export function SignalDashboard() {
  const runtime = useChatRuntime({
    transport: new AssistantChatTransport({
      api: "/api/chat",
    }),
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="flex h-dvh w-full bg-zinc-950 overflow-hidden">
        {/* Left panel — Chat */}
        <div className="flex flex-col w-1/2 border-r border-zinc-800 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-3 px-5 py-4 border-b border-zinc-800 shrink-0">
            <div className="flex flex-col">
              <span className="text-zinc-100 font-bold text-lg leading-none">
                Signal
              </span>
              <span className="text-zinc-500 text-xs mt-0.5">
                Autonomous Engineering Action Agent
              </span>
            </div>
          </div>

          {/* Upload zone */}
          <div className="px-4 pt-4 pb-2 shrink-0">
            <UploadZone />
          </div>

          {/* CEO Digest */}
          <div className="px-4 pb-2 shrink-0">
            <DigestPanel />
          </div>

          {/* Chat */}
          <div className="flex-1 overflow-hidden">
            <Thread />
          </div>
        </div>

        {/* Right panel — Live Activity Feed */}
        <div className="flex flex-col w-1/2 min-w-0">
          <ActivityFeed />
        </div>
      </div>
    </AssistantRuntimeProvider>
  );
}
