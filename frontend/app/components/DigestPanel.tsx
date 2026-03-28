"use client";

import { useCallback, useEffect, useState } from "react";

type Digest = {
  generated_at: string;
  summary: string;
  signal_counts: Record<string, number>;
  top_themes: string[];
  churn_risks: string[];
  actions_taken: number;
};

export function DigestPanel() {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDigest = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8080/digest");
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

  return (
    <div className="flex flex-col gap-3 p-4 border border-zinc-800 rounded-lg bg-zinc-900/50">
      <div className="flex items-center justify-between">
        <span className="text-zinc-200 font-semibold text-sm">CEO Digest</span>
        <button
          onClick={fetchDigest}
          className="text-zinc-600 hover:text-zinc-400 text-xs transition-colors"
        >
          {loading ? "refreshing…" : "refresh"}
        </button>
      </div>

      {error && (
        <p className="text-red-400 text-xs">Backend not reachable: {error}</p>
      )}

      {!digest && !error && !loading && (
        <p className="text-zinc-600 text-xs">No digest yet.</p>
      )}

      {digest && (
        <>
          <p className="text-zinc-400 text-xs leading-relaxed">
            {digest.summary}
          </p>

          {digest.signal_counts &&
            Object.keys(digest.signal_counts).length > 0 && (
              <div className="flex flex-wrap gap-2">
                {Object.entries(digest.signal_counts).map(([type, count]) => (
                  <span
                    key={type}
                    className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400 border border-zinc-700"
                  >
                    {type} × {count}
                  </span>
                ))}
              </div>
            )}

          {digest.churn_risks?.length > 0 && (
            <div className="flex flex-col gap-1">
              <span className="text-red-400 text-xs font-medium">
                Churn risks
              </span>
              {digest.churn_risks.map((r, i) => (
                <span key={i} className="text-zinc-500 text-xs pl-2">
                  • {r}
                </span>
              ))}
            </div>
          )}

          <p className="text-zinc-600 text-[10px]">
            {digest.actions_taken ?? 0} actions taken ·{" "}
            {digest.generated_at
              ? new Date(digest.generated_at).toLocaleString()
              : ""}
          </p>
        </>
      )}
    </div>
  );
}
