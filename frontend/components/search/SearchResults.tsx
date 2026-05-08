"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Clock, BookOpen, Lightbulb, ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Badge } from "@/components/ui/badge";
import { useRelatedMoments } from "@/lib/hooks/useSearch";
import type {
  CombinedSearchResponse,
  SearchResult,
  ConceptSearchResult,
} from "@/lib/types/search";
import { CONFIDENCE_TIER_CONFIG } from "@/lib/types/search";

// ── Timestamp formatter ───────────────────────────────────────────────────────

function fmt(secs: number | null | undefined): string | null {
  if (!secs && secs !== 0) return null;
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

// ── Related moments panel ─────────────────────────────────────────────────────

function RelatedMoments({ segmentId }: { segmentId: string }) {
  const { data, isLoading } = useRelatedMoments(segmentId);

  if (isLoading)
    return <div className="mt-3 h-16 rounded-lg bg-white/5 animate-shimmer" />;

  if (!data?.length) return null;

  return (
    <div className="mt-3 space-y-1.5">
      <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
        Related moments
      </p>
      {data.map((r) => (
        <div
          key={r.segment_id}
          className="flex items-start gap-2 rounded-lg bg-white/5 px-3 py-2 text-xs"
        >
          <div className="shrink-0 mt-0.5">
            <span className={cn("font-mono text-[10px]", CONFIDENCE_TIER_CONFIG[r.confidence_tier].color)}>
              {fmt(r.timestamp_start)}
            </span>
          </div>
          <p className="text-muted-foreground line-clamp-2 leading-relaxed">
            {r.content}
          </p>
          {r.lecture_title !== "Untitled" && (
            <span className="ml-auto shrink-0 text-[10px] text-muted-foreground/60 italic">
              {r.lecture_title.slice(0, 20)}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Segment result card ───────────────────────────────────────────────────────

function SegmentCard({ result, index }: { result: SearchResult; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const tierCfg = CONFIDENCE_TIER_CONFIG[result.confidence_tier];

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      className="glass-card rounded-xl p-4 space-y-2"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold",
              tierCfg.bg, tierCfg.color, "border-current/20"
            )}
          >
            {Math.round(result.similarity * 100)}% {tierCfg.label}
          </span>
          {result.topic_label && (
            <Badge variant="outline" className="text-[10px]">
              {result.topic_label}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {result.timestamp_start !== null && (
            <span className="flex items-center gap-1 text-[11px] font-mono text-lens-primary">
              <Clock className="h-3 w-3" />
              {fmt(result.timestamp_start)}
            </span>
          )}
        </div>
      </div>

      {/* Lecture title */}
      <p className="flex items-center gap-1 text-[11px] text-muted-foreground">
        <BookOpen className="h-3 w-3 shrink-0" />
        <span className="truncate">{result.lecture_title}</span>
      </p>

      {/* Content */}
      <p className="text-sm text-foreground/90 leading-relaxed">
        {result.content}
      </p>

      {/* Related moments toggle */}
      <button
        onClick={() => setExpanded((e) => !e)}
        className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
      >
        {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        {expanded ? "Hide related" : "Show related moments"}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <RelatedMoments segmentId={result.segment_id} />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ── Concept result card ───────────────────────────────────────────────────────

function ConceptCard({
  result,
  index,
}: {
  result: ConceptSearchResult;
  index: number;
}) {
  const tierCfg = CONFIDENCE_TIER_CONFIG[result.confidence_tier];

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="glass-card rounded-xl p-4 space-y-2 border border-lens-primary/10"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <Lightbulb className="h-4 w-4 text-lens-primary shrink-0" />
          <span className="text-sm font-semibold">{result.name}</span>
          <Badge
            variant="outline"
            className={cn("text-[10px]", tierCfg.color)}
          >
            {result.importance}
          </Badge>
        </div>
        {result.timestamp_start !== null && (
          <span className="flex items-center gap-1 text-[11px] font-mono text-lens-primary shrink-0">
            <Clock className="h-3 w-3" />
            {fmt(result.timestamp_start)}
          </span>
        )}
      </div>

      <p className="text-[11px] text-muted-foreground">{result.lecture_title}</p>
      <p className="text-sm text-foreground/80 leading-relaxed line-clamp-3">
        {result.definition}
      </p>

      {result.evidence_quote && (
        <blockquote className="border-l-2 border-lens-primary/40 pl-3 text-[11px] text-muted-foreground italic line-clamp-2">
          "{result.evidence_quote}"
        </blockquote>
      )}

      <div className="flex items-center gap-2">
        <span
          className={cn(
            "text-[10px] font-medium rounded-full px-2 py-0.5 border",
            tierCfg.bg, tierCfg.color, "border-current/20"
          )}
        >
          {Math.round(result.similarity * 100)}% {tierCfg.label}
        </span>
        <span className="text-[10px] text-muted-foreground">
          Exam: {Math.round(result.exam_likelihood * 100)}%
        </span>
      </div>
    </motion.div>
  );
}

// ── Main SearchResults component ──────────────────────────────────────────────

interface SearchResultsProps {
  response: CombinedSearchResponse;
  className?: string;
}

export function SearchResults({ response, className }: SearchResultsProps) {
  const [tab, setTab] = useState<"segments" | "concepts">("segments");

  if (!response.total_segments && !response.total_concepts) {
    return (
      <div className={cn("glass-card p-8 text-center", className)}>
        <p className="text-muted-foreground text-sm">
          No results found for "{response.query}"
        </p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Results summary + tab switcher */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          Found{" "}
          <span className="text-foreground font-medium">{response.total_segments}</span> moments
          {response.total_concepts > 0 && (
            <>
              {" "}and{" "}
              <span className="text-foreground font-medium">{response.total_concepts}</span> concepts
            </>
          )}{" "}
          for "{response.query}"
        </p>

        {response.total_concepts > 0 && (
          <div className="flex rounded-lg bg-white/5 p-1 gap-1">
            <button
              onClick={() => setTab("segments")}
              className={cn(
                "rounded px-3 py-1 text-xs font-medium transition-all",
                tab === "segments"
                  ? "bg-lens-primary/20 text-lens-primary"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              Moments ({response.total_segments})
            </button>
            <button
              onClick={() => setTab("concepts")}
              className={cn(
                "rounded px-3 py-1 text-xs font-medium transition-all",
                tab === "concepts"
                  ? "bg-lens-primary/20 text-lens-primary"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              Concepts ({response.total_concepts})
            </button>
          </div>
        )}
      </div>

      {/* Results */}
      <AnimatePresence mode="wait">
        {tab === "segments" ? (
          <motion.div
            key="segments"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-3"
          >
            {response.segments.map((r, i) => (
              <SegmentCard key={r.segment_id} result={r} index={i} />
            ))}
          </motion.div>
        ) : (
          <motion.div
            key="concepts"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-3"
          >
            {response.concepts.map((r, i) => (
              <ConceptCard key={r.concept_id} result={r} index={i} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
