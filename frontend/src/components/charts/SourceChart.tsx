"use client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LabelList } from "recharts";
import type { SourceStat } from "@/types";

const SOURCE_COLORS: Record<string, string> = {
  reddit: "#f97316",
  twitter: "#38bdf8",
  youtube: "#ef4444",
  instagram: "#ec4899",
  news: "#facc15",
};

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-3 text-xs shadow-xl">
      <p className="font-semibold text-white capitalize mb-1">{d.source}</p>
      <p className="text-gray-300">{d.count.toLocaleString()} posts</p>
      <p className="text-gray-400">{d.percentage ?? 0}% of total</p>
      {d.avg_trend_score > 0 && (
        <p className="text-gray-400">Avg score <span className="text-white">{d.avg_trend_score}</span></p>
      )}
    </div>
  );
}

export default function SourceChart({ data }: { data: SourceStat[] }) {
  // Only show platforms that actually have posts, sorted by count desc
  const sorted = [...data]
    .filter((d) => d.count > 0)
    .sort((a, b) => b.count - a.count);

  return (
    <div className="card h-72">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">Posts by Source</h3>
      <ResponsiveContainer width="100%" height="85%">
        <BarChart data={sorted} barSize={32}>
          <XAxis
            dataKey="source"
            tick={{ fill: "#9ca3af", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => v.charAt(0).toUpperCase() + v.slice(1)}
          />
          <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
          <Bar dataKey="count" radius={[6, 6, 0, 0]} isAnimationActive={true} animationDuration={700}>
            {sorted.map((entry) => (
              <Cell key={entry.source} fill={SOURCE_COLORS[entry.source] ?? "#4f6ef7"} />
            ))}
            <LabelList
              dataKey="percentage"
              position="top"
              formatter={(v: number) => v > 0 ? `${v}%` : ""}
              style={{ fill: "#9ca3af", fontSize: 10 }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
