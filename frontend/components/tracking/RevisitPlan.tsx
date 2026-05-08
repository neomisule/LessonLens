"use client";

import { motion } from "framer-motion";
import { Calendar, BookOpen } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface RevisitItem {
  concept_name: string;
  lecture_title: string;
  due_in_label: string;
  due_urgency: "today" | "soon" | "later";
}

interface RevisitPlanProps { items: RevisitItem[]; }

const URGENCY_CONFIG = {
  today: { variant: "destructive" as const, label: "Today" },
  soon: { variant: "default" as const, label: "Soon" },
  later: { variant: "outline" as const, label: "Later" },
};

export function RevisitPlan({ items }: RevisitPlanProps) {
  if (items.length === 0) return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-lens-glass-border py-8 text-center">
      <Calendar className="h-8 w-8 text-muted-foreground/40" />
      <p className="text-sm text-muted-foreground">No items scheduled for review.</p>
      <p className="text-xs text-muted-foreground/60">Complete flashcard sessions to build your plan.</p>
    </div>
  );

  return (
    <div className="flex flex-col gap-2">
      {items.map((item, i) => {
        const config = URGENCY_CONFIG[item.due_urgency];
        return (
          <motion.div key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
            className="flex items-center gap-3 rounded-lg border border-lens-glass-border bg-white/3 p-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-lens-purple/10">
              <BookOpen className="h-3.5 w-3.5 text-lens-purple-light" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-foreground truncate">{item.concept_name}</p>
              <p className="text-[10px] text-muted-foreground truncate">{item.lecture_title}</p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-[10px] text-muted-foreground">{item.due_in_label}</span>
              <Badge variant={config.variant} className="text-[10px] py-0">{config.label}</Badge>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
