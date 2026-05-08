"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { BookOpen, Layers, RotateCcw, Search, GitBranch, ArrowLeft } from "lucide-react";
import { useLecture } from "@/lib/hooks/useLectures";
import { LearnMode } from "@/components/content/LearnMode";
import { BreakdownMode } from "@/components/content/BreakdownMode";
import { ReviseMode } from "@/components/revise/ReviseMode";
import { MasteryTracker } from "@/components/tracking/MasteryTracker";
import { SubjectMindMap } from "@/components/mindmap/SubjectMindMap";
import { SearchResults } from "@/components/search/SearchResults";
import { ErrorStateCard } from "@/components/shared/ErrorStateCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils/cn";
import { useSemanticSearch } from "@/lib/hooks/useSearch";
import type { LectureMode } from "@/lib/types/lectures";
import Link from "next/link";

const MODES: { id: LectureMode; label: string; icon: React.ElementType }[] = [
  { id: "learn",         label: "Learn",         icon: BookOpen  },
  { id: "break_it_down", label: "Break It Down",  icon: Layers    },
  { id: "revise",        label: "Revise",         icon: RotateCcw },
  { id: "search",        label: "Search",         icon: Search    },
  { id: "mind_map",      label: "Mind Map",       icon: GitBranch },
];

function SearchMode({ lectureId }: { lectureId: string }) {
  const [query, setQuery] = useState("");
  const { search, data, isPending, lastQuery } = useSemanticSearch();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    search({
      query: query.trim(),
      lecture_id: lectureId,
      limit: 10,
      include_concepts: true,
    });
  };

  return (
    <div className="flex flex-col gap-4">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          placeholder="Ask anything about this lecture…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button type="submit" disabled={!query.trim() || isPending}>
          <Search className="h-4 w-4" />
        </Button>
      </form>

      {isPending && (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 rounded-xl bg-white/5 animate-shimmer" />
          ))}
        </div>
      )}

      {data && !isPending && <SearchResults response={data} />}
    </div>
  );
}

export default function LectureDashboardPage() {
  const { lectureId } = useParams<{ lectureId: string }>();
  const [mode, setMode] = useState<LectureMode>("learn");

  const { data: lecture, isLoading, error } = useLecture(lectureId);

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
      {/* ── Sticky header ──────────────────────────────────────────────────── */}
      <div className="sticky top-0 z-30 border-b border-lens-glass-border glass px-6 py-3">
        <div className="flex items-start gap-4">
          <Button variant="ghost" size="icon-sm" asChild>
            <Link href="/dashboard"><ArrowLeft className="h-4 w-4" /></Link>
          </Button>
          <div className="flex-1 min-w-0">
            <h1 className="text-sm font-semibold text-foreground truncate">
              {lecture.title ?? "Untitled Lecture"}
            </h1>
            {lecture.channel_name && (
              <p className="text-xs text-muted-foreground">{lecture.channel_name}</p>
            )}
          </div>
          <MasteryTracker lectureId={lectureId} compact />
        </div>

        {/* Mode tabs */}
        <div className="mt-3 flex gap-1 overflow-x-auto">
          {MODES.map((m) => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              className={cn(
                "flex shrink-0 items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-all",
                mode === m.id
                  ? "mode-tab-active"
                  : "border-transparent text-muted-foreground hover:text-foreground hover:bg-white/5",
              )}
            >
              <m.icon className="h-3.5 w-3.5" />
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Content area ───────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto p-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={mode}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            {mode === "learn"         && <LearnMode lectureId={lectureId} />}
            {mode === "break_it_down" && <BreakdownMode lectureId={lectureId} />}
            {mode === "revise" && <ReviseMode lectureId={lectureId} />}
            {mode === "search"   && <SearchMode lectureId={lectureId} />}
            {mode === "mind_map" && (
              <SubjectMindMap
                lectureId={lectureId}
                subjectId={lecture.subject_id ?? undefined}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
