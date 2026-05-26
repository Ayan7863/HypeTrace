import { Lightbulb, AlertTriangle, Rocket, Zap, TrendingUp, BarChart2 } from "lucide-react";
import clsx from "clsx";
import type { AiInsights } from "@/types";

interface Props { insights: AiInsights }

const SENTIMENT_BADGE: Record<string, string> = {
  positive: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  negative: "text-red-400 bg-red-500/10 border-red-500/20",
  mixed:    "text-yellow-400 bg-yellow-500/10 border-yellow-500/20",
};

function InsightItem({ text, color }: { text: string; color: string }) {
  return (
    <li className="flex gap-2 text-xs text-gray-400 leading-relaxed group/item">
      <span className={clsx("mt-0.5 shrink-0 font-bold transition-colors group-hover/item:scale-110", color)}>→</span>
      <span className="group-hover/item:text-gray-300 transition-colors">{text}</span>
    </li>
  );
}

function ConfidenceBar({ score, label }: { score: number; label: string }) {
  const color = score >= 75 ? "bg-emerald-500" : score >= 50 ? "bg-brand-500" : "bg-gray-600";
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[10px] text-gray-500">
        <span>{label}</span>
        <span className="font-semibold text-white">{score}%</span>
      </div>
      <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
        <div className={clsx("h-full rounded-full transition-all duration-700", color)} style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}

export default function AiInsightsPanel({ insights }: Props) {
  const sentimentClass = SENTIMENT_BADGE[insights.dominant_sentiment] ?? "text-gray-400 bg-gray-800 border-gray-700";

  // Derive confidence scores from data
  const dataConfidence = Math.min(95, 40 + insights.spike_count * 8 + (insights.avg_trend_score ?? 0) * 4);
  const viralityRisk = insights.spike_count > 0
    ? Math.min(90, 50 + insights.spike_count * 12)
    : Math.max(10, 30 - (insights.avg_trend_score ?? 0) * 2);

  return (
    <div className="card-glass space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <div className="w-5 h-5 rounded-md bg-brand-500/20 border border-brand-500/30 flex items-center justify-center">
              <Zap size={11} className="text-brand-500" />
            </div>
            AI Intelligence Report
          </h3>
          <p className="text-[11px] text-gray-600 mt-0.5 ml-7">Automated · updated on each analysis run</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {insights.spike_count > 0 && (
            <span className="text-xs bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 px-2.5 py-1 rounded-full font-medium flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse" />
              {insights.spike_count} viral spike{insights.spike_count > 1 ? "s" : ""}
            </span>
          )}
          {insights.dominant_sentiment && (
            <span className={clsx("text-xs border px-2.5 py-1 rounded-full font-medium capitalize", sentimentClass)}>
              {insights.dominant_sentiment} sentiment
            </span>
          )}
          {(insights.avg_trend_score ?? 0) > 0 && (
            <span className="text-xs bg-brand-500/10 text-brand-500 border border-brand-500/20 px-2.5 py-1 rounded-full font-medium">
              avg {insights.avg_trend_score}/10
            </span>
          )}
        </div>
      </div>

      {/* Summary */}
      <div className="relative pl-3 py-2 pr-3 rounded-r-lg"
        style={{ borderLeft: "2px solid rgba(79,110,247,0.5)", background: "rgba(79,110,247,0.04)" }}>
        <p className="text-sm text-gray-300 leading-relaxed">{insights.summary}</p>
      </div>

      {/* 4-column insights */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5">
        <div className="space-y-3">
          <p className="text-[10px] font-semibold text-emerald-400 flex items-center gap-1.5 uppercase tracking-widest">
            <Rocket size={10} /> Opportunities
          </p>
          <ul className="space-y-2">
            {insights.opportunities.map((o, i) => <InsightItem key={i} text={o} color="text-emerald-500" />)}
          </ul>
        </div>
        <div className="space-y-3">
          <p className="text-[10px] font-semibold text-red-400 flex items-center gap-1.5 uppercase tracking-widest">
            <AlertTriangle size={10} /> Pain Points
          </p>
          <ul className="space-y-2">
            {insights.pain_points.map((p, i) => <InsightItem key={i} text={p} color="text-red-500" />)}
          </ul>
        </div>
        <div className="space-y-3">
          <p className="text-[10px] font-semibold text-brand-500 flex items-center gap-1.5 uppercase tracking-widest">
            <Lightbulb size={10} /> Recommendations
          </p>
          <ul className="space-y-2">
            {insights.recommendations.map((r, i) => <InsightItem key={i} text={r} color="text-brand-500" />)}
          </ul>
        </div>
        <div className="space-y-3">
          <p className="text-[10px] font-semibold text-purple-400 flex items-center gap-1.5 uppercase tracking-widest">
            <TrendingUp size={10} /> Market Predictions
          </p>
          <ul className="space-y-2">
            {(insights.market_predictions ?? []).map((m, i) => <InsightItem key={i} text={m} color="text-purple-400" />)}
          </ul>
        </div>
      </div>

      {/* Confidence metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-3 border-t border-white/[0.05]">
        <div className="space-y-2">
          <p className="text-[10px] font-semibold text-gray-500 flex items-center gap-1.5 uppercase tracking-widest">
            <BarChart2 size={10} /> Signal Confidence
          </p>
          <ConfidenceBar score={Math.round(dataConfidence)} label="Data confidence" />
          <ConfidenceBar score={Math.round(viralityRisk)} label="Virality risk" />
        </div>
        {insights.top_topics?.length > 0 && (
          <div className="space-y-2">
            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest">Trending Topics</p>
            <div className="flex flex-wrap gap-1.5">
              {insights.top_topics.map((t) => (
                <span key={t} className="text-[11px] bg-gray-800/80 hover:bg-gray-700/80 transition-colors text-gray-300 px-2 py-0.5 rounded-full border border-white/[0.06] cursor-default">
                  {t}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
