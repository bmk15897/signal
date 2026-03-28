"use client";

import { useState } from "react";
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
  const [chatOpen, setChatOpen] = useState(false);

  const runtime = useChatRuntime({
    transport: new AssistantChatTransport({
      api: "/api/chat",
    }),
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="flex h-dvh w-full bg-zinc-950 overflow-hidden">

        {/* Left panel — Upload + Digest */}
        <div className="flex flex-col w-1/2 border-r border-zinc-800 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-3 px-5 py-4 border-b border-zinc-800 shrink-0">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white font-black text-sm shrink-0">
              S
            </div>
            <div className="flex flex-col">
              <span className="text-zinc-100 font-bold text-lg leading-none">Signal</span>
              <span className="text-zinc-500 text-xs mt-0.5">Autonomous Engineering Action Agent</span>
            </div>
          </div>

          {/* Upload zone */}
          <div className="px-4 pt-4 pb-3 shrink-0">
            <UploadZone />
          </div>

          {/* CEO Digest */}
          <div className="px-4 pb-4 flex-1 overflow-y-auto">
            <DigestPanel />
          </div>
        </div>

        {/* Right panel — Live Activity Feed */}
        <div className="flex flex-col w-1/2 min-w-0">
          <ActivityFeed />
        </div>

        {/* Floating chat button */}
        <button
          onClick={() => setChatOpen(v => !v)}
          className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 shadow-lg shadow-violet-900/40 flex items-center justify-center hover:scale-105 active:scale-95 transition-transform"
          aria-label="Ask Signal"
        >
          {chatOpen ? (
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="text-white">
              <path d="M4 4L16 16M16 4L4 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          ) : (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-white">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          )}
        </button>

        {/* Chat drawer */}
        {chatOpen && (
          <div className="fixed bottom-24 right-6 z-50 w-[380px] h-[520px] rounded-2xl border border-zinc-700 bg-zinc-950 shadow-2xl shadow-black/60 overflow-hidden flex flex-col">
            {/* Chat header */}
            <div className="flex items-center gap-2.5 px-4 py-3 border-b border-zinc-800 shrink-0 bg-zinc-900/80">
              <div className="w-6 h-6 rounded-md bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white text-[10px] font-black shrink-0">
                S
              </div>
              <div>
                <p className="text-zinc-100 font-semibold text-sm leading-none">Ask Signal</p>
                <p className="text-zinc-500 text-[10px] mt-0.5">Query your customer intelligence</p>
              </div>
            </div>
            <div className="flex-1 overflow-hidden">
              <Thread />
            </div>
          </div>
        )}
      </div>
    </AssistantRuntimeProvider>
  );
}
