"use client";

import { Clock } from "lucide-react";
import { formatTimestamp } from "@/lib/utils/youtube";
import { usePlayerStore } from "@/lib/store/playerStore";
import { cn } from "@/lib/utils/cn";

interface TimestampButtonProps {
  seconds: number;
  lectureId: string;
  className?: string;
}

/**
 * Clickable timestamp chip.
 * Clicking seeks the lecture's YouTube player to `seconds` via Zustand store.
 */
export function TimestampButton({ seconds, lectureId: _lectureId, className }: TimestampButtonProps) {
  const seekTo = usePlayerStore((s) => s.seekTo);

  return (
    <button
      onClick={() => seekTo(seconds)}
      title={`Jump to ${formatTimestamp(seconds)} in the lecture`}
      className={cn(
        "inline-flex items-center gap-1 rounded-md border border-lens-teal/20 bg-lens-teal/10",
        "px-1.5 py-0.5 text-xs text-lens-teal-light hover:bg-lens-teal/20 transition-colors cursor-pointer",
        className,
      )}
    >
      <Clock className="h-2.5 w-2.5" />
      {formatTimestamp(seconds)}
    </button>
  );
}
