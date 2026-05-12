"use client";

import { useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, Send, RotateCcw, ChevronDown, ChevronUp, Clock, Volume2, Square } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { useQuery } from "@tanstack/react-query";
import { contentApi } from "@/lib/api/content";
import { useOralQuestion, useEvaluateOralAnswer } from "@/lib/hooks/useRevise";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { Concept } from "@/lib/types/content";

// ── Types ──────────────────────────────────────────────────────────────────────

interface OralExamModeProps {
  lectureId: string;
  className?: string;
}

type VoiceState = "idle" | "speaking" | "listening" | "transcribing";

// ── ScoreBadge ─────────────────────────────────────────────────────────────────

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 80 ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/20" :
    score >= 50 ? "bg-amber-500/15  text-amber-400  border-amber-500/20"   :
                  "bg-red-500/15    text-red-400    border-red-500/20";
  return (
    <span className={cn("rounded-full border px-2 py-0.5 text-sm font-bold", color)}>
      {score}/100
    </span>
  );
}

// ── Voice helpers ──────────────────────────────────────────────────────────────

/** Speak text via browser TTS (Web Speech API). Returns a cancel fn. */
function speakText(text: string, onEnd?: () => void): () => void {
  if (typeof window === "undefined" || !window.speechSynthesis) {
    onEnd?.();
    return () => {};
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate  = 0.95;
  utterance.pitch = 1;
  utterance.onend = () => onEnd?.();
  window.speechSynthesis.speak(utterance);
  return () => window.speechSynthesis.cancel();
}

/** Check if Web Speech Recognition is available. */
function hasSpeechRecognition(): boolean {
  if (typeof window === "undefined") return false;
  return "SpeechRecognition" in window || "webkitSpeechRecognition" in window;
}

// ── OralSession ────────────────────────────────────────────────────────────────

function OralSession({ lectureId, concept }: { lectureId: string; concept: Concept }) {
  const { data: question, isLoading: qLoading, refetch } = useOralQuestion(
    lectureId, concept.id,
  );
  const { mutate: evaluate, isPending, data: feedback } = useEvaluateOralAnswer();

  const [answer,       setAnswer]       = useState("");
  const [showCitations, setShowCitations] = useState(false);
  const [voiceState,   setVoiceState]   = useState<VoiceState>("idle");
  const [voiceError,   setVoiceError]   = useState<string | null>(null);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null);
  const cancelTtsRef   = useRef<(() => void) | null>(null);

  // ── Listen (TTS) ────────────────────────────────────────────────────────────

  const handleListen = useCallback(() => {
    if (!question) return;
    if (voiceState === "speaking") {
      cancelTtsRef.current?.();
      setVoiceState("idle");
      return;
    }
    setVoiceError(null);
    setVoiceState("speaking");
    cancelTtsRef.current = speakText(question.question_text, () => setVoiceState("idle"));
  }, [question, voiceState]);

  // ── Speak answer (Speech Recognition) ──────────────────────────────────────

  const handleSpeak = useCallback(() => {
    if (!hasSpeechRecognition()) {
      setVoiceError("Speech recognition is not supported in this browser. Try Chrome or Edge.");
      return;
    }

    if (voiceState === "listening") {
      recognitionRef.current?.stop();
      return;
    }

    setVoiceError(null);
    setVoiceState("listening");

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const w = window as any;
    const SpeechRecognitionCtor: (new () => any) | undefined =
      w.SpeechRecognition ?? w.webkitSpeechRecognition;

    if (!SpeechRecognitionCtor) return;

    const rec = new SpeechRecognitionCtor();
    rec.continuous    = true;
    rec.interimResults = false;
    rec.lang          = "en-US";

    rec.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((r: any) => r[0].transcript)
        .join(" ")
        .trim();
      setAnswer((prev) => (prev ? `${prev} ${transcript}` : transcript));
    };

    rec.onend = () => {
      setVoiceState("idle");
      recognitionRef.current = null;
    };

    rec.onerror = (event: any) => {
      setVoiceState("idle");
      recognitionRef.current = null;
      if (event.error !== "aborted") {
        setVoiceError(`Mic error: ${event.error}`);
      }
    };

    recognitionRef.current = rec;
    rec.start();
  }, [voiceState]);

  const handleSubmit = () => {
    if (!question || !answer.trim()) return;
    evaluate({
      concept_id: concept.id,
      question_text: question.question_text,
      student_answer: answer.trim(),
    });
  };

  const handleReset = () => {
    recognitionRef.current?.stop();
    cancelTtsRef.current?.();
    setAnswer("");
    setVoiceState("idle");
    setVoiceError(null);
    refetch();
  };

  if (qLoading) {
    return <div className="h-32 rounded-xl bg-white/5 animate-shimmer" />;
  }

  if (!question) return null;

  return (
    <div className="flex flex-col gap-4">
      {/* Question card */}
      <div className="glass-card rounded-2xl p-5 space-y-3">
        <div className="flex items-center gap-2">
          <Mic className="h-4 w-4 text-lens-primary" />
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Oral Question
          </span>
          {question.timestamp_start !== null && (
            <div className="flex items-center gap-1 text-[10px] text-muted-foreground ml-auto">
              <Clock className="h-3 w-3" />
              <span>
                {Math.floor(question.timestamp_start / 60)}:
                {String(Math.floor(question.timestamp_start % 60)).padStart(2, "0")}
              </span>
            </div>
          )}
        </div>

        <p className="text-sm font-medium leading-relaxed">{question.question_text}</p>

        {/* Listen button */}
        <button
          onClick={handleListen}
          className={cn(
            "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all",
            voiceState === "speaking"
              ? "bg-lens-purple/20 text-lens-purple-light border border-lens-purple/30 animate-pulse"
              : "bg-white/5 text-muted-foreground border border-white/10 hover:bg-white/10 hover:text-foreground",
          )}
        >
          {voiceState === "speaking" ? (
            <><Square className="h-3 w-3" /> Stop</>
          ) : (
            <><Volume2 className="h-3 w-3" /> Listen to question</>
          )}
        </button>
      </div>

      {/* Answer area */}
      {!feedback && (
        <>
          <div className="relative">
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder={
                voiceState === "listening"
                  ? "Listening… speak your answer"
                  : "Type your answer here, or use the mic button below…"
              }
              rows={5}
              className={cn(
                "w-full rounded-xl border bg-white/5 px-4 py-3",
                "text-sm text-foreground placeholder:text-muted-foreground",
                "focus:outline-none focus:ring-1 focus:ring-lens-primary/50 resize-none",
                voiceState === "listening"
                  ? "border-lens-primary/50 ring-1 ring-lens-primary/30"
                  : "border-white/10",
              )}
            />
          </div>

          {/* Voice error */}
          {voiceError && (
            <p className="text-xs text-red-400">{voiceError}</p>
          )}

          <div className="flex items-center justify-between gap-2">
            {/* Speak button */}
            <button
              onClick={handleSpeak}
              title={hasSpeechRecognition() ? "Speak your answer" : "Speech recognition unavailable"}
              className={cn(
                "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium border transition-all",
                voiceState === "listening"
                  ? "bg-red-500/20 text-red-400 border-red-500/30 animate-pulse"
                  : "bg-white/5 text-muted-foreground border-white/10 hover:bg-white/10 hover:text-foreground",
                !hasSpeechRecognition() && "opacity-40 cursor-not-allowed",
              )}
              disabled={!hasSpeechRecognition() || voiceState === "speaking"}
            >
              {voiceState === "listening" ? (
                <><MicOff className="h-3 w-3" /> Stop recording</>
              ) : (
                <><Mic className="h-3 w-3" /> Speak answer</>
              )}
            </button>

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleReset}
                className="text-xs gap-1"
              >
                <RotateCcw className="h-3 w-3" />
                New question
              </Button>
              <Button
                size="sm"
                onClick={handleSubmit}
                disabled={!answer.trim() || isPending || voiceState !== "idle"}
                className="gap-1.5"
              >
                <Send className="h-3.5 w-3.5" />
                {isPending ? "Evaluating…" : "Submit"}
              </Button>
            </div>
          </div>
        </>
      )}

      {/* Feedback */}
      <AnimatePresence>
        {feedback && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-3"
          >
            {/* Score + overview */}
            <div className="glass-card rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold">Evaluation</span>
                <ScoreBadge score={feedback.score} />
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {feedback.feedback}
              </p>
            </div>

            {/* Strong points */}
            {feedback.strong_points.length > 0 && (
              <div className="rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-4 space-y-1.5">
                <p className="text-xs font-medium text-emerald-400">✓ Strong points</p>
                {feedback.strong_points.map((pt, i) => (
                  <p key={i} className="text-[12px] text-emerald-300/80 leading-relaxed">
                    • {pt}
                  </p>
                ))}
              </div>
            )}

            {/* Missed points */}
            {feedback.missed_points.length > 0 && (
              <div className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-4 space-y-1.5">
                <p className="text-xs font-medium text-amber-400">⚠ Points to add</p>
                {feedback.missed_points.map((pt, i) => (
                  <p key={i} className="text-[12px] text-amber-300/80 leading-relaxed">
                    • {pt}
                  </p>
                ))}
              </div>
            )}

            {/* Transcript citations */}
            {feedback.timestamp_citations.length > 0 && (
              <div className="glass-card rounded-xl">
                <button
                  onClick={() => setShowCitations((s) => !s)}
                  className="flex w-full items-center justify-between p-4 text-xs font-medium"
                >
                  <span>Transcript citations ({feedback.timestamp_citations.length})</span>
                  {showCitations ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                </button>
                <AnimatePresence>
                  {showCitations && (
                    <motion.div
                      initial={{ height: 0 }}
                      animate={{ height: "auto" }}
                      exit={{ height: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="px-4 pb-4 space-y-2">
                        {feedback.timestamp_citations.map((c, i) => (
                          <div key={i} className="text-[11px] text-muted-foreground">
                            <span className="font-mono text-lens-primary mr-2">
                              {Math.floor(c.ts / 60)}:{String(Math.floor(c.ts % 60)).padStart(2, "0")}
                            </span>
                            <span className="italic">&ldquo;{c.quote}&rdquo;</span>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}

            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              className="w-full gap-1.5"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              Try another question
            </Button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── OralExamMode (concept selector) ───────────────────────────────────────────

export function OralExamMode({ lectureId, className }: OralExamModeProps) {
  const { data: learnData, isLoading } = useQuery({
    queryKey: ["learn", lectureId],
    queryFn: () => contentApi.getLearnMode(lectureId),
    staleTime: 5 * 60 * 1000,
  });

  const [selectedConcept, setSelectedConcept] = useState<Concept | null>(null);

  const concepts = (learnData?.concepts ?? [])
    .filter((c) => c.importance === "core" || c.importance === "supporting")
    .sort((a, b) => (b.exam_likelihood ?? 0) - (a.exam_likelihood ?? 0))
    .slice(0, 10);

  if (isLoading) {
    return <div className={cn("h-48 rounded-xl bg-white/5 animate-shimmer", className)} />;
  }

  if (!concepts.length) {
    return (
      <div className={cn("glass-card p-8 text-center", className)}>
        <p className="text-muted-foreground text-sm">No concepts available for oral exam.</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {!selectedConcept ? (
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">
            Choose a concept to be orally examined on:
          </p>
          {concepts.map((c) => (
            <motion.button
              key={c.id}
              onClick={() => setSelectedConcept(c)}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              className="w-full text-left glass-card rounded-xl px-4 py-3 flex items-center justify-between gap-3 hover:bg-white/5 transition-colors"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium truncate">{c.name}</p>
                <p className="text-[11px] text-muted-foreground">{c.importance}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {c.exam_likelihood !== undefined && (
                  <Badge variant="outline" className="text-[10px]">
                    {Math.round(c.exam_likelihood * 100)}% exam
                  </Badge>
                )}
              </div>
            </motion.button>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold">{selectedConcept.name}</p>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedConcept(null)}
              className="text-xs"
            >
              ← Change concept
            </Button>
          </div>
          <OralSession lectureId={lectureId} concept={selectedConcept} />
        </div>
      )}
    </div>
  );
}
