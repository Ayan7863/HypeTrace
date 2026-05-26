import clsx from "clsx";
import type { TopicSummary } from "@/types";

interface Props {
  topics: TopicSummary[];
  onTopicClick?: (label: string) => void;
  activeTopic?: string | null;
}

function SentimentBar({ value }: { value: number }) {
  const pct = Math.round(((value + 1) / 2) * 100);
  return (
    <div className="w-full h-1 bg-gray-800 rounded-full overflow-hidden">
      <div
        className={clsx("h-full rounded-full", value >= 0 ? "bg-emerald-500" : "bg-red-500")}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

export default function TopicsPanel({ topics, onTopicClick, activeTopic }: Props) {
  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">Topic Clusters</h3>
      <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
        {topics.map((t) => (
          <div
            key={t.topic_label}
            onClick={() => onTopicClick?.(t.topic_label)}
            className={clsx(
              "rounded-xl p-3 space-y-2 transition-colors",
              onTopicClick && "cursor-pointer",
              activeTopic === t.topic_label
                ? "bg-brand-500/20 ring-1 ring-brand-500/40"
                : "bg-gray-800/60 hover:bg-gray-800"
            )}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium text-white truncate">{t.topic_label}</span>
              <span className="text-xs text-brand-500 font-semibold shrink-0">
                🔥 {t.avg_trend_score.toFixed(1)}
              </span>
            </div>
            <SentimentBar value={t.avg_sentiment} />
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>{t.post_count} posts</span>
              <span>{t.top_sources.join(", ")}</span>
            </div>
          </div>
        ))}
        {topics.length === 0 && (
          <p className="text-sm text-gray-500 text-center py-6">No topics yet — run AI analysis</p>
        )}
      </div>
    </div>
  );
}
