"use client";

import { motion } from "framer-motion";
import { Calendar, Clock, Flame, CheckCircle } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { useRevisionPlan } from "@/lib/hooks/useRevise";
import { Badge } from "@/components/ui/badge";
import { CONFIDENCE_CONFIG } from "@/lib/types/revise";
import type { Confidence, RevisionEntry } from "@/lib/types/revise";

interface RevisionPlanCardProps {
  lectureId: string;
  className?: string;
}

function DueLabel({ days }: { days: number }) {
  if (days === 0)
    return <span className="text-red-400 font-medium text-[11px]">Due today</span>;
  if (days === 1)
    return <span className="text-amber-400 font-medium text-[11px]">Due tomorrow</span>;
  return <span className="text-muted-foreground text-[11px]">In {days} days</span>;
}

function PriorityIcon({ priority }: { priority: number }) {
  if (priority === 1) return <Flame className="h-3.5 w-3.5 text-red-400" />;
  if (priority === 2) return <Clock className="h-3.5 w-3.5 text-amber-400" />;
  return <CheckCircle className="h-3.5 w-3.5 text-zinc-500" />;
}

function EntryRow({ entry, index }: { entry: RevisionEntry; index: number }) {
  const confCfg = CONFIDENCE_CONFIG[entry.confidence as Confidence];

  return (
    <motion.div
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.04 }}
      className="flex items-center gap-3 py-2.5 border-b border-white/5 last:border-0"
    >
      <PriorityIcon priority={entry.priority} />

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{entry.concept_name}</p>
        <p className="text-[11px] text-muted-foreground truncate">{entry.reason}</p>
      </div>

      <div className="flex flex-col items-end gap-1 shrink-0">
        <DueLabel days={entry.due_in_days} />
        <span className={cn("text-[10px] font-medium", confCfg.color)}>
          {confCfg.emoji} {confCfg.label}
        </span>
      </div>
    </motion.div>
  );
}

export function RevisionPlanCard({ lectureId, className }: RevisionPlanCardProps) {
  const { data: plan, isLoading } = useRevisionPlan(lectureId);

  if (isLoading) {
    return (
      <div className={cn("space-y-2", className)}>
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-12 rounded-xl bg-white/5 animate-shimmer" />
        ))}
      </div>
    );
  }

  if (!plan?.entries.length) {
    return (
      <div className={cn("glass-card p-8 text-center", className)}>
        <Calendar className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
        <p className="text-muted-foreground text-sm">
          Your revision plan will appear here once you start studying flashcards.
        </p>
      </div>
    );
  }

  const dueToday = plan.entries.filter((e) => e.due_in_days === 0);
  const later    = plan.entries.filter((e) => e.due_in_days > 0);

  return (
    <div className={cn("space-y-4", className)}>
      {/* Stats row */}
      <div className="flex gap-3">
        <div className="glass-card flex-1 rounded-xl p-3 text-center">
          <p className="text-xl font-bold text-red-400">{plan.due_today}</p>
          <p className="text-[11px] text-muted-foreground">Due today</p>
        </div>
        <div className="glass-card flex-1 rounded-xl p-3 text-center">
          <p className="text-xl font-bold text-amber-400">{plan.due_this_week}</p>
          <p className="text-[11px] text-muted-foreground">This week</p>
        </div>
        <div className="glass-card flex-1 rounded-xl p-3 text-center">
          <p className="text-xl font-bold text-foreground">{plan.entries.length}</p>
          <p className="text-[11px] text-muted-foreground">Total</p>
        </div>
      </div>

      {/* Due today */}
      {dueToday.length > 0 && (
        <div className="glass-card rounded-xl p-4">
          <p className="text-xs font-semibold text-red-400 mb-3 flex items-center gap-1.5">
            <Flame className="h-3.5 w-3.5" />
            Due Today
          </p>
          {dueToday.map((entry, i) => (
            <EntryRow key={entry.concept_id ?? entry.concept_name} entry={entry} index={i} />
          ))}
        </div>
      )}

      {/* Upcoming */}
      {later.length > 0 && (
        <div className="glass-card rounded-xl p-4">
          <p className="text-xs font-semibold text-muted-foreground mb-3 flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5" />
            Upcoming
          </p>
          {later.slice(0, 8).map((entry, i) => (
            <EntryRow key={entry.concept_id ?? entry.concept_name} entry={entry} index={i} />
          ))}
          {later.length > 8 && (
            <p className="text-[11px] text-muted-foreground text-center mt-2">
              + {later.length - 8} more
            </p>
          )}
        </div>
      )}
    </div>
  );
}
