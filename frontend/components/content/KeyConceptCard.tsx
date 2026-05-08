"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Lightbulb, Star, Clock, ArrowRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { TimestampButton } from "@/components/lectures/TimestampButton";
import { ConceptExamBadge } from "@/components/content/ConceptExamBadge";
import { WhyThisMattersCard } from "@/components/content/WhyThisMattersCard";
import { cn } from "@/lib/utils/cn";
import type { Concept } from "@/lib/types/content";

const IMPORTANCE_CONFIG = {
  core: { label: "Core", variant: "default" as const, icon: Star },
  supporting: { label: "Supporting", variant: "secondary" as const, icon: Lightbulb },
  supplemental: { label: "Supplemental", variant: "outline" as const, icon: Lightbulb },
};

function formatTime(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  return `${Math.round(seconds / 60)}m`;
}

interface KeyConceptCardProps {
  concept: Concept;
  lectureId: string;
}

export function KeyConceptCard({ concept, lectureId }: KeyConceptCardProps) {
  const [expanded, setExpanded] = useState(false);
  const config = IMPORTANCE_CONFIG[concept.importance];

  return (
    <motion.div
      layout
      className="glass-card overflow-hidden"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
    >
      {/* ── Header (always visible) ─────────────────────────────────────── */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-start gap-3 p-4 text-left"
      >
        <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-lens-purple/15 text-lens-purple-light">
          <config.icon className="h-3.5 w-3.5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="text-sm font-semibold text-foreground">{concept.name}</span>
            <Badge variant={config.variant} className="text-[10px]">{config.label}</Badge>
            {concept.exam_likelihood >= 0.3 && (
              <ConceptExamBadge likelihood={concept.exam_likelihood} showLabel={false} />
            )}
          </div>
          <p className="text-xs text-muted-foreground line-clamp-2">{concept.definition}</p>
        </div>
        <ChevronDown
          className={cn(
            "mt-1 h-4 w-4 shrink-0 text-muted-foreground transition-transform",
            expanded && "rotate-180",
          )}
        />
      </button>

      {/* ── Expanded content ─────────────────────────────────────────────── */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 pt-0 flex flex-col gap-3 border-t border-lens-glass-border">
              {/* Explanation */}
              <p className="text-sm text-muted-foreground leading-relaxed pt-3">
                {concept.explanation}
              </p>

              {/* Why it matters */}
              {concept.why_it_matters && (
                <WhyThisMattersCard
                  conceptName={concept.name}
                  whyItMatters={concept.why_it_matters}
                />
              )}

              {/* Examples */}
              {concept.examples && concept.examples.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-foreground mb-1.5">Examples</p>
                  <ul className="flex flex-col gap-1">
                    {concept.examples.map((ex, i) => (
                      <li key={i} className="text-xs text-muted-foreground flex gap-2">
                        <span className="text-lens-teal-light shrink-0">•</span>{ex}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Prerequisites + Related */}
              <div className="flex flex-wrap gap-x-6 gap-y-2">
                {concept.prerequisites && concept.prerequisites.length > 0 && (
                  <div>
                    <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide mb-1">
                      Prerequisites
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {concept.prerequisites.map((p) => (
                        <Badge key={p} variant="outline" className="text-[10px] text-amber-400 border-amber-500/30">
                          {p}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                {concept.related_concepts && concept.related_concepts.length > 0 && (
                  <div>
                    <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide mb-1">
                      Related
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {concept.related_concepts.map((r) => (
                        <Badge key={r} variant="outline" className="text-[10px]">
                          <ArrowRight className="h-2.5 w-2.5 mr-1" />{r}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Footer: timestamp + time-spent + tags */}
              <div className="flex items-center gap-2 flex-wrap">
                {concept.timestamp_start != null && (
                  <TimestampButton seconds={concept.timestamp_start} lectureId={lectureId} />
                )}
                {concept.time_spent_seconds != null && concept.time_spent_seconds > 0 && (
                  <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    {formatTime(concept.time_spent_seconds)} in lecture
                  </span>
                )}
                {concept.exam_likelihood >= 0.3 && (
                  <ConceptExamBadge likelihood={concept.exam_likelihood} />
                )}
                {concept.tags && concept.tags.map((tag) => (
                  <Badge key={tag} variant="outline" className="text-[10px]">{tag}</Badge>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
