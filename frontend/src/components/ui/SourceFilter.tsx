import clsx from "clsx";

const SOURCES = ["all", "reddit", "twitter", "instagram", "youtube", "news"] as const;
type Source = (typeof SOURCES)[number];

interface Props {
  active: Source;
  onChange: (s: Source) => void;
}

export default function SourceFilter({ active, onChange }: Props) {
  return (
    <div className="flex gap-2 flex-wrap">
      {SOURCES.map((s) => (
        <button
          key={s}
          onClick={() => onChange(s)}
          className={clsx(
            "px-4 py-1.5 rounded-full text-sm font-medium transition-all capitalize",
            active === s
              ? "bg-brand-500 text-white"
              : "bg-gray-800 text-gray-400 hover:bg-gray-700"
          )}
        >
          {s}
        </button>
      ))}
    </div>
  );
}
