import { clsx } from "clsx";

interface ScoreBarProps {
  score: number;
  max?: number;
  label?: string;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

export function ScoreBar({ score, max = 100, label, size = "md", showLabel = true }: ScoreBarProps) {
  const pct = Math.min((score / max) * 100, 100);
  const color = pct >= 75 ? "bg-green-500" : pct >= 50 ? "bg-yellow-500" : pct >= 25 ? "bg-orange-500" : "bg-red-500";
  const heights = { sm: "h-1.5", md: "h-2", lg: "h-3" };

  return (
    <div className="w-full">
      {(label || showLabel) && (
        <div className="flex justify-between items-center mb-1">
          {label && <span className="text-xs text-slate-500">{label}</span>}
          {showLabel && <span className="text-xs font-semibold text-slate-700">{score.toFixed(1)}</span>}
        </div>
      )}
      <div className={clsx("w-full bg-slate-100 rounded-full overflow-hidden", heights[size])}>
        <div className={clsx("rounded-full transition-all duration-500", color, heights[size])} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function ScoreBadge({ score }: { score: number }) {
  const color = score >= 75 ? "bg-green-100 text-green-800" : score >= 50 ? "bg-yellow-100 text-yellow-800" : score >= 25 ? "bg-orange-100 text-orange-800" : "bg-red-100 text-red-800";
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${color}`}>
      {score.toFixed(1)}
    </span>
  );
}
