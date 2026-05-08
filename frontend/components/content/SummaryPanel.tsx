"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Clock, ChevronDown, ChevronRight } from "lucide-react";
import { TimestampButton } from "@/components/lectures/TimestampButton";
import { cn } from "@/lib/utils/cn";
import type { Summary, SummaryLevel } from "@/lib/types/content";

const LEVEL_CONFIG: Record<SummaryLevel, { label: string; readTime: string; description: string }> = {
  brief: {
    label: "Brief",
    readTime: "90s read",
    description: "Essential points only",
  },
  standard: {
    label: "Standard",
    readTime: "5 min read",
    description: "Complete overview",
  },
  detailed: {
    label: "Detailed",
    readTime: "Full coverage",
    description: "Every concept & example",
  },
};

interface SectionItemProps {
  heading: string;
  content: string;
  keyPoints: string[];
  timestampStart: number | null;
  lectureId: string;
  index: number;
}

function SectionItem({
  heading,
  content,
  keyPoints,
  timestampStart,
  lectureId,
  index,
}: SectionItemProps) {
  const [open, setOpen] = useState(index === 0);

  return (
    <motion.div
      layout
      className="rounded-xl border border-lens-glass-border bg-white/3 overflow-hidden"
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
    >
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left"
      >
        {timestampStart != null ? (
          <TimestampButton
            seconds={timestampStart}
            lectureId={lectureId}
            className="text-[10px] shrink-0"
          />
        ) : (
          <span className="w-12 shrink-0" />
        )}
        <span className="flex-1 text-sm font-semibold text-foreground">{heading}</span>
        <ChevronDown
          className={cn(
            "h-4 w-4 shrink-0 text-muted-foreground transition-transform",
            open && "rotate-180",
          )}
        />
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="overflow-hidden"
          >
            <div className="flex flex-col gap-3 px-4 pb-4 border-t border-lens-glass-border pt-3">
              <p className="text-sm text-muted-foreground leading-relaxed">{content}</p>
              {keyPoints.length > 0 && (
                <ul className="flex flex-col gap-1.5 pl-1">
                  {keyPoints.map((point, i) => (
                    <li key={i} className="flex gap-2 text-xs text-muted-foreground">
                      <ChevronRight className="mt-0.5 h-3 w-3 shrink-0 text-lens-teal-light" />
                      {point}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

interface SummaryPanelProps {
  summaries: Summary[];
  lectureId: string;
}

export function SummaryPanel({ summaries, lectureId }: SummaryPanelProps) {
  const [activeLevel, setActiveLevel] = useState<SummaryLevel>(() => {
    // Default to first available level, prefer "standard"
    const hasStandard = summaries.some((s) => s.level === "standard");
    return hasStandard ? "standard" : (summaries[0]?.level ?? "standard");
  });

  const activeSummary = summaries.find((s) => s.level === activeLevel);
  const availableLevels = summaries.map((s) => s.level);

  if (summaries.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center rounded-xl border border-dashed border-lens-glass-border text-sm text-muted-foreground">
        Summaries not yet generated.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Level switcher */}
      <div className="flex gap-2">
        {(["brief", "standard", "detailed"] as SummaryLevel[])
          .filter((l) => availableLevels.includes(l))
          .map((level) => {
            const cfg = LEVEL_CONFIG[level];
            const isActive = activeLevel === level;
            return (
              <button
                key={level}
                onClick={() => setActiveLevel(level)}
                className={cn(
                  "flex flex-col gap-0.5 rounded-xl border px-4 py-2.5 text-left transition-all",
                  isActive
                    ? "border-lens-purple/50 bg-lens-purple/15 text-foreground"
                    : "border-lens-glass-border bg-white/3 text-muted-foreground hover:bg-white/5",
                )}
              >
                <span className="text-xs font-semibold">{cfg.label}</span>
                <span className="flex items-center gap-1 text-[10px] opacity-70">
                  <Clock className="h-3 w-3" />
                  {cfg.readTime}
                </span>
              </button>
            );
          })}
      </div>

      {/* Summary content */}
      <AnimatePresence mode="wait">
        {activeSummary && (
          <motion.div
            key={activeSummary.level}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.2 }}
            className="flex flex-col gap-4"
          >
            {/* Intro paragraph */}
            <div className="glass-card p-4">
              <h2 className="text-sm font-bold text-foreground mb-2">
                {activeSummary.title}
              </h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {activeSummary.content}
              </p>
            </div>

            {/* Sections */}
            {activeSummary.sections.length > 0 && (
              <div className="flex flex-col gap-2">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide px-1">
                  Sections
                </p>
                {activeSummary.sections.map((section, i) => (
                  <SectionItem
                    key={i}
                    heading={section.heading}
                    content={section.content}
                    keyPoints={section.key_points ?? []}
                    timestampStart={section.timestamp_start}
                    lectureId={lectureId}
                    index={i}
                  />
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
