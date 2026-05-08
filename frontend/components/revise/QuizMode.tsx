"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, XCircle, ChevronRight, Trophy, RotateCcw, Clock } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { useQuizQuestions } from "@/lib/hooks/useRevise";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { QuizQuestion } from "@/lib/types/revise";

interface QuizModeProps {
  lectureId: string;
  className?: string;
}

type AnswerState = "unanswered" | "correct" | "incorrect";

interface QuizSessionEntry {
  question: QuizQuestion;
  selected: string | null;
  state: AnswerState;
}

function formatTimestamp(secs: number | null | undefined) {
  if (!secs && secs !== 0) return null;
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function ScoreScreen({
  entries,
  onRestart,
}: {
  entries: QuizSessionEntry[];
  onRestart: () => void;
}) {
  const correct = entries.filter((e) => e.state === "correct").length;
  const pct = Math.round((correct / entries.length) * 100);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex flex-col items-center gap-6 py-8"
    >
      <Trophy className="h-12 w-12 text-amber-400" />
      <div className="text-center">
        <p className="text-3xl font-bold">{pct}%</p>
        <p className="text-muted-foreground text-sm mt-1">
          {correct} / {entries.length} correct
        </p>
      </div>

      <div
        className={cn(
          "rounded-xl px-6 py-3 text-sm font-medium",
          pct >= 80 ? "bg-emerald-500/15 text-emerald-400" :
          pct >= 50 ? "bg-amber-500/15  text-amber-400"   :
                      "bg-red-500/15    text-red-400"
        )}
      >
        {pct >= 80 ? "Excellent! Keep it up 🎉" :
         pct >= 50 ? "Good effort — review the missed ones 💪" :
                     "Keep studying — you'll get there 📚"}
      </div>

      <Button onClick={onRestart} className="gap-2">
        <RotateCcw className="h-4 w-4" />
        Try Again
      </Button>
    </motion.div>
  );
}

