"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { contentApi } from "@/lib/api/content";
import { TimestampButton } from "@/components/lectures/TimestampButton";
import { cn } from "@/lib/utils/cn";
import type { SummaryLevel } from "@/lib/types/content";

const LEVELS: { value: SummaryLevel; label: string; description: string }[] = [
  { value: "brief", label: "Brief", description: "Key points only" },
  { value: "standard", label: "Standard", description: "Balanced overview" },
  { value: "detailed", label: "Detailed", description: "Full coverage" },
];

interface SummarySelectorProps {
  lectureId: string;
}

export function SummarySelector({ lectureId }: SummarySelectorProps) {
  const [level, setLevel] = useState<SummaryLevel>("standard");

  const { data: summary, isLoading } = useQuery({
    queryKey: ["summary", lectureId, level],
    queryFn: () => contentApi.getSummary(lectureId, level),
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2">
        {LEVELS.map((l) => (
          <button
            key={l.value}
            onClick={() => setLevel(l.value)}
            className={cn(
              "flex flex-col rounded-lg border px-3 py-2 text-left transition-all",
              level === l.value
                ? "border-lens-purple/40 bg-lens-purple/15 text-lens-purple-light"
                : "border-lens-glass-border bg-white/3 text-muted-foreground hover:bg-white/5"
            )}
          >
            <span className="text-xs font-medium">{l.label}</span>
            <span className="text-[10px] opacity-70">{l.description}</span>
          </button>
        ))}
      </div>

      {isLoading && (
        <div className="flex flex-col gap-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-4 rounded bg-white/5 animate-shimmer" style={{ width: `${70 + (i % 3) * 10}%` }} />
          ))}
        </div>
      )}

      {summary && (
        <motion.div
          key={level}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col gap-5"
        >
          {summary.sections.map((section, i) => (
            <div key={i} className="flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-semibold text-foreground">{section.heading}</h4>
                {section.timestamp_start != null && (
                  <TimestampButton seconds={section.timestamp_start} lectureId={lectureId} />
                )}
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">{section.content}</p>
            </div>
          ))}
        </motion.div>
      )}
    </div>
  );
}
