"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, Eye, EyeOff, RotateCcw, Clock } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { useFlashcards, useMastery, useUpdateConfidence } from "@/lib/hooks/useRevise";
import { ConfidenceButtons } from "./ConfidenceButtons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Flashcard, Confidence, MasteryRecord } from "@/lib/types/revise";
import {
  CONFIDENCE_CONFIG,
  QUESTION_TYPE_CONFIG,
} from "@/lib/types/revise";

interface FlashcardDeckV2Props {
  lectureId: string;
  className?: string;
}

function formatTimestamp(secs: number | null | undefined) {
  if (!secs && secs !== 0) return null;
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function FlashcardDeckV2({ lectureId, className }: FlashcardDeckV2Props) {
  const { data, isLoading }            = useFlashcards(lectureId);
  const { data: masteryRecords }       = useMastery(lectureId);
  const { mutate: updateConf, isPending } = useUpdateConfidence(lectureId);

  const [index,    setIndex]    = useState(0);
  const [flipped,  setFlipped]  = useState(false);
  const [showHint, setShowHint] = useState(false);
  const [direction, setDirection] = useState(1); // 1=next, -1=prev

  const cards: Flashcard[] = data?.flashcards ?? [];

  // Build mastery lookup by flashcard_id
  const masteryMap: Record<string, MasteryRecord> = {};
  (masteryRecords ?? []).forEach((m) => {
    if (m.flashcard_id) masteryMap[m.flashcard_id] = m;
  });

  const current = cards[index];
  const mastery  = current ? masteryMap[current.id] : undefined;

  // Reset flip on card change
  useEffect(() => {
    setFlipped(false);
    setShowHint(false);
  }, [index]);

  // Keyboard navigation
  const navigate = useCallback((dir: 1 | -1) => {
    setDirection(dir);
    setIndex((i) => (i + dir + cards.length) % cards.length);
  }, [cards.length]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") navigate(1);
      if (e.key === "ArrowLeft")  navigate(-1);
      if (e.key === " ")          { e.preventDefault(); setFlipped((f) => !f); }
      if (e.key === "1") updateConf({ flashcard_id: current?.id ?? "", confidence: "confused" });
      if (e.key === "2") updateConf({ flashcard_id: current?.id ?? "", confidence: "shaky" });
      if (e.key === "3") updateConf({ flashcard_id: current?.id ?? "", confidence: "mastered" });
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [navigate, current, updateConf]);

  if (isLoading) {
    return (
      <div className={cn("space-y-4", className)}>
        <div className="h-56 rounded-2xl bg-white/5 animate-shimmer" />
        <div className="h-10 rounded-xl bg-white/5 animate-shimmer" />
      </div>
    );
  }

  if (!cards.length) {
    return (
      <div className={cn("glass-card p-8 text-center", className)}>
        <p className="text-muted-foreground text-sm">
          No flashcards yet — processing may still be running.
        </p>
      </div>
    );
  }

  const qtCfg   = QUESTION_TYPE_CONFIG[current.question_type];
  const confCfg = mastery ? CONFIDENCE_CONFIG[mastery.confidence as Confidence] : null;

  return (
    <div className={cn("flex flex-col gap-4", className)}>
      {/* Progress */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>{index + 1} / {cards.length}</span>
        <div className="flex items-center gap-2">
          {confCfg && (
            <span className={cn("text-[11px] font-medium", confCfg.color)}>
              {confCfg.emoji} {confCfg.label}
            </span>
          )}
          <Badge variant="outline" className={cn("text-[10px]", qtCfg.color)}>
            {qtCfg.label}
          </Badge>
          <Badge variant="outline" className="text-[10px]">
            {current.difficulty}
          </Badge>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1 w-full bg-white/10 rounded-full">
        <motion.div
          className="h-1 bg-lens-primary rounded-full"
          animate={{ width: `${((index + 1) / cards.length) * 100}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>

      {/* Card */}
      <div
        className="relative h-64 cursor-pointer select-none"
        style={{ perspective: "1000px" }}
        onClick={() => setFlipped((f) => !f)}
      >
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={`${current.id}-${flipped}`}
            custom={direction}
            initial={{ rotateY: flipped ? -90 : 90, opacity: 0 }}
            animate={{ rotateY: 0, opacity: 1 }}
            exit={{ rotateY: flipped ? 90 : -90, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className={cn(
              "absolute inset-0 rounded-2xl border glass-card p-6",
              "flex flex-col justify-between backface-hidden",
              flipped ? "bg-lens-primary/5 border-lens-primary/30" : ""
            )}
          >
            <div className="flex flex-col gap-3 flex-1">
              <p className="text-[11px] text-muted-foreground uppercase tracking-wider font-medium">
                {flipped ? "Answer" : "Question"}
              </p>
              <p className="text-base font-medium text-foreground leading-relaxed flex-1">
                {flipped ? current.back : current.front}
              </p>

              {flipped && current.evidence_quote && (
                <blockquote className="mt-2 border-l-2 border-lens-primary/40 pl-3 text-[11px] text-muted-foreground italic line-clamp-3">
                  "{current.evidence_quote}"
                </blockquote>
              )}
            </div>

            {/* Timestamp */}
            {current.timestamp_start !== null && (
              <div className="flex items-center gap-1 text-[10px] text-muted-foreground mt-2">
                <Clock className="h-3 w-3" />
                <span>{formatTimestamp(current.timestamp_start)}</span>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Hint */}
      {current.hint && !flipped && (
        <button
          onClick={() => setShowHint((s) => !s)}
          className="flex items-center gap-1.5 text-[11px] text-muted-foreground hover:text-foreground transition-colors mx-auto"
        >
          {showHint ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
          {showHint ? "Hide hint" : "Show hint"}
        </button>
      )}
      {showHint && current.hint && (
        <motion.div
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-lg bg-amber-500/10 border border-amber-500/20 px-3 py-2 text-[12px] text-amber-300 text-center"
        >
          💡 {current.hint}
        </motion.div>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" size="icon-sm" onClick={() => navigate(-1)}>
          <ChevronLeft className="h-4 w-4" />
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={() => setFlipped((f) => !f)}
          className="text-xs gap-1.5"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          {flipped ? "Show Question" : "Reveal Answer"}
        </Button>

        <Button variant="ghost" size="icon-sm" onClick={() => navigate(1)}>
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Confidence buttons (only after flip) */}
      <AnimatePresence>
        {flipped && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4 }}
          >
            <p className="text-center text-[11px] text-muted-foreground mb-2">
              How well did you know this?
            </p>
            <ConfidenceButtons
              onSelect={(conf) => {
                updateConf({ flashcard_id: current.id, confidence: conf });
                navigate(1);
              }}
              loading={isPending}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Keyboard hints */}
      <p className="text-center text-[10px] text-muted-foreground">
        Space to flip · ← → to navigate · 1/2/3 to rate
      </p>
    </div>
  );
}