export function QuizMode({ lectureId, className }: QuizModeProps) {
  const { data, isLoading } = useQuizQuestions(lectureId);

  const [session, setSession] = useState<QuizSessionEntry[]>([]);
  const [qIndex,  setQIndex]  = useState(0);
  const [started, setStarted] = useState(false);
  const [done,    setDone]    = useState(false);

  const startSession = () => {
    if (!data?.questions.length) return;
    setSession(
      data.questions.map((q) => ({ question: q, selected: null, state: "unanswered" }))
    );
    setQIndex(0);
    setDone(false);
    setStarted(true);
  };

  const handleAnswer = (option: string) => {
    const entry = session[qIndex];
    if (entry.state !== "unanswered") return;

    // Normalize: strip "A. " prefix for MCQ options
    const selectedKey = option.split(".")[0].trim();
    const correct = entry.question.correct_answer.trim();
    const isCorrect =
      selectedKey.toLowerCase() === correct.toLowerCase() ||
      option.toLowerCase() === correct.toLowerCase();

    const updated = session.map((e, i) =>
      i === qIndex
        ? { ...e, selected: option, state: (isCorrect ? "correct" : "incorrect") as AnswerState }
        : e
    );
    setSession(updated);
  };

  const goNext = () => {
    if (qIndex + 1 >= session.length) {
      setDone(true);
    } else {
      setQIndex((i) => i + 1);
    }
  };

  if (isLoading) {
    return <div className={cn("h-48 rounded-xl bg-white/5 animate-shimmer", className)} />;
  }

  if (!data?.questions.length) {
    return (
      <div className={cn("glass-card p-8 text-center", className)}>
        <p className="text-muted-foreground text-sm">No quiz questions available yet.</p>
      </div>
    );
  }

  if (!started) {
    return (
      <div className={cn("glass-card p-8 text-center space-y-4", className)}>
        <p className="text-lg font-semibold">Quiz Mode</p>
        <p className="text-muted-foreground text-sm">
          {data.total} questions · grounded in lecture transcript
        </p>
        <Button onClick={startSession} className="gap-2">
          Start Quiz
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    );
  }

  if (done) {
    return (
      <div className={cn("glass-card p-6", className)}>
        <ScoreScreen entries={session} onRestart={startSession} />
      </div>
    );
  }

  const entry = session[qIndex];
  const q     = entry.question;
  const answered = entry.state !== "unanswered";

  const options =
    q.question_type === "true_false"
      ? ["True", "False"]
      : (q.options ?? []);

  return (
    <div className={cn("flex flex-col gap-4", className)}>
      {/* Progress */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>{qIndex + 1} / {session.length}</span>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-[10px]">{q.question_type === "true_false" ? "T/F" : "MCQ"}</Badge>
          <Badge variant="outline" className="text-[10px]">{q.difficulty}</Badge>
        </div>
      </div>
      <div className="h-1 w-full bg-white/10 rounded-full">
        <div
          className="h-1 bg-lens-primary rounded-full transition-all"
          style={{ width: `${((qIndex + 1) / session.length) * 100}%` }}
        />
      </div>

      {/* Question */}
      <div className="glass-card p-5 rounded-2xl">
        <p className="text-sm font-medium leading-relaxed">{q.question_text}</p>
        {q.timestamp_start !== null && (
          <div className="flex items-center gap-1 mt-2 text-[10px] text-muted-foreground">
            <Clock className="h-3 w-3" />
            <span>{formatTimestamp(q.timestamp_start)}</span>
          </div>
        )}
      </div>

      {/* Options */}
      <div className="flex flex-col gap-2">
        {options.map((opt) => {
          const key       = opt.split(".")[0].trim();
          const isCorrect = key.toLowerCase() === q.correct_answer.trim().toLowerCase() ||
                            opt.toLowerCase() === q.correct_answer.trim().toLowerCase();
          const isSelected = entry.selected === opt;

          return (
            <motion.button
              key={opt}
              onClick={() => handleAnswer(opt)}
              whileHover={!answered ? { scale: 1.01 } : {}}
              whileTap={!answered ? { scale: 0.99 } : {}}
              className={cn(
                "flex items-center gap-3 rounded-xl border px-4 py-3 text-sm text-left transition-all",
                !answered && "hover:bg-white/5 border-white/10",
                answered && isCorrect  && "bg-emerald-500/15 border-emerald-500/30 text-emerald-300",
                answered && isSelected && !isCorrect && "bg-red-500/15 border-red-500/30 text-red-300",
                answered && !isSelected && !isCorrect && "opacity-50 border-white/5",
              )}
              disabled={answered}
            >
              {answered && isCorrect  && <CheckCircle className="h-4 w-4 text-emerald-400 shrink-0" />}
              {answered && isSelected && !isCorrect && <XCircle className="h-4 w-4 text-red-400 shrink-0" />}
              {(!answered || (!isCorrect && !isSelected)) && (
                <span className="h-4 w-4 shrink-0 rounded-full border border-current/30 text-[10px] flex items-center justify-center font-mono">
                  {key}
                </span>
              )}
              <span>{q.question_type === "true_false" ? opt : opt.replace(/^[A-D]\.\s*/, "")}</span>
            </motion.button>
          );
        })}
      </div>

      {/* Explanation after answering */}
      <AnimatePresence>
        {answered && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
              "rounded-xl border p-4 text-sm space-y-2",
              entry.state === "correct"
                ? "bg-emerald-500/10 border-emerald-500/20"
                : "bg-red-500/10 border-red-500/20"
            )}
          >
            <p className="font-medium">
              {entry.state === "correct" ? "✓ Correct!" : `✗ Correct answer: ${q.correct_answer}`}
            </p>
            <p className="text-muted-foreground text-[12px] leading-relaxed">
              {q.explanation}
            </p>
            {q.evidence_quote && (
              <blockquote className="border-l-2 border-lens-primary/40 pl-3 text-[11px] text-muted-foreground italic">
                "{q.evidence_quote}"
              </blockquote>
            )}
            <Button size="sm" onClick={goNext} className="mt-1 gap-1.5">
              {qIndex + 1 >= session.length ? "See Results" : "Next"}
              <ChevronRight className="h-3.5 w-3.5" />
            </Button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
