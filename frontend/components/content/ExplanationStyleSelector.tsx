"use client";

import { motion } from "framer-motion";
import {
  Feather, GitCompare, Lightbulb, BookOpen, LayoutTemplate, Baby,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import type { ExplanationStyle } from "@/lib/types/breakdown";
import { EXPLANATION_STYLES } from "@/lib/types/breakdown";

const ICON_MAP: Record<string, React.ElementType> = {
  Feather, GitCompare, Lightbulb, BookOpen, LayoutTemplate, Baby,
};

interface ExplanationStyleSelectorProps {
  selected: ExplanationStyle | null;
  onSelect: (style: ExplanationStyle) => void;
  loading?: ExplanationStyle | null;  // which style is currently loading
  className?: string;
}

export function ExplanationStyleSelector({
  selected,
  onSelect,
  loading,
  className,
}: ExplanationStyleSelectorProps) {
  return (
    <div className={cn("grid grid-cols-3 gap-2", className)}>
      {EXPLANATION_STYLES.map((s, i) => {
        const Icon = ICON_MAP[s.icon] ?? Feather;
        const isSelected = selected === s.id;
        const isLoading  = loading === s.id;

        return (
          <motion.button
            key={s.id}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
            onClick={() => onSelect(s.id)}
            disabled={isLoading}
            className={cn(
              "relative flex flex-col items-start gap-1.5 rounded-xl border p-3 text-left transition-all",
              isSelected
                ? "border-lens-teal/50 bg-lens-teal/12 text-foreground"
                : "border-lens-glass-border bg-white/3 text-muted-foreground hover:bg-white/6 hover:text-foreground",
              isLoading && "opacity-60 cursor-wait",
            )}
          >
            {/* Loading shimmer */}
            {isLoading && (
              <motion.div
                className="absolute inset-0 rounded-xl bg-lens-teal/10"
                animate={{ opacity: [0.3, 0.7, 0.3] }}
                transition={{ duration: 1.2, repeat: Infinity }}
              />
            )}

            <div className={cn(
              "flex h-7 w-7 items-center justify-center rounded-lg transition-colors",
              isSelected ? "bg-lens-teal/25 text-lens-teal-light" : "bg-white/8 text-muted-foreground",
            )}>
              <Icon className="h-3.5 w-3.5" />
            </div>

            <div className="flex flex-col gap-0.5">
              <span className="text-xs font-semibold leading-tight">{s.label}</span>
              <span className="text-[10px] leading-tight opacity-65">{s.description}</span>
            </div>

            {isSelected && (
              <motion.div
                layoutId="style-pill"
                className="absolute top-2 right-2 h-1.5 w-1.5 rounded-full bg-lens-teal"
              />
            )}
          </motion.button>
        );
      })}
    </div>
  );
}
