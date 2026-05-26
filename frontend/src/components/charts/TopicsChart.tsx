"use client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LabelList } from "recharts";
import type { TopicSummary } from "@/types";

interface Props {
  data: TopicSummary[];
  onTopicClick?: (label: string) => void;
  activeTopic?: string | null;
}

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-gray-900/95 border border-gray-700 rounded-xl p-3 text-xs shadow-2xl max-w-[200px]">
      <p className="font-semibold text-white mb-1 leading-snug">{d.fullName}</p>
      <div className="space-y-0.5 text-gray-400">
        <p>{d.posts} posts <span className="text-gray-500">({d.pct}%)</span></p>
        <p>Avg score <span className="text-white font-medium">{d.score?.toFixed(1)}</span></p>
        {d.spike_count > 0 && <p className="text-yellow-400">⚡ {d.spike_count} spike{d.spike_count > 1 ? "s" : ""}</p>}
        {d.sources?.length > 0 && <p className="text-gray-500">{d.sources.join(", ")}</p>}
      </div>
    </div>
  );
}

export default function TopicsChart({ data, onTopicClick, activeTopic }: Props) {
  const sorted = [...data].sort((a, b) => b.avg_trend_score - a.avg_trend_score).slice(0, 8);
  const chartData = sorted.map((t) => ({
    name: t.topic_label.length > 20 ? t.topic_label.slice(0, 20) + "…" : t.topic_label,
    fullName: t.topic_label,
    score: t.avg_trend_score,
    posts: t.post_count,
    pct: t.percentage ?? 0,
    spike_count: t.spike_count ?? 0,
    sources: t.top_sources,
  }));

  return (
    <div className="card h-80">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-300">Topic Clusters</h3>
          <p className="text-xs text-gray-500 mt-0.5">Sorted by trend score · {data.length} clusters</p>
        </div>
        {onTopicClick && <span className="text-xs text-gray-600">Click to filter</span>}
      </div>
      <ResponsiveContainer width="100%" height="86%">
        <BarChart
          data={chartData}
          layout="vertical"
          barSize={13}
          onClick={(e) => {
            const label = e?.activePayload?.[0]?.payload?.fullName;
            if (label && onTopicClick) onTopicClick(label);
          }}
          style={{ cursor: onTopicClick ? "pointer" : "default" }}
          margin={{ right: 40 }}
        >
          <XAxis type="number" domain={[0, 10]} tick={{ fill: "#6b7280", fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis type="category" dataKey="name" width={130} tick={{ fill: "#d1d5db", fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
          <Bar dataKey="score" radius={[0, 6, 6, 0]} isAnimationActive animationDuration={700}>
            <LabelList
              dataKey="pct"
              position="right"
              formatter={(v: number) => v > 0 ? `${v}%` : ""}
              style={{ fill: "#6b7280", fontSize: 10 }}
            />
            {chartData.map((entry) => (
              <Cell
                key={entry.fullName}
                fill={
                  activeTopic === entry.fullName ? "#818cf8" :
                  entry.spike_count > 0 ? "#f59e0b" : "#4f6ef7"
                }
                opacity={activeTopic && activeTopic !== entry.fullName ? 0.5 : 1}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
