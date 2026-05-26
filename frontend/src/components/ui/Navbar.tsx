"use client";
import { useEffect, useState } from "react";
import { Zap, Clock, Radio } from "lucide-react";

interface Props { lastUpdated?: string }

export default function Navbar({ lastUpdated }: Props) {
  const [liveSpikes, setLiveSpikes] = useState<number | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
    const url = `${base}/v1/dashboard/stream`;
    let es: EventSource;
    let retryTimeout: ReturnType<typeof setTimeout>;

    const connect = () => {
      es = new EventSource(url);
      es.onopen = () => setConnected(true);
      es.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.spike_count != null) setLiveSpikes(data.spike_count);
        } catch {}
      };
      es.onerror = () => {
        setConnected(false);
        es.close();
        retryTimeout = setTimeout(connect, 15_000);
      };
    };

    connect();
    return () => { es?.close(); clearTimeout(retryTimeout); };
  }, []);

  const timeStr = lastUpdated
    ? new Date(lastUpdated).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
    : null;

  return (
    <header className="sticky top-0 z-50 border-b border-white/[0.06] backdrop-blur-md"
      style={{ background: "rgba(3,7,18,0.85)" }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-brand-500/20 border border-brand-500/30 flex items-center justify-center">
            <Zap size={14} className="text-brand-500" />
          </div>
          <span className="font-bold text-white text-base tracking-tight">HypeTrace</span>
          <span className="hidden sm:inline text-xs text-gray-600 font-medium">AI</span>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3 text-xs">
          {liveSpikes != null && liveSpikes > 0 && (
            <span className="hidden sm:flex items-center gap-1.5 bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 px-2.5 py-1 rounded-full font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse" />
              {liveSpikes} spike{liveSpikes > 1 ? "s" : ""} live
            </span>
          )}
          {timeStr && (
            <span className="hidden md:flex items-center gap-1 text-gray-600">
              <Clock size={10} /> {timeStr}
            </span>
          )}
          <span className="flex items-center gap-1.5 text-gray-500">
            <Radio size={11} className={connected ? "text-emerald-400" : "text-gray-600"} />
            <span className={connected ? "text-emerald-400" : "text-gray-600"}>
              {connected ? "Live" : "Connecting…"}
            </span>
          </span>
        </div>
      </div>
    </header>
  );
}
