"use client";

import { useCallback, useEffect, useState } from "react";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8080";

type Digest = {
  markdown: string;
  generated_at: string;
  signal_count: number;
};

type SignalType = "BUG" | "CHURN_RISK" | "FEATURE_REQUEST" | "PRAISE" | "QUESTION";

const TYPE_CONFIG: Record<string, { color: string; bg: string; border: string; icon: string; label: string }> = {
  BUG:             { color: "text-red-400",    bg: "bg-red-950/40",    border: "border-red-800/50",    icon: "⚠", label: "Bug" },
  CHURN_RISK:      { color: "text-orange-400", bg: "bg-orange-950/40", border: "border-orange-800/50", icon: "🔥", label: "Churn Risk" },
  FEATURE_REQUEST: { color: "text-blue-400",   bg: "bg-blue-950/40",   border: "border-blue-800/50",   icon: "✦", label: "Feature" },
  PRAISE:          { color: "text-emerald-400",bg: "bg-emerald-950/40",border: "border-emerald-800/50",icon: "★", label: "Praise" },
  QUESTION:        { color: "text-zinc-400",   bg: "bg-zinc-900/40",   border: "border-zinc-700/50",   icon: "?", label: "Question" },
};

function parseMarkdown(markdown: string) {
  const lines = markdown.split("\n");
  const sections: { heading: string; lines: string[] }[] = [];
  let current: { heading: string; lines: string[] } | null = null;

  for (const line of lines) {
    if (line.startsWith("## ")) {
      if (current) sections.push(current);
      current = { heading: line.replace(/^##\s+/, ""), lines: [] };
    } else if (line.startsWith("# ")) {
      // skip top-level heading
    } else if (current) {
      current.lines.push(line);
    }
  }
  if (current) sections.push(current);
  return sections;
}

function extractStats(markdown: string) {
  const bugs = (markdown.match(/\bBUG\b/gi) || []).length;
  const churns = (markdown.match(/\bCHURN_RISK\b|\bchurn\b/gi) || []).length;
  const features = (markdown.match(/\bFEATURE_REQUEST\b|\bfeature\b/gi) || []).length;
  return { bugs, churns, features };
}

function UrgencyDot({ level }: { level: number }) {
  const color =
    level >= 8 ? "bg-red-500" :
    level >= 5 ? "bg-orange-500" :
    "bg-zinc-600";
  return (
    <span className={`inline-block w-1.5 h-1.5 rounded-full ${color} mr-1`} />
  );
}

function StatCard({ value, label, color }: { value: number; label: string; color: string }) {
  return (
    <div className={`flex flex-col items-center justify-center px-4 py-3 rounded-lg border ${color} flex-1`}>
      <span className="text-2xl font-black tabular-nums leading-none">{value}</span>
      <span className="text-[10px] uppercase tracking-widest mt-1 opacity-70 font-semibold">{label}</span>
    </div>
  );
}

function SectionBlock({ heading, lines }: { heading: string; lines: string[] }) {
  const type = Object.keys(TYPE_CONFIG).find(t =>
    heading.toUpperCase().includes(t)
  );
  const cfg = type ? TYPE_CONFIG[type] : TYPE_CONFIG["QUESTION"];

  const bullets = lines.filter(l => l.trim().startsWith("-") || l.trim().startsWith("•"));
  const rest = lines.filter(l => !l.trim().startsWith("-") && !l.trim().startsWith("•") && l.trim());

  return (
    <div className={`rounded-lg border ${cfg.border} ${cfg.bg} p-3 gap-1.5 flex flex-col`}>
      <div className="flex items-center gap-2 mb-0.5">
        <span className={`text-base leading-none ${cfg.color}`}>{cfg.icon}</span>
        <span className={`text-xs font-bold uppercase tracking-wider ${cfg.color}`}>{heading}</span>
      </div>
      {rest.map((line, i) => (
        <p key={i} className="text-zinc-300 text-xs leading-relaxed">{line}</p>
      ))}
      {bullets.map((line, i) => {
        const text = line.replace(/^[-•]\s*/, "");
        // Try to extract urgency like "urgency: 8" or "8/10"
        const urgencyMatch = text.match(/urgency[:\s]+(\d+)/i) || text.match(/(\d+)\/10/);
        const urgency = urgencyMatch ? parseInt(urgencyMatch[1]) : 0;
        return (
          <div key={i} className="flex items-start gap-1.5 group">
            {urgency > 0 && <UrgencyDot level={urgency} />}
            {urgency === 0 && <span className={`mt-1 w-1 h-1 rounded-full ${cfg.color} opacity-60 shrink-0`} />}
            <span className="text-zinc-300 text-xs leading-relaxed">{text}</span>
          </div>
        );
      })}
    </div>
  );
}

export function DigestPanel() {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  const fetchDigest = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/backend/digest`);
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();
      setDigest(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load digest");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDigest();
    const timer = setInterval(fetchDigest, 30_000);
    return () => clearInterval(timer);
  }, [fetchDigest]);

  const stats = digest ? extractStats(digest.markdown) : null;
  const sections = digest ? parseMarkdown(digest.markdown) : [];

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 backdrop-blur-sm overflow-hidden">
      {/* Header bar */}
      <div
        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-zinc-800/40 transition-colors"
        onClick={() => setExpanded(v => !v)}
      >
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-md bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white text-[10px] font-black shrink-0">
            C
          </div>
          <div>
            <p className="text-zinc-100 font-bold text-sm leading-none">CEO Digest</p>
            {digest && (
              <p className="text-zinc-500 text-[10px] mt-0.5">
                {digest.signal_count ?? 0} signals ·{" "}
                {digest.generated_at
                  ? new Date(digest.generated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                  : ""}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {loading && (
            <span className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-pulse" />
          )}
          <button
            onClick={e => { e.stopPropagation(); fetchDigest(); }}
            className="text-zinc-600 hover:text-zinc-300 text-[10px] uppercase tracking-wider transition-colors px-2 py-1 rounded hover:bg-zinc-800"
          >
            ↻
          </button>
          <span className={`text-zinc-500 text-xs transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}>
            ▾
          </span>
        </div>
      </div>

      {/* Body */}
      {expanded && (
        <div className="border-t border-zinc-800 p-4 flex flex-col gap-3">
          {error && (
            <div className="rounded-lg bg-red-950/30 border border-red-800/40 px-3 py-2 text-red-400 text-xs">
              ⚠ {error}
            </div>
          )}

          {!digest && !error && !loading && (
            <p className="text-zinc-600 text-xs text-center py-4">No signals processed yet.</p>
          )}

          {stats && (
            <div className="flex gap-2">
              <StatCard value={stats.bugs}     label="Bugs"    color="border-red-800/40 text-red-400" />
              <StatCard value={stats.churns}   label="Churn"   color="border-orange-800/40 text-orange-400" />
              <StatCard value={stats.features} label="Features" color="border-blue-800/40 text-blue-400" />
            </div>
          )}

          {sections.length > 0 ? (
            <div className="flex flex-col gap-2">
              {sections.map((s, i) => (
                <SectionBlock key={i} heading={s.heading} lines={s.lines} />
              ))}
            </div>
          ) : digest && (
            // Fallback: raw markdown if no sections parsed
            <pre className="text-zinc-400 text-[11px] leading-relaxed whitespace-pre-wrap font-sans">
              {digest.markdown}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
