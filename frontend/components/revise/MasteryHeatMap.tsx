"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils/cn";
import { useReviseSummary } from "@/lib/hooks/useRevise";
import { CONFIDENCE_CONFIG } from "@/lib/types/revise";

interface MasteryHeatMapProps {
  lectureId: string;
  className?: string;
}

export function MasteryHeatMap({ lectureId, className }: MasteryHeatMapProps) {
  const { data: summary, isLoading } = useReviseSummary(lectureId);

  if (isLoading) {
    return (
      <div className={cn("h-24 rounded-xl bg-white/5 animate-shimmer", className)} />
    );
  }

  if (!summary) return null;

  const total =
    summary.mastered_count +
    summary.shaky_count +
    summary.confused_count +
    summary.not_started_count || 1;

  const bars: { key: string; count: number; pct: number }[] = [
    { key: "mastered",    count: summary.mastered_count,    pct: summary.mastered_count    / total },
    { key: "shaky",       count: summary.shaky_count,       pct: summary.shaky_count       / total },
    { key: "confused",    count: summary.confused_count,    pct: summary.confused_count    / total },
    { key: "not_started", count: summary.not_started_count, pct: summary.not_started_count / total },
  ];

  const progressPct = Math.round(summary.overall_progress * 100);

  return (
    <div className={cn("glass-card p-4 space-y-3", className)}>
      {/* Progress bar */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>Overall progress</span>
        <span className="font-semibold text-foreground">{progressPct}%</span>
      </div>
      <div className="flex h-2 w-full overflow-hidden rounded-full bg-white/10">
        {bars.map(({ key, pct }) => (
          <motion.div
            key={key}
            initial={{ width: 0 }}
            animate={{ width: `${pct * 100}%` }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className={cn(
              "h-full",
              key === "mastered"    && "bg-emerald-500",
              key === "shaky"       && "bg-amber-500",
              key === "confused"    && "bg-red-500",
              key === "not_started" && "bg-zinc-600",
            )}
          />
        ))}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-x-4 gap-y-1">
        {bars.map(({ key, count }) => {
          const cfg = CONFIDENCE_CONFIG[key as keyof typeof CONFIDENCE_CONFIG];
          return (
            <div key={key} className="flex items-center gap-1.5 text-[11px]">
              <span className={cn("font-semibold", cfg.color)}>{cfg.emoji}</span>
              <span className="text-muted-foreground">{cfg.label}</span>
              <span className="font-medium text-foreground">{count}</span>
            </div>
          );
        })}
      </div>

      <p className="text-[10px] text-muted-foreground">
        {summary.flashcard_count} flashcards · {summary.quiz_count} quiz questions
      </p>
    </div>
  );
}
