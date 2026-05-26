import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react";
import clsx from "clsx";

interface Props {
  label: string;
  value: string | number;
  icon: LucideIcon;
  trend?: "up" | "down" | "neutral";
  color?: string;
  sub?: string;
}

export default function StatCard({ label, value, icon: Icon, trend, color = "text-brand-500", sub }: Props) {
  return (
    <div className="card-glass flex items-center gap-4 animate-fade-in">
      <div className={clsx(
        "p-3 rounded-xl shrink-0",
        "bg-gray-800/60 border border-white/[0.05]",
        color
      )}>
        <Icon size={18} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[10px] text-gray-500 uppercase tracking-widest font-medium">{label}</p>
        <div className="flex items-end gap-1.5 mt-0.5">
          <p className="text-2xl font-bold text-white leading-none tabular-nums">{value}</p>
          {trend && trend !== "neutral" && (
            <span className={clsx("mb-0.5", trend === "up" ? "text-emerald-400" : "text-red-400")}>
              {trend === "up" ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
            </span>
          )}
        </div>
        {sub && <p className="text-[10px] text-gray-600 mt-0.5 truncate">{sub}</p>}
      </div>
    </div>
  );
}
