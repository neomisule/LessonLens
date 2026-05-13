"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FileText, List, Clock3, GraduationCap } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { contentApi } from "@/lib/api/content";
import { SummaryPanel } from "@/components/content/SummaryPanel";
import { LectureOutline } from "@/components/content/LectureOutline";
import { ChapterTimeline } from "@/components/content/ChapterTimeline";
import { KeyConceptCard } from "@/components/content/KeyConceptCard";
import { cn } from "@/lib/utils/cn";
import type { Concept } from "@/lib/types/content";

type LearnTab = "summary" | "outline" | "timeline" | "concepts";

const TABS: { id: LearnTab; label: string; icon: React.ElementType }[] = [
  { id: "summary", label: "Summary", icon: FileText },
  { id: "outline", label: "Outline", icon: List },
  { id: "timeline", label: "Chapters", icon: Clock3 },
  { id: "concepts", label: "Concepts", icon: GraduationCap },
];

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex h-48 items-center justify-center rounded-xl border border-dashed border-lens-glass-border text-sm text-muted-foreground">
      {message}
    </div>
  );
}

function ConceptsList({
  concepts,
  lectureId,
}: {
  concepts: Concept[];
  lectureId: string;
}) {
  // Show core concepts first, then sort by exam_likelihood
  const sorted = [...concepts].sort(
    (a, b) => b.exam_likelihood - a.exam_likelihood,
  );

  if (sorted.length === 0) {
    return <EmptyState message="No concepts extracted yet." />;
  }

  return (
    <div className="flex flex-col gap-2">
      {sorted.map((concept, i) => (
        <motion.div
          key={concept.id}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.03 }}
        >
          <KeyConceptCard concept={concept} lectureId={lectureId} />
        </motion.div>
      ))}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex flex-col gap-3" aria-label="Loading content" aria-busy="true">
      <div className="h-32 rounded-xl skeleton" />
      <div className="h-24 rounded-xl skeleton" />
      <div className="h-24 rounded-xl skeleton" />
    </div>
  );
}

interface LearnModeProps {
  lectureId: string;
}

export function LearnMode({ lectureId }: LearnModeProps) {
  const [activeTab, setActiveTab] = useState<LearnTab | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["learn-mode", lectureId],
    queryFn: () => contentApi.getLearnMode(lectureId),
    staleTime: 60 * 1000, // 1 min — fresh enough that new content shows quickly
    retry: 2,
  });

  const summaries = data?.summaries ?? [];
  const chapters = data?.chapters ?? [];
  const concepts = data?.concepts ?? [];

  // Auto-select first tab with content once data loads.
  // Default to "summary" only if summaries exist; otherwise fall back to
  // "timeline" (chapters always have a heuristic fallback) then "concepts".
  const resolvedTab: LearnTab = (() => {
    if (activeTab) return activeTab;
    if (summaries.length > 0) return "summary";
    if (chapters.length > 0)  return "timeline";
    if (concepts.length > 0)  return "concepts";
    return "summary";
  })();

  // Find standard or detailed summary for use in outline
  const outlineSummary =
    summaries.find((s) => s.level === "detailed") ??
    summaries.find((s) => s.level === "standard") ??
    null;

  // Total duration from last chapter
  const totalDuration =
    chapters[chapters.length - 1]?.timestamp_end ??
    chapters[chapters.length - 1]?.timestamp_start ??
    undefined;

  return (
    <div className="flex flex-col gap-4">
      {/* Tab bar */}
      <div className="flex gap-1 rounded-xl border border-lens-glass-border bg-white/3 p-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "flex flex-1 items-center justify-center gap-1.5 rounded-lg py-1.5 text-xs font-medium transition-all",
              resolvedTab === tab.id
                ? "bg-lens-purple/20 text-lens-purple-light shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            <tab.icon className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      {isLoading ? (
        <LoadingState />
      ) : error ? (
        <EmptyState message="Content could not be loaded. The lecture may still be processing." />
      ) : (
        <AnimatePresence mode="wait">
          <motion.div
            key={resolvedTab}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.18 }}
          >
            {resolvedTab === "summary" && (
              <SummaryPanel summaries={summaries} lectureId={lectureId} />
            )}
            {resolvedTab === "outline" && (
              <LectureOutline
                chapters={chapters}
                summary={outlineSummary}
                concepts={concepts}
                lectureId={lectureId}
              />
            )}
            {resolvedTab === "timeline" && (
              <ChapterTimeline
                chapters={chapters}
                lectureId={lectureId}
                totalDuration={totalDuration}
              />
            )}
            {resolvedTab === "concepts" && (
              <ConceptsList concepts={concepts} lectureId={lectureId} />
            )}
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  );
}
