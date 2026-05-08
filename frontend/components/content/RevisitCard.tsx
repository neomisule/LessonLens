"use client";

import { motion } from "framer-motion";
import { RefreshCw, GraduationCap, Clock, Star } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { TimestampButton } from "@/components/lectures/TimestampButton";
import { cn } from "@/lib/utils/cn";
import type { RevisitRecommendation } from "@/lib/types/breakdown";

const IMPORTANCE_COLORS = {
  core:         "text-lens-purple-light border-lens-purple/30 bg-lens-purple/10",
  supporting:   "text-lens-teal-light border-lens-teal/30 bg-lens-teal/10",
  supplemental: "text-muted-foreground border-white/10 bg-white/5",
};

interface RevisitCardProps {
  recommendation: RevisitRecommendation;
  lectureId: string;
  index: number;
  onConceptClick?: (conceptId: string) => void;
}

export function RevisitCard({
  recommendation: rec,
  lectureId,
  index,
  onConceptClick,
}: RevisitCardProps) {
  const colorClass =
    IMPORTANCE_COLORS[rec.importance as keyof typeof IMPORTANCE_COLORS] ??
    IMPORTANCE_COLORS.supplemental;

  return (
    <motion.div
      initial={{ opacity: 0, x: 8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.07 }}
      className="glass-card flex items-start gap-3 p-4"
    >
      {/* Priority badge */}
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-amber-500/15 text-[11px] font-bold text-amber-400">
        {rec.priority}
      </div>

      <div className="flex-1 min-w-0 flex flex-col gap-2">
        {/* Header */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => onConceptClick?.(rec.concept_id)}
            className="text-sm font-semibold text-foreground hover:text-lens-teal-light transition-colors text-left"
          >
            {rec.concept_name}
          </button>
          <Badge
            variant="outline"
            className={cn("text-[9px] capitalize px-1.5 py-0", colorClass)}
          >
            {rec.importance}
          </Badge>
        </div>

        {/* Reason */}
        <p className="text-xs text-muted-foreground">{rec.reason}</p>

        {/* Stats row */}
        <div className="flex items-center gap-3 flex-wrap">
          {rec.timestamp_start != null && (
            <TimestampButton
              seconds={rec.timestamp_start}
              lectureId={lectureId}
              className="text-[10px]"
            />
          )}
          <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
            <GraduationCap className="h-3 w-3" />
            {Math.round(rec.exam_likelihood * 100)}% exam
          </span>
        </div>
      </div>

      {/* Revisit icon */}
      <RefreshCw className="h-4 w-4 shrink-0 text-amber-400/60 mt-0.5" />
    </motion.div>
  );
}
