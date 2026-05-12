"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useProcessingJob } from "@/lib/hooks/useLectures";
import { AgentProcessingTimeline } from "@/components/processing/AgentProcessingTimeline";
import { TranscriptStatusCard } from "@/components/processing/TranscriptStatusCard";
import { ErrorStateCard } from "@/components/shared/ErrorStateCard";
import { LogoIcon } from "@/components/shared/LogoIcon";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import Link from "next/link";

// Skeleton row for the timeline while loading
function TimelineSkeleton() {
  const widths    = [45, 52, 42, 55, 38];
  const subWidths = [65, 72, 60, 75, 55];
  return (
    <div className="flex flex-col gap-0" aria-label="Loading pipeline steps" aria-busy="true">
      {widths.map((w, i) => (
        <div key={i} className="flex gap-4">
          <div className="flex flex-col items-center">
            <Skeleton className="mt-3 h-5 w-5 shrink-0 rounded-full" />
            {i < 4 && <div className="mt-1 min-h-[1.5rem] w-0.5 flex-1 rounded-full bg-white/5" />}
          </div>
          <div className="flex-1 pb-5 flex flex-col gap-1.5 pt-2.5">
            <Skeleton className="h-3 rounded" style={{ width: `${w}%` }} />
            <Skeleton className="h-2.5 rounded" style={{ width: `${subWidths[i]}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

/** Elapsed timer — counts up from the job's started_at timestamp. */
function useElapsed(startedAt: string | null | undefined): number {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!startedAt) return;
    const startMs = new Date(startedAt).getTime();

    const tick = () => setElapsed(Math.floor((Date.now() - startMs) / 1000));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [startedAt]);

  return elapsed;
}

function formatElapsed(s: number): string {
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return rem === 0 ? `${m}m` : `${m}m ${rem}s`;
}

export default function ProcessingPage() {
  const params       = useParams<{ jobId: string }>();
  const searchParams = useSearchParams();
  const router       = useRouter();

  const lectureId = searchParams.get("lectureId");
  const { data: job, isLoading } = useProcessingJob(params.jobId);

  const elapsed = useElapsed(job?.started_at);
  const isStillRunning = job && !["complete", "completed", "failed"].includes(job.status);

  // Auto-redirect to lecture dashboard when fully complete
  useEffect(() => {
    if (job?.status === "complete" && lectureId) {
      router.push(`/lecture/${lectureId}`);
    }
  }, [job?.status, lectureId, router]);

  // "dashboard_ready" means fast-path content is available — show an action button
  const isDashboardReady =
    job?.status === "dashboard_ready" ||
    job?.status === "deep_materials_generating" ||
    job?.status === "complete";

  const showTranscriptCard =
    job &&
    (job.steps_completed.includes("transcript_extracting") ||
      job.current_step === "transcript_extracting");

  const progressPct = job
    ? Math.round((job.steps_completed.length / job.steps_total) * 100)
    : 0;

  // Show "long lecture" hint after 45 s
  const showLongHint = isStillRunning && elapsed > 45;

  return (
    <div className="flex min-h-screen items-start justify-center px-6 py-16">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md space-y-4"
      >
        {/* Header */}
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
            className="mx-auto mb-4 flex h-16 w-16 items-center justify-center"
          >
            <LogoIcon size="lg" spinning className="shadow-lg shadow-lens-purple/20" />
          </motion.div>
          <h1 className="text-xl font-bold text-foreground">Analyzing Lecture</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Our AI agents are building your study system…
          </p>

          {/* Progress bar + elapsed time */}
          {job && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mx-auto mt-4 flex flex-col items-center gap-1.5"
            >
              <div className="h-1 w-48 overflow-hidden rounded-full bg-white/10">
                <motion.div
                  className="h-full rounded-full bg-lens-gradient"
                  initial={{ width: 0 }}
                  animate={{ width: `${progressPct}%` }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                />
              </div>
              {isStillRunning && elapsed > 0 && (
                <p className="text-[10px] tabular-nums text-muted-foreground/60">
                  {formatElapsed(elapsed)} elapsed · {progressPct}% complete
                </p>
              )}
            </motion.div>
          )}
        </div>

        {/* Long lecture hint */}
        <AnimatePresence>
          {showLongHint && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-xl border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-xs text-amber-300"
            >
              <span className="font-semibold">Long lecture detected.</span>{" "}
              This may take a few extra minutes — concept extraction and summaries
              are running in the background. You can leave this page and come back.
            </motion.div>
          )}
        </AnimatePresence>

        {/* Timeline card */}
        <div className="glass-card p-6">
          {isLoading && <TimelineSkeleton />}
          {job && <AgentProcessingTimeline job={job} />}

          {job?.status === "failed" && (
            <div className="mt-4 flex flex-col gap-3">
              <ErrorStateCard
                message={job.error_message ?? "An unknown error occurred during processing."}
                compact
              />
              <Button variant="outline" asChild>
                <Link href="/dashboard">Back to Dashboard</Link>
              </Button>
            </div>
          )}
        </div>

        {/* "Open dashboard now" — appears as soon as fast-path content is ready */}
        <AnimatePresence>
          {isDashboardReady && lectureId && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-xl border border-lens-purple/30 bg-lens-purple/10 px-5 py-4 flex flex-col gap-3"
            >
              <div>
                <p className="text-sm font-semibold text-lens-purple-light">
                  Your dashboard is ready!
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Key concepts, chapters, and flashcards are available.
                  Deeper summaries and quiz questions are still generating in the background.
                </p>
              </div>
              <Button asChild size="sm" className="self-start gap-1.5">
                <Link href={`/lecture/${lectureId}`}>
                  Open dashboard →
                </Link>
              </Button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Transcript status card — appears after download step */}
        <AnimatePresence>
          {showTranscriptCard && <TranscriptStatusCard job={job!} />}
        </AnimatePresence>

        {/* Helpful tip while waiting */}
        <AnimatePresence>
          {isStillRunning && !showLongHint && !isDashboardReady && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center text-xs text-muted-foreground/50"
            >
              This usually takes 30–90 seconds for a 1-hour lecture.
              You can leave and come back — we'll keep going.
            </motion.p>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
