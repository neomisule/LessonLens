"use client";

import { cn } from "@/lib/utils/cn";
import type { Confidence } from "@/lib/types/revise";
import { CONFIDENCE_CONFIG } from "@/lib/types/revise";

interface ConfidenceButtonsProps {
  onSelect: (confidence: Confidence) => void;
  loading?: boolean;
  className?: string;
}

const BUTTONS: { confidence: Confidence; shortcut: string }[] = [
  { confidence: "confused",    shortcut: "1" },
  { confidence: "shaky",       shortcut: "2" },
  { confidence: "mastered",    shortcut: "3" },
];

export function ConfidenceButtons({
  onSelect,
  loading,
  className,
}: ConfidenceButtonsProps) {
  return (
    <div className={cn("flex gap-2 justify-center", className)}>
      {BUTTONS.map(({ confidence, shortcut }) => {
        const cfg = CONFIDENCE_CONFIG[confidence];
        return (
          <button
            key={confidence}
            onClick={() => onSelect(confidence)}
            disabled={loading}
            className={cn(
              "flex flex-col items-center gap-1 rounded-xl border px-4 py-2.5",
              "text-xs font-medium transition-all min-w-[80px]",
              "hover:scale-105 active:scale-95",
              cfg.bg,
              cfg.color,
              "border-current/20",
              loading && "opacity-40 pointer-events-none"
            )}
          >
            <span className="text-base">{cfg.emoji}</span>
            <span>{cfg.label}</span>
            <kbd className="mt-0.5 opacity-40 text-[9px] font-mono">{shortcut}</kbd>
          </button>
        );
      })}
    </div>
  );
}
