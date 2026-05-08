"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { BookOpen, Layers, RotateCcw, Search, GitBranch, ArrowLeft } from "lucide-react";
import { useLecture } from "@/lib/hooks/useLectures";
import { useQuery } from "@tanstack/react-query";
import { contentApi } from "@/lib/api/content";
import { SummarySelector } from "@/components/content/SummarySelector";
import { KeyConceptCard } from "@/components/content/KeyConceptCard";
import { FlashcardDeck } from "@/components/content/FlashcardDeck";
import { MasteryTracker } from "@/components/tracking/MasteryTracker";
import { SubjectMindMap } from "@/components/mindmap/SubjectMindMap";
import { ErrorStateCard } from "@/components/shared/ErrorStateCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils/cn";
import type { LectureMode } from "@/lib/types/lectures";
import type { SearchQuery } from "@/lib/types/content";
import Link from "next/link";

const MODES: { id: LectureMode; label: string; icon: React.ElementType }[] = [
  { id: "learn", label: "Learn", icon: BookOpen },
  { id: "break_it_down", label: "Break It Down", icon: Layers },
  { id: "revise", label: "Revise", icon: RotateCcw },
  { id: "search", label: "Search", icon: Search },
  { id: "mind_map", label: "Mind Map", icon: GitBranch },
];

function SearchMode({ lectureId }: { lectureId: string }) {
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState("");

  const { data: results, isLoading } = useQuery({
    queryKey: ["search", lectureId, submitted],
    queryFn: () => contentApi.search({ query: submitted, lecture_id: lectureId, limit: 10 } as SearchQuery),
    enabled: Boolean(submitted),
  });

  return (
    <div className="flex flex-col gap-4">
      <form onSubmit={(e) => { e.preventDefault(); setSubmitted(query); }} className="flex gap-2">
        <Input placeholder="Ask anything about this lecture…" value={query} onChange={(e) => setQuery(e.target.value)} />
        <Button type="submit" disabled={!query || isLoading}><Search className="h-4 w-4" /></Button>
      </form>
      {isLoading && <div className="h-32 rounded-xl bg-white/5 animate-shimmer" />}
      {results?.map((r, i) => (
        <motion.div key={r.segment_id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }} className="glass-card p-4">
          <div className="flex items-center justify-between mb-2">
            <Badge variant="outline" className="text-[10px]">{Math.round(r.similarity * 100)}% match</Badge>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">{r.content}</p>
        </motion.div>
      ))}
    </div>
  );
}

export default function LectureDashboardPage() {
  const { lectureId } = useParams<{ lectureId: string }>();
  const [mode, setMode] = useState<LectureMode>("learn");

  const { data: lecture, isLoading, error } = useLecture(lectureId);
  const { data: concepts = [] } = useQuery({
    queryKey: ["concepts", lectureId],
    queryFn: () => contentApi.getConcepts(lectureId),
    enabled: mode === "break_it_down" && Boolean(lectureId),
  });

  if (isLoading) return (
    <div className="flex h-full items-center justify-center">
      <div className="h-12 w-48 rounded-xl bg-white/5 animate-shimmer" />
    </div>
  );

  if (error || !lecture) return (
    <div className="flex h-full items-center justify-center p-6">
      <ErrorStateCard message="Failed to load lecture." className="max-w-sm" />
    </div>
  );

  return (
    <div className="flex h-full flex-col">
      <div className="sticky top-0 z-30 border-b border-lens-glass-border glass px-6 py-3">
        <div className="flex items-start gap-4">
          <Button variant="ghost" size="icon-sm" asChild>
            <Link href="/dashboard"><ArrowLeft className="h-4 w-4" /></Link>
          </Button>
          <div className="flex-1 min-w-0">
            <h1 className="text-sm font-semibold text-foreground truncate">{lecture.title ?? "Untitled Lecture"}</h1>
            {lecture.channel_name && <p className="text-xs text-muted-foreground">{lecture.channel_name}</p>}
          </div>
          <MasteryTracker lectureId={lectureId} compact />
        </div>
        <div className="mt-3 flex gap-1 overflow-x-auto">
          {MODES.map((m) => (
            <button key={m.id} onClick={() => setMode(m.id)}
              className={cn("flex shrink-0 items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-all",
                mode === m.id ? "mode-tab-active" : "border-transparent text-muted-foreground hover:text-foreground hover:bg-white/5")}>
              <m.icon className="h-3.5 w-3.5" />{m.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <AnimatePresence mode="wait">
          <motion.div key={mode} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.2 }}>
            {mode === "learn" && <SummarySelector lectureId={lectureId} />}
            {mode === "break_it_down" && (
              <div className="flex flex-col gap-3">
                {concepts.length === 0
                  ? <div className="flex h-40 items-center justify-center rounded-xl border border-dashed border-lens-glass-border text-sm text-muted-foreground">No concepts extracted yet.</div>
                  : concepts.map((concept) => <KeyConceptCard key={concept.id} concept={concept} lectureId={lectureId} />)
                }
              </div>
            )}
            {mode === "revise" && <div className="flex flex-col gap-6 max-w-xl mx-auto"><FlashcardDeck lectureId={lectureId} /></div>}
            {mode === "search" && <SearchMode lectureId={lectureId} />}
            {mode === "mind_map" && <SubjectMindMap lectureId={lectureId} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
