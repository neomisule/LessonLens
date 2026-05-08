"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  BookOpen, Clock, Layers, TrendingUp, Youtube, ArrowRight,
  CheckCircle2, XCircle, Loader2, AlertCircle,
} from "lucide-react";
import { useSubjects } from "@/lib/hooks/useSubjects";
import { useLectures } from "@/lib/hooks/useLectures";
import { useAppStore } from "@/lib/store/appStore";
import { Button } from "@/components/ui/button";
import { MasteryTracker } from "@/components/tracking/MasteryTracker";
import { LectureCardSkeleton, StatSkeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";
import Link from "next/link";
import type { Lecture, ProcessingStatus } from "@/lib/types/lectures";

// ── Processing status badge ──────────────────────────────────────────────────

function ProcessingBadge({ status }: { status: ProcessingStatus }) {
  if (status === "completed") return null;

  const variants: Record<string, { icon: React.ElementType; label: string; className: string }> = {
    failed:      { icon: XCircle,    label: "Failed",      className: "text-red-400 bg-red-500/10 border-red-500/20" },
    queued:      { icon: Clock,      label: "Queued",      className: "text-muted-foreground bg-white/5 border-white/10" },
    processing:  { icon: Loader2,    label: "Processing",  className: "text-amber-400 bg-amber-500/10 border-amber-500/20" },
    transcribing:{ icon: Loader2,    label: "Transcribing",className: "text-blue-400 bg-blue-500/10 border-blue-500/20" },
  };

  const cfg = variants[status] ?? variants.processing;
  const Icon = cfg.icon;
  const isSpinning = ["processing", "transcribing"].includes(status);

  return (
    <span className={cn(
      "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-medium",
      cfg.className,
    )}>
      <Icon className={cn("h-3 w-3", isSpinning && "animate-spin")} />
      {cfg.label}
    </span>
  );
}

// ── Lecture card ──────────────────────────────────────────────────────────────

function LectureCard({ lecture, index }: { lecture: Lecture; index: number }) {
  const { setActiveLecture } = useAppStore();
  const isDone    = lecture.processing_status === "completed";
  const isFailed  = lecture.processing_status === "failed";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      className={cn(
        "glass-card card-hover flex flex-col gap-3 p-4 group",
        isFailed && "border-red-500/20",
      )}
    >
      {/* Thumbnail */}
      {lecture.thumbnail_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={lecture.thumbnail_url}
          alt={lecture.title ?? "Lecture thumbnail"}
          className="w-full rounded-lg aspect-video object-cover ring-1 ring-white/5 group-hover:ring-lens-purple/20 transition-all duration-300"
          loading="lazy"
        />
      ) : (
        <div className="w-full aspect-video rounded-lg bg-white/5 flex items-center justify-center">
          <Youtube className="h-8 w-8 text-muted-foreground/30" />
        </div>
      )}

      {/* Title + channel */}
      <div className="flex flex-col gap-0.5 flex-1">
        <p className="text-sm font-medium text-foreground line-clamp-2 leading-snug">
          {lecture.title ?? "Untitled Lecture"}
        </p>
        {lecture.channel_name && (
          <p className="text-xs text-muted-foreground truncate">{lecture.channel_name}</p>
        )}
      </div>

      {/* Bottom: status / mastery / action */}
      {isDone ? (
        <>
          <MasteryTracker lectureId={lecture.id} compact />
          <Button
            size="sm"
            variant="outline"
            className="w-full justify-between group-hover:border-lens-purple/40 group-hover:text-lens-purple-light transition-colors"
            onClick={() => setActiveLecture(lecture.id)}
            asChild
          >
            <Link href={`/lecture/${lecture.id}`}>
              Open lecture
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </Button>
        </>
      ) : (
        <ProcessingBadge status={lecture.processing_status} />
      )}
    </motion.div>
  );
}

// ── Stat definitions ─────────────────────────────────────────────────────────

const STAT_DEFS = [
  { label: "Subjects",    key: "subjects"   as const, icon: Layers,     color: "text-lens-purple-light" },
  { label: "Lectures",    key: "lectures"   as const, icon: Youtube,    color: "text-red-400"            },
  { label: "Processed",   key: "processed"  as const, icon: TrendingUp, color: "text-green-400"          },
  { label: "In Progress", key: "inProgress" as const, icon: Clock,      color: "text-amber-400"          },
];

// ── Empty states ──────────────────────────────────────────────────────────────

