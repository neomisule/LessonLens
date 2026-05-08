"use client";

import { motion } from "framer-motion";
import { GraduationCap } from "lucide-react";
import { cn } from "@/lib/utils/cn";

interface ConceptExamBadgeProps {
  likelihood: number;   // 0–1
  className?: string;
  showLabel?: boolean;
}

function getExamTier(likelihood: number): {
  label: string;
  colorClass: string;
  bgClass: string;
} {
  if (likelihood >= 0.8) {
    return {
      label: "High Exam Chance",
      colorClass: "text-red-400",
      bgClass: "bg-red-500/15 border-red-500/30",
    };
  }
  if (likelihood >= 0.55) {
    return {
      label: "Likely on Exam",
      colorClass: "text-amber-400",
      bgClass: "bg-amber-500/15 border-amber-500/30",
    };
  }
  if (likelihood >= 0.3) {
    return {
      label: "Possible Exam",
      colorClass: "text-lens-teal-light",
      bgClass: "bg-lens-teal/15 border-lens-teal/30",
    };
  }
  return {
    label: "Supplemental",
    colorClass: "text-muted-foreground",
    bgClass: "bg-white/5 border-white/10",
  };
}

export function ConceptExamBadge({
  likelihood,
  className,
  showLabel = true,
}: ConceptExamBadgeProps) {
  const { label, colorClass, bgClass } = getExamTier(likelihood);
  const pct = Math.round(likelihood * 100);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-medium",
        bgClass,
        colorClass,
        className,
      )}
    >
      <GraduationCap className="h-3 w-3 shrink-0" />
      {showLabel ? label : `${pct}%`}
    </motion.div>
  );
}
