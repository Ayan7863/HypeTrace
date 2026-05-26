"use client";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import type { SentimentStats } from "@/types";

const SENTIMENT_CONFIG = [
  { key: "positive" as const, label: "Positive", color: "#10b981" },
  { key: "negative" as const, label: "Negative", color: "#ef4444" },
  { key: "neutral"  as const, label: "Neutral",  color: "#6b7280" },
];

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-3 text-xs shadow-xl">
      <p style={{ color: d.payload.color }} className="font-semibold mb-1">{d.name}</p>
      <p className="text-white">{d.value.toLocaleString()} posts</p>
      <p className="text-gray-400">{d.payload.pct}% of total</p>
    </div>
  );
}

// Renders the dominant label in the donut center using SVG viewBox coordinates
function CenterLabel({ cx, cy, dominant }: { cx: number; cy: number; dominant: { pct: number; name: string; color: string } }) {
  return (
    <g>
      <text x={cx} y={cy - 8} textAnchor="middle" dominantBaseline="middle"
        fill={dominant.color} fontSize={20} fontWeight={700}>
        {dominant.pct}%
      </text>
      <text x={cx} y={cy + 12} textAnchor="middle" dominantBaseline="middle"
        fill="#9ca3af" fontSize={11}>
        {dominant.name}
      </text>
    </g>
  );
}

export default function SentimentChart({ data }: { data: SentimentStats }) {
  const total = data.positive + data.negative + data.neutral;
  const chartData = SENTIMENT_CONFIG
    .map((c) => ({
      name: c.label,
      value: data[c.key],
      color: c.color,
      pct: total > 0 ? Math.round(data[c.key] / total * 100) : 0,
    }))
    .filter((d) => d.value > 0);

  if (chartData.length === 0) {
    return (
      <div className="card h-72 flex flex-col">
        <h3 className="text-sm font-semibold text-gray-300 mb-2">Sentiment Distribution</h3>
        <div className="flex-1 flex items-center justify-center text-gray-600 text-sm">No data yet</div>
      </div>
    );
  }

  const dominant = chartData.reduce((a, b) => a.value > b.value ? a : b);

  return (
    <div className="card h-72">
      <h3 className="text-sm font-semibold text-gray-300 mb-2">Sentiment Distribution</h3>
      <ResponsiveContainer width="100%" height="85%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="46%"
            innerRadius={50}
            outerRadius={76}
            paddingAngle={3}
            dataKey="value"
            isAnimationActive
            animationBegin={0}
            animationDuration={700}
          >
            {chartData.map((entry) => (
              <Cell key={entry.name} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            iconType="circle"
            iconSize={8}
            formatter={(v, entry: any) => (
              <span className="text-xs text-gray-400">
                {v} <span className="text-white font-medium">{entry.payload.pct}%</span>
              </span>
            )}
          />
          {/* Center label rendered via customized label on a zero-size Pie */}
          <Pie
            data={[{ value: 1 }]}
            cx="50%"
            cy="46%"
            innerRadius={0}
            outerRadius={0}
            dataKey="value"
            isAnimationActive={false}
            label={(props) => <CenterLabel cx={props.cx} cy={props.cy} dominant={dominant} />}
            labelLine={false}
          >
            <Cell fill="transparent" />
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
