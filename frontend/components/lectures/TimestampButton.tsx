"use client";

import { Clock } from "lucide-react";
import { formatTimestamp } from "@/lib/utils/youtube";
import { cn } from "@/lib/utils/cn";

interface TimestampButtonProps {
  seconds: number;
  lectureId: string;
  className?: string;
}

export function TimestampButton({ seconds, lectureId, className }: TimestampButtonProps) {
  const handleClick = () => {
    console.info(`[TimestampButton] seek ${lectureId} to ${seconds}s`);
  };

  return (
    <button
      onClick={handleClick}
      className={cn(
        "inline-flex items-center gap-1 rounded-md border border-lens-teal/20 bg-lens-teal/10",
        "px-1.5 py-0.5 text-xs text-lens-teal-light hover:bg-lens-teal/20 transition-colors",
        className
      )}
    >
      <Clock className="h-2.5 w-2.5" />
      {formatTimestamp(seconds)}
    </button>
  );
}
