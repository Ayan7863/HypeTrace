"use client";
import {
  ComposedChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, ReferenceLine,
} from "recharts";
import type { TrendHistoryPoint } from "@/types";

const PLATFORM_COLORS: Record<string, string> = {
  reddit: "#f97316", twitter: "#38bdf8", youtube: "#ef4444",
  instagram: "#ec4899", news: "#facc15",
};

const PHASE_COLORS: Record<string, string> = {
  Viral: "#f59e0b", Emerging: "#10b981", Declining: "#ef4444", Stable: "#6b7280",
};

function fmt(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d || d.score == null) return null;
  const platColor = PLATFORM_COLORS[d.platform] ?? "#4f6ef7";
  const phaseColor = PHASE_COLORS[d.phase] ?? "#6b7280";
  const ts = d.rawTimestamp
    ? new Date(d.rawTimestamp).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
    : null;
  return (
    <div className="bg-gray-900/95 border border-gray-700/80 rounded-xl p-3 text-xs shadow-2xl max-w-[220px] backdrop-blur-md">
      {d.title && <p className="text-white font-semibold mb-2 leading-snug">{d.title}</p>}
      <div className="flex flex-wrap gap-1 mb-2">
        {d.platform && (
          <span className="px-1.5 py-0.5 rounded-full text-[10px] font-medium capitalize"
            style={{ background: `${platColor}22`, color: platColor }}>{d.platform}</span>
        )}
        {d.phase && (
          <span className="px-1.5 py-0.5 rounded-full text-[10px] font-medium"
            style={{ background: `${phaseColor}22`, color: phaseColor }}>{d.phase}</span>
        )}
        {d.isSpike && (
          <span className="px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-yellow-500/20 text-yellow-400">Spike</span>
        )}
      </div>
      <div className="space-y-0.5 text-gray-400">
        <div className="flex justify-between gap-4">
          <span>Score</span><span className="text-white font-bold">{d.score?.toFixed(1)}</span>
        </div>
        {d.virality != null && (
          <div className="flex justify-between gap-4">
            <span>Virality</span><span className="text-purple-400 font-medium">{d.virality}%</span>
          </div>
        )}
        {d.engagement > 0 && (
          <div className="flex justify-between gap-4">
            <span>Engagement</span><span className="text-white">{fmt(d.engagement)}</span>
          </div>
        )}
        {ts && <p className="text-gray-600 mt-1">{ts}</p>}
      </div>
    </div>
  );
}

// Custom dot renderer — spikes get a yellow ring, others get platform color
function CustomDot(props: any) {
  const { cx, cy, payload } = props;
  if (cx == null || cy == null) return null;
  if (payload.isSpike) {
    return (
      <g key={`spike-${payload.idx}`}>
        <circle cx={cx} cy={cy} r={6} fill="#facc15" stroke="#fef08a" strokeWidth={2} />
        <circle cx={cx} cy={cy} r={10} fill="none" stroke="#facc15" strokeWidth={1} opacity={0.4} />
      </g>
    );
  }
  if (payload.title) {
    // Only draw dots at "current" points (end of each post's curve)
    const color = PLATFORM_COLORS[payload.platform] ?? "#4f6ef7";
    return <circle key={`dot-${payload.idx}`} cx={cx} cy={cy} r={3} fill={color} />;
  }
  return null;
}

interface Props { data: TrendHistoryPoint[] }

export default function TrendScoreChart({ data }: Props) {
  const chartData: any[] = [];
  let globalIdx = 0;

  data.forEach((post) => {
    const curve = post.decay_curve?.length ? post.decay_curve : [post.score];
    curve.forEach((val, ci) => {
      const isLast = ci === curve.length - 1;
      chartData.push({
        idx: globalIdx++,
        score: val,
        title: isLast ? post.title : undefined,
        platform: isLast ? post.platform : undefined,
        phase: isLast ? post.trend_phase : undefined,
        isSpike: isLast && post.is_spike,
        virality: isLast ? post.virality_score : undefined,
        engagement: isLast ? post.engagement : 0,
        rawTimestamp: isLast ? post.timestamp : undefined,
      });
    });
  });

  const spikes = data.filter((d) => d.is_spike);
  const scores = chartData.map((d) => d.score).filter((s) => s != null);
  const avgScore = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
  const maxScore = scores.length ? Math.max(...scores) : 10;

  return (
    <div className="card-glass h-72">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-white">Virality Momentum</h3>
          <p className="text-xs text-gray-500 mt-0.5">Decay curves · {data.length} trends</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap justify-end">
          {spikes.length > 0 && (
            <span className="text-xs bg-yellow-500/15 text-yellow-400 border border-yellow-500/20 px-2 py-0.5 rounded-full">
              ⚡ {spikes.length} spike{spikes.length > 1 ? "s" : ""}
            </span>
          )}
          <span className="text-xs text-gray-500">
            avg <span className="text-white font-medium">{avgScore.toFixed(1)}</span>
            {" · "}peak <span className="text-orange-400 font-medium">{maxScore.toFixed(1)}</span>
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height="82%">
        <ComposedChart data={chartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#4f6ef7" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#4f6ef7" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="2 4" stroke="#1f2937" vertical={false} />
          <XAxis dataKey="idx" hide />
          <YAxis
            domain={[0, 10]}
            ticks={[0, 2, 4, 6, 8, 10]}
            tick={{ fill: "#4b5563", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: "#374151", strokeWidth: 1, strokeDasharray: "3 3" }} />
          <ReferenceLine y={avgScore} stroke="#374151" strokeDasharray="4 4" />
          <Area
            type="monotone"
            dataKey="score"
            stroke="#4f6ef7"
            strokeWidth={2}
            fill="url(#areaGrad)"
            dot={<CustomDot />}
            activeDot={{ r: 4, fill: "#818cf8", stroke: "#4f6ef7", strokeWidth: 2 }}
            isAnimationActive
            animationDuration={900}
            animationEasing="ease-out"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
