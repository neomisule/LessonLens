"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { BookMarked } from "lucide-react";
import { TimestampButton } from "@/components/lectures/TimestampButton";
import { cn } from "@/lib/utils/cn";
import type { Chapter } from "@/lib/types/content";

function formatTimestamp(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

interface ChapterTimelineProps {
  chapters: Chapter[];
  lectureId: string;
  totalDuration?: number;   // seconds, used to compute width proportions
  activeChapterIndex?: number;
  className?: string;
}

export function ChapterTimeline({
  chapters,
  lectureId,
  totalDuration,
  activeChapterIndex,
  className,
}: ChapterTimelineProps) {
  const [hovered, setHovered] = useState<number | null>(null);

  if (chapters.length === 0) return null;

  const duration = totalDuration ||
    (chapters[chapters.length - 1]?.timestamp_end ??
      chapters[chapters.length - 1]?.timestamp_start + 1) ||
    1;

  return (
    <div className={cn("flex flex-col gap-4", className)}>
      {/* ── Bar timeline ──────────────────────────────────────────────── */}
      <div className="relative h-8 w-full overflow-hidden rounded-lg bg-white/5">
        {chapters.map((ch, i) => {
          const startPct = (ch.timestamp_start / duration) * 100;
          const endPct = ch.timestamp_end != null
            ? (ch.timestamp_end / duration) * 100
            : i + 1 < chapters.length
            ? (chapters[i + 1].timestamp_start / duration) * 100
            : 100;
          const widthPct = Math.max(endPct - startPct, 0.5);

          const isActive = activeChapterIndex === i;
          const isHovered = hovered === i;

          return (
            <button
              key={ch.id}
              onMouseEnter={() => setHovered(i)}
              onMouseLeave={() => setHovered(null)}
              className="absolute top-0 h-full transition-all"
              style={{ left: `${startPct}%`, width: `${widthPct}%` }}
              title={ch.title}
            >
              <div
                className={cn(
                  "h-full border-r border-lens-bg transition-all",
                  isActive
                    ? "bg-lens-purple/50"
                    : isHovered
                    ? "bg-lens-purple/30"
                    : i % 2 === 0
                    ? "bg-lens-teal/20"
                    : "bg-lens-purple/15",
                )}
              />
            </button>
          );
        })}

        {/* Chapter index labels */}
        {chapters.map((ch, i) => {
          const startPct = (ch.timestamp_start / duration) * 100;
          return (
            <span
              key={ch.id}
              className="absolute top-1/2 -translate-y-1/2 text-[9px] font-bold text-white/50 pointer-events-none select-none"
              style={{ left: `calc(${startPct}% + 4px)` }}
            >
              {i + 1}
            </span>
          );
        })}
      </div>

      {/* ── Chapter list ──────────────────────────────────────────────── */}
      <div className="flex flex-col gap-2">
        {chapters.map((ch, i) => {
          const isActive = activeChapterIndex === i;
          return (
            <motion.div
              key={ch.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.04 }}
              className={cn(
                "flex items-start gap-3 rounded-xl border px-3 py-2.5 transition-colors",
                isActive
                  ? "border-lens-purple/40 bg-lens-purple/10"
                  : "border-lens-glass-border bg-white/3 hover:bg-white/5",
              )}
            >
              {/* Chapter number */}
              <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-lens-purple/20 text-[10px] font-bold text-lens-purple-light">
                {i + 1}
              </div>

              {/* Title + summary */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-semibold text-foreground">{ch.title}</span>
                  <TimestampButton
                    seconds={ch.timestamp_start}
                    lectureId={lectureId}
                    className="text-[10px]"
                  />
                </div>
                {ch.summary && (
                  <p className="mt-0.5 text-[11px] text-muted-foreground leading-relaxed line-clamp-2">
                    {ch.summary}
                  </p>
                )}
                {ch.concept_names && ch.concept_names.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {ch.concept_names.slice(0, 5).map((name) => (
                      <span
                        key={name}
                        className="inline-flex items-center gap-1 rounded-full border border-lens-glass-border bg-white/5 px-1.5 py-0.5 text-[9px] text-muted-foreground"
                      >
                        <BookMarked className="h-2 w-2" />
                        {name}
                      </span>
                    ))}
                    {ch.concept_names.length > 5 && (
                      <span className="text-[9px] text-muted-foreground">
                        +{ch.concept_names.length - 5} more
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Duration */}
              {ch.timestamp_end != null && (
                <span className="shrink-0 text-[10px] text-muted-foreground">
                  {formatTimestamp(ch.timestamp_start)}
                  {" — "}
                  {formatTimestamp(ch.timestamp_end)}
                </span>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
