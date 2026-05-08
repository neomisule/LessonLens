"use client";

import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { contentApi } from "@/lib/api/content";
import { cn } from "@/lib/utils/cn";

interface MasteryTrackerProps { lectureId: string; compact?: boolean; }

const MASTERY_LEVELS = [
  { key: "mastered", label: "Mastered", color: "bg-green-500" },
  { key: "familiar", label: "Familiar", color: "bg-lens-teal" },
  { key: "learning", label: "Learning", color: "bg-lens-blue" },
  { key: "unseen", label: "Unseen", color: "bg-white/20" },
] as const;

export function MasteryTracker({ lectureId, compact = false }: MasteryTrackerProps) {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["mastery", lectureId],
    queryFn: () => contentApi.getMastery(lectureId),
  });

  if (isLoading) return (
    <div className="flex flex-col gap-2" aria-label="Loading mastery" aria-busy="true">
      <div className="h-2 w-full rounded-full skeleton" />
      {!compact && <div className="h-8 w-full rounded-lg skeleton" />}
    </div>
  );
  if (!stats) return null;

  return (
    <div className={cn("flex flex-col gap-3", compact && "gap-2")}>
      {!compact && (
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-foreground">Overall Mastery</span>
          <span className="text-sm font-bold gradient-text">{Math.round(stats.mastery_percentage)}%</span>
        </div>
      )}
      <div className="relative h-2 w-full overflow-hidden rounded-full bg-white/10">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${stats.mastery_percentage}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
          className="h-full rounded-full bg-lens-gradient"
        />
      </div>
      {!compact && (
        <div className="grid grid-cols-4 gap-2">
          {MASTERY_LEVELS.map(({ key, label, color }) => (
            <div key={key} className="flex flex-col gap-1">
              <div className="flex items-center gap-1.5">
                <div className={cn("h-2 w-2 rounded-full", color)} />
                <span className="text-[10px] text-muted-foreground">{label}</span>
              </div>
              <span className="text-xs font-medium text-foreground">
                {stats[`${key}_concepts` as keyof typeof stats] as number}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
