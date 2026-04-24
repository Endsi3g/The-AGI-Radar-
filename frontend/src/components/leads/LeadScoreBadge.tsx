import { cn } from "@/lib/utils";

interface Props {
  score: number | null;
  showLabel?: boolean;
  size?: "sm" | "md";
}

function scoreColor(score: number | null): string {
  if (score === null) return "bg-gray-100 text-gray-400";
  if (score >= 70) return "bg-emerald-100 text-emerald-700";
  if (score >= 40) return "bg-amber-100 text-amber-700";
  return "bg-red-100 text-red-600";
}

function scoreRing(score: number | null): string {
  if (score === null) return "bg-gray-200";
  if (score >= 70) return "bg-emerald-500";
  if (score >= 40) return "bg-amber-400";
  return "bg-red-500";
}

export function LeadScoreBadge({ score, showLabel = false, size = "md" }: Props) {
  return (
    <div className={cn("flex items-center gap-1.5 rounded-full px-2 py-0.5 font-semibold", scoreColor(score), size === "sm" ? "text-xs" : "text-sm")}>
      <span className={cn("rounded-full shrink-0", scoreRing(score), size === "sm" ? "w-1.5 h-1.5" : "w-2 h-2")} />
      {score !== null ? score : "—"}
      {showLabel && <span className="font-normal opacity-70">/100</span>}
    </div>
  );
}
