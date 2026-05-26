"use client";
import { useState } from "react";
import { RefreshCw, Brain, CheckCircle, AlertCircle } from "lucide-react";
import { triggerFetch, triggerAnalysis } from "@/lib/api";

interface Props { onRefresh: () => void }
type Status = "idle" | "loading" | "success" | "error";

export default function ControlPanel({ onRefresh }: Props) {
  const [fetchStatus, setFetchStatus] = useState<Status>("idle");
  const [analyzeStatus, setAnalyzeStatus] = useState<Status>("idle");
  const [message, setMessage] = useState("");
  const [progress, setProgress] = useState(0);

  const runWithProgress = async (fn: () => Promise<void>) => {
    setProgress(0);
    const tick = setInterval(() => setProgress((p) => Math.min(p + Math.random() * 18, 88)), 300);
    try {
      await fn();
      setProgress(100);
    } finally {
      clearInterval(tick);
      setTimeout(() => setProgress(0), 800);
    }
  };

  const handleFetch = () => runWithProgress(async () => {
    setFetchStatus("loading");
    setMessage("");
    try {
      const res = await triggerFetch(["reddit", "twitter", "youtube", "instagram"], 30);
      const newCount = res.inserted ?? 0;
      const updCount = res.updated ?? 0;
      setMessage(
        `${res.fetched} posts fetched · ${newCount} new · ${updCount} updated · ${res.mode} mode`
      );
      setFetchStatus("success");
      onRefresh();
    } catch (err: any) {
      setMessage(`Error: ${err?.response?.data?.detail ?? err?.message ?? "unknown"}`);
      setFetchStatus("error");
    }
  });

  const handleAnalyze = () => runWithProgress(async () => {
    setAnalyzeStatus("loading");
    setMessage("");
    try {
      const res = await triggerAnalysis(false);
      setMessage(`Analyzed ${res.analyzed} posts`);
      setAnalyzeStatus("success");
      onRefresh();
    } catch {
      setMessage("Analysis failed");
      setAnalyzeStatus("error");
    }
  });

  const isLoading = fetchStatus === "loading" || analyzeStatus === "loading";
  const isError = fetchStatus === "error" || analyzeStatus === "error";

  return (
    <div className="card-glass space-y-3">
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div className="flex gap-3">
          <button onClick={handleFetch} disabled={isLoading} className="btn-primary">
            <RefreshCw size={14} className={fetchStatus === "loading" ? "animate-spin" : ""} />
            {fetchStatus === "loading" ? "Fetching…" : "Fetch Trends"}
          </button>
          <button onClick={handleAnalyze} disabled={isLoading} className="btn-ghost">
            <Brain size={14} className={analyzeStatus === "loading" ? "animate-pulse" : ""} />
            {analyzeStatus === "loading" ? "Analyzing…" : "Run AI Analysis"}
          </button>
        </div>

        {message && (
          <div className="flex items-center gap-2 text-xs">
            {isError
              ? <AlertCircle size={13} className="text-red-400 shrink-0" />
              : <CheckCircle size={13} className="text-emerald-400 shrink-0" />}
            <span className={isError ? "text-red-400" : "text-emerald-400"}>{message}</span>
          </div>
        )}
      </div>

      {/* Progress bar */}
      {progress > 0 && (
        <div className="h-0.5 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-500 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
}