function WelcomeEmpty() {
  return (
    <div className="flex h-full min-h-[60vh] flex-col items-center justify-center gap-8 p-12 text-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 20 }}
        className="relative"
      >
        <div className="flex h-24 w-24 items-center justify-center rounded-3xl bg-lens-gradient text-white glow-purple">
          <BookOpen className="h-12 w-12" />
        </div>
        <div className="absolute -right-1 -top-1 flex h-6 w-6 items-center justify-center rounded-full bg-green-500 text-white">
          <CheckCircle2 className="h-3.5 w-3.5" />
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="max-w-sm space-y-3"
      >
        <h2 className="text-2xl font-bold">Welcome to LectureLens</h2>
        <p className="text-muted-foreground text-sm leading-relaxed">
          Create a subject in the sidebar, then paste a YouTube URL to let AI
          analyze your lecture — flashcards, summaries, mind maps, and smart
          revision plans generated automatically.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="flex items-center gap-6 text-xs text-muted-foreground"
      >
        {["Create a subject", "Paste a YouTube URL", "Start learning"].map((step, i) => (
          <div key={step} className="flex items-center gap-2">
            <div className="flex h-5 w-5 items-center justify-center rounded-full bg-lens-purple/20 text-lens-purple-light text-[10px] font-bold shrink-0">
              {i + 1}
            </div>
            <span>{step}</span>
            {i < 2 && <ArrowRight className="h-3 w-3 opacity-40" />}
          </div>
        ))}
      </motion.div>
    </div>
  );
}

function NoLecturesEmpty() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex h-48 flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-lens-glass-border bg-white/2 text-center"
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/5 text-muted-foreground">
        <Youtube className="h-5 w-5" />
      </div>
      <div className="space-y-1">
        <p className="text-sm font-medium text-foreground/80">No lectures yet</p>
        <p className="text-xs text-muted-foreground max-w-[240px]">
          Paste a YouTube URL in the sidebar to analyze your first lecture.
        </p>
      </div>
    </motion.div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const { data: subjectsData, isLoading: subjectsLoading } = useSubjects();
  const { activeSubjectId }  = useAppStore();
  const { data: lecturesData, isLoading: lecturesLoading } = useLectures(activeSubjectId ?? undefined);

  const subjects = subjectsData?.items ?? [];
  const lectures = lecturesData?.items ?? [];
  const isLoading = subjectsLoading || lecturesLoading;

  // ── True empty — no subjects yet ──────────────────────────────────────────
  if (!subjectsLoading && subjects.length === 0) {
    return <WelcomeEmpty />;
  }

  const statValues = {
    subjects:   subjects.length,
    lectures:   lectures.length,
    processed:  lectures.filter((l) => l.processing_status === "completed").length,
    inProgress: lectures.filter((l) =>
      !["completed", "failed", "queued"].includes(l.processing_status)
    ).length,
  };

  return (
    <div className="flex flex-col gap-8 p-6">
      {/* ── Stats ──────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {isLoading
          ? STAT_DEFS.map((s) => <StatSkeleton key={s.key} />)
          : STAT_DEFS.map((stat, i) => (
              <motion.div
                key={stat.key}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
                className="glass-card p-4 flex items-center gap-3"
              >
                <div className={cn("opacity-80 shrink-0", stat.color)}>
                  <stat.icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xl font-bold text-foreground tabular-nums">
                    {statValues[stat.key]}
                  </p>
                  <p className="text-xs text-muted-foreground">{stat.label}</p>
                </div>
              </motion.div>
            ))}
      </div>

      {/* ── Lecture grid ───────────────────────────────────────────────────── */}
      <AnimatePresence>
        {activeSubjectId && (
          <motion.section
            key={activeSubjectId}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                {subjects.find((s) => s.id === activeSubjectId)?.name ?? "Lectures"}
              </h2>
              {lectures.length > 0 && (
                <span className="text-xs text-muted-foreground tabular-nums">
                  {statValues.processed}/{lectures.length} processed
                </span>
              )}
            </div>

            {lecturesLoading ? (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <LectureCardSkeleton key={i} />
                ))}
              </div>
            ) : lectures.length === 0 ? (
              <NoLecturesEmpty />
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {lectures.map((lecture, i) => (
                  <LectureCard key={lecture.id} lecture={lecture} index={i} />
                ))}
              </div>
            )}
          </motion.section>
        )}
      </AnimatePresence>

      {/* No subject selected yet but subjects exist */}
      {!isLoading && !activeSubjectId && subjects.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex h-48 flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-lens-glass-border text-center"
        >
          <AlertCircle className="h-6 w-6 text-muted-foreground/40" />
          <p className="text-sm text-muted-foreground">
            Select a subject from the sidebar to see its lectures.
          </p>
        </motion.div>
      )}
    </div>
  );
}
