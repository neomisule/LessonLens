"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Layers, RefreshCw } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { contentApi } from "@/lib/api/content";
import { useRevisitRecommendations } from "@/lib/hooks/useBreakdown";
import { ConfusionRepairCard } from "@/components/content/ConfusionRepairCard";
import { RevisitCard } from "@/components/content/RevisitCard";
import { cn } from "@/lib/utils/cn";

type BreakdownTab = "concepts" | "revisit";

const TABS: { id: BreakdownTab; label: string; icon: React.ElementType }[] = [
  { id: "concepts", label: "Break It Down", icon: Layers },
  { id: "revisit",  label: "Revisit",       icon: RefreshCw },
];

function LoadingState() {
  return (
    <div className="flex flex-col gap-3">
      {[...Array(4)].map((_, i) => (
        <div
          key={i}
          className="h-20 rounded-xl bg-white/5 animate-shimmer"
          style={{ animationDelay: `${i * 80}ms` }}
        />
      ))}
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex h-48 items-center justify-center rounded-xl border border-dashed border-lens-glass-border text-sm text-muted-foreground">
      {message}
    </div>
  );
}

interface BreakdownModeProps {
  lectureId: string;
}

export function BreakdownMode({ lectureId }: BreakdownModeProps) {
  const [activeTab, setActiveTab] = useState<BreakdownTab>("concepts");
  const [focusedConceptId, setFocusedConceptId] = useState<string | null>(null);

  const { data: concepts = [], isLoading: conceptsLoading } = useQuery({
    queryKey: ["concepts", lectureId],
    queryFn: () => contentApi.getConcepts(lectureId),
    enabled: Boolean(lectureId),
    staleTime: 5 * 60_000,
  });

  const {
    data: revisit = [],
    isLoading: revisitLoading,
  } = useRevisitRecommendations(lectureId, 6);

  // When user clicks a concept from a revisit card, switch to concepts tab
  // and the card with that id will already be in the list
  function handleRevisitConceptClick(conceptId: string) {
    setFocusedConceptId(conceptId);
    setActiveTab("concepts");
  }

  // Sort concepts: put focused concept first, then by exam_likelihood
  const sortedConcepts = [...concepts].sort((a, b) => {
    if (a.id === focusedConceptId) return -1;
    if (b.id === focusedConceptId) return  1;
    return b.exam_likelihood - a.exam_likelihood;
  });

  return (
    <div className="flex flex-col gap-4">
      {/* Tab bar */}
      <div className="flex gap-1 rounded-xl border border-lens-glass-border bg-white/3 p-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "relative flex flex-1 items-center justify-center gap-1.5 rounded-lg py-1.5 text-xs font-medium transition-all",
              activeTab === tab.id
                ? "bg-lens-purple/20 text-lens-purple-light shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            <tab.icon className="h-3.5 w-3.5" />
            {tab.label}
            {tab.id === "revisit" && revisit.length > 0 && (
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-amber-500/25 text-[9px] font-bold text-amber-400">
                {revisit.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -5 }}
          transition={{ duration: 0.18 }}
        >
          {/* ── Concepts tab ─────────────────────────────────────────────── */}
          {activeTab === "concepts" && (
            <div className="flex flex-col gap-2">
              {conceptsLoading ? (
                <LoadingState />
              ) : sortedConcepts.length === 0 ? (
                <EmptyState message="No concepts extracted yet. Processing may still be running." />
              ) : (
                sortedConcepts.map((concept, i) => (
                  <motion.div
                    key={concept.id}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.025 }}
                    // Scroll into view if this concept was just focused
                    ref={(el) => {
                      if (el && concept.id === focusedConceptId) {
                        el.scrollIntoView({ behavior: "smooth", block: "start" });
                        setFocusedConceptId(null);
                      }
                    }}
                  >
                    <ConfusionRepairCard
                      concept={concept}
                      lectureId={lectureId}
                    />
                  </motion.div>
                ))
              )}
            </div>
          )}

          {/* ── Revisit tab ──────────────────────────────────────────────── */}
          {activeTab === "revisit" && (
            <div className="flex flex-col gap-3">
              {revisitLoading ? (
                <LoadingState />
              ) : revisit.length === 0 ? (
                <EmptyState message="No revisit recommendations yet." />
              ) : (
                <>
                  <p className="text-xs text-muted-foreground px-1">
                    Concepts worth revisiting — ranked by importance and exam likelihood.
                  </p>
                  {revisit.map((rec, i) => (
                    <RevisitCard
                      key={rec.concept_id}
                      recommendation={rec}
                      lectureId={lectureId}
                      index={i}
                      onConceptClick={handleRevisitConceptClick}
                    />
                  ))}
                </>
              )}
            </div>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
