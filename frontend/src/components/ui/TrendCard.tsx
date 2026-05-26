import clsx from "clsx";
import { ExternalLink, ThumbsUp, MessageCircle, Share2, Clock, Zap } from "lucide-react";
import type { TrendPost } from "@/types";

const SOURCE_COLORS: Record<string, string> = {
  reddit:    "bg-orange-500/15 text-orange-400 border-orange-500/25",
  twitter:   "bg-sky-500/15 text-sky-400 border-sky-500/25",
  youtube:   "bg-red-500/15 text-red-400 border-red-500/25",
  instagram: "bg-pink-500/15 text-pink-400 border-pink-500/25",
  news:      "bg-yellow-500/15 text-yellow-400 border-yellow-500/25",
};

const SENTIMENT_COLORS: Record<string, string> = {
  positive: "bg-emerald-500/15 text-emerald-400",
  negative: "bg-red-500/15 text-red-400",
  neutral:  "bg-gray-700/50 text-gray-400",
};

const PHASE_CONFIG: Record<string, { color: string; bg: string; dot: string }> = {
  Viral:    { color: "text-yellow-400",  bg: "bg-yellow-500/15 border-yellow-500/25",  dot: "bg-yellow-400" },
  Emerging: { color: "text-emerald-400", bg: "bg-emerald-500/15 border-emerald-500/25", dot: "bg-emerald-400" },
  Declining:{ color: "text-red-400",     bg: "bg-red-500/15 border-red-500/25",         dot: "bg-red-400" },
  Stable:   { color: "text-gray-400",    bg: "bg-gray-700/40 border-gray-600/30",       dot: "bg-gray-500" },
};

function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return n.toLocaleString();
}

function relativeTime(ts: string): string {
  if (!ts) return "";
  const diff = (Date.now() - new Date(ts).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export default function TrendCard({ post }: { post: TrendPost }) {
  const platform = post.platform || post.source || "reddit";
  const sentiment = post.sentiment_label || post.sentiment;
  const topic = post.topic || post.topic_label;
  const likes = post.engagement?.likes ?? post.score ?? 0;
  const comments = post.engagement?.comments ?? 0;
  const shares = post.engagement?.shares ?? 0;
  const timeAgo = relativeTime(post.timestamp || post.fetched_at || "");
  const phase = post.trend_phase ?? "Stable";
  const phaseConf = PHASE_CONFIG[phase] ?? PHASE_CONFIG.Stable;
  const virality = post.virality_score;

  return (
    <div className={clsx(
      "card-glass flex flex-col gap-3 group",
      "hover:-translate-y-0.5 hover:border-gray-600/60",
      post.is_spike && "border-yellow-500/30 shadow-yellow-500/10 shadow-lg"
    )}>
      {/* Top row */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex gap-1.5 flex-wrap">
          <span className={clsx("badge border text-[11px]", SOURCE_COLORS[platform] ?? "bg-gray-700 text-gray-300 border-gray-600")}>
            {platform}
          </span>
          {sentiment && (
            <span className={clsx("badge text-[11px]", SENTIMENT_COLORS[sentiment])}>
              {sentiment}
            </span>
          )}
          {/* Phase badge */}
          <span className={clsx("badge border text-[11px] flex items-center gap-1", phaseConf.bg)}>
            <span className={clsx("w-1.5 h-1.5 rounded-full shrink-0", phaseConf.dot,
              phase === "Viral" && "animate-pulse"
            )} />
            <span className={phaseConf.color}>{phase}</span>
          </span>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {post.is_spike && <Zap size={12} className="text-yellow-400" />}
          {post.trend_score != null && (
            <span className={clsx(
              "text-xs font-bold px-1.5 py-0.5 rounded-lg tabular-nums",
              post.trend_score >= 8.5 ? "bg-orange-500/20 text-orange-400" :
              post.trend_score >= 7.0 ? "bg-brand-500/20 text-brand-500" :
              "bg-gray-800 text-gray-400"
            )}>
              {post.trend_score.toFixed(1)}
            </span>
          )}
        </div>
      </div>

      {/* Title */}
      <a
        href={post.url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-sm font-semibold text-white hover:text-brand-500 transition-colors line-clamp-2 flex items-start gap-1 group/link"
      >
        <span>{post.title}</span>
        <ExternalLink size={11} className="mt-0.5 shrink-0 opacity-0 group-hover/link:opacity-50 transition-opacity" />
      </a>

      {/* AI Summary */}
      {post.ai_summary && (
        <p className="text-[11px] text-gray-500 leading-relaxed line-clamp-2 italic">
          {post.ai_summary}
        </p>
      )}

      {/* Virality bar */}
      {virality != null && virality > 0 && (
        <div className="space-y-1">
          <div className="flex items-center justify-between text-[10px] text-gray-500">
            <span>Virality probability</span>
            <span className={clsx("font-semibold",
              virality >= 70 ? "text-yellow-400" :
              virality >= 45 ? "text-brand-500" : "text-gray-400"
            )}>{virality}%</span>
          </div>
          <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
            <div
              className={clsx("h-full rounded-full transition-all duration-700",
                virality >= 70 ? "bg-yellow-400" :
                virality >= 45 ? "bg-brand-500" : "bg-gray-600"
              )}
              style={{ width: `${virality}%` }}
            />
          </div>
        </div>
      )}

      {/* Topic tag */}
      {topic && (
        <span className="self-start badge bg-brand-500/10 text-brand-500/80 text-[10px] max-w-full truncate">
          {topic}
        </span>
      )}

      {/* Footer */}
      <div className="flex items-center gap-3 text-[11px] text-gray-500 mt-auto pt-2 border-t border-gray-800/60">
        <span className="flex items-center gap-1"><ThumbsUp size={10} /> {fmt(likes)}</span>
        <span className="flex items-center gap-1"><MessageCircle size={10} /> {fmt(comments)}</span>
        {shares > 0 && <span className="flex items-center gap-1"><Share2 size={10} /> {fmt(shares)}</span>}
        {timeAgo && (
          <span className="flex items-center gap-1 ml-auto text-gray-600">
            <Clock size={10} /> {timeAgo}
          </span>
        )}
      </div>
    </div>
  );
}
