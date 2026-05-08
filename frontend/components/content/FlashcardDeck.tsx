"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RotateCcw, ChevronLeft, ChevronRight, Check, X, Minus } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { contentApi } from "@/lib/api/content";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

interface FlashcardDeckProps { lectureId: string; }

export function FlashcardDeck({ lectureId }: FlashcardDeckProps) {
  const { data: cards = [], isLoading } = useQuery({
    queryKey: ["flashcards", lectureId],
    queryFn: () => contentApi.getFlashcards(lectureId),
  });

  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [results, setResults] = useState<Record<string, "correct" | "incorrect" | "skipped">>({});
  const [finished, setFinished] = useState(false);

  const card = cards[index];
  const progress = cards.length > 0 ? (index / cards.length) * 100 : 0;
  const correctCount = Object.values(results).filter((v) => v === "correct").length;

  const handleResponse = (response: "correct" | "incorrect" | "skipped") => {
    if (!card) return;
    setResults((prev) => ({ ...prev, [card.id]: response }));
    if (index + 1 >= cards.length) { setFinished(true); }
    else { setIndex((i) => i + 1); setFlipped(false); }
  };

  const reset = () => { setIndex(0); setFlipped(false); setResults({}); setFinished(false); };

  if (isLoading) return <div className="h-52 rounded-xl bg-white/5 animate-shimmer" />;
  if (cards.length === 0) return (
    <div className="flex h-40 items-center justify-center rounded-xl border border-dashed border-lens-glass-border text-sm text-muted-foreground">
      No flashcards generated yet.
    </div>
  );

  if (finished) return (
    <motion.div initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }}
      className="glass-card flex flex-col items-center gap-4 py-10 px-6 text-center">
      <div className="text-4xl">🎉</div>
      <h3 className="text-lg font-semibold">Session Complete</h3>
      <p className="text-sm text-muted-foreground">{correctCount}/{cards.length} correct ({Math.round((correctCount / cards.length) * 100)}%)</p>
      <Button onClick={reset} variant="outline"><RotateCcw className="h-4 w-4" /> Review Again</Button>
    </motion.div>
  );

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>{index + 1} / {cards.length}</span>
        <span>{correctCount} correct</span>
      </div>
      <Progress value={progress} />

      <div className="relative h-52 cursor-pointer" onClick={() => setFlipped((f) => !f)} style={{ perspective: 1000 }}>
        <motion.div animate={{ rotateY: flipped ? 180 : 0 }} transition={{ duration: 0.4 }}
          style={{ transformStyle: "preserve-3d", position: "absolute", inset: 0 }}>
          <div className="absolute inset-0 glass-card flex items-center justify-center p-6" style={{ backfaceVisibility: "hidden" }}>
            <div className="flex flex-col items-center gap-3 text-center">
              <Badge variant="outline" className="capitalize">{card?.difficulty}</Badge>
              <p className="text-sm font-medium text-foreground">{card?.front}</p>
              <p className="text-xs text-muted-foreground">Tap to reveal answer</p>
            </div>
          </div>
          <div className="absolute inset-0 glass-card flex items-center justify-center p-6" style={{ backfaceVisibility: "hidden", transform: "rotateY(180deg)" }}>
            <p className="text-sm text-foreground text-center leading-relaxed">{card?.back}</p>
          </div>
        </motion.div>
      </div>

      <AnimatePresence>
        {flipped && (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }} className="flex justify-center gap-3">
            <Button variant="outline" onClick={() => handleResponse("incorrect")} className="flex-1 border-red-500/30 hover:bg-red-500/10 text-red-400"><X className="h-4 w-4" /> Miss</Button>
            <Button variant="outline" onClick={() => handleResponse("skipped")} className="flex-1"><Minus className="h-4 w-4" /> Skip</Button>
            <Button variant="outline" onClick={() => handleResponse("correct")} className="flex-1 border-green-500/30 hover:bg-green-500/10 text-green-400"><Check className="h-4 w-4" /> Got it</Button>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex justify-between">
        <Button variant="ghost" size="sm" onClick={() => { setIndex((i) => Math.max(0, i - 1)); setFlipped(false); }} disabled={index === 0}><ChevronLeft className="h-4 w-4" /> Prev</Button>
        <Button variant="ghost" size="sm" onClick={() => { setIndex((i) => Math.min(cards.length - 1, i + 1)); setFlipped(false); }} disabled={index === cards.length - 1}>Next <ChevronRight className="h-4 w-4" /></Button>
      </div>
    </div>
  );
}
