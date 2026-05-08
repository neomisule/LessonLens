"use client";

import { useEffect } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useProcessingJob } from "@/lib/hooks/useLectures";
import { AgentProcessingTimeline } from "@/components/processing/AgentProcessingTimeline";
import { TranscriptStatusCard } from "@/components/processing/TranscriptStatusCard";
import { ErrorStateCard } from "@/components/shared/ErrorStateCard";
import { Button } from "@/components/ui/button";
import Link from "next/link";

// Skeleton row for the timeline while loading
function TimelineSkeleton() {
  return (
    <div className="flex flex-col gap-0">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex gap-4">
          <div className="flex flex-col items-center">
            <div className="mt-3 h-5 w-5 shrink-0 rounded-full bg-white/10 animate-pulse" />
            {i < 4 && <div className="mt-1 min-h-[1.5rem] w-0.5 flex-1 rounded-full bg-white/5" />}
          </div>
          <div className="flex-1 pb-5 flex flex-col gap-1.5 pt-2.5">
            <div
              className="h-3 rounded bg-white/10 animate-pulse"
              style={{ width: `${[45, 52, 42, 55, 38][i]}%` }}
            />
            <div
              className="h-2.5 rounded bg-white/5 animate-pulse"
              style={{ width: `${[65, 72, 60, 75, 55][i]}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ProcessingPage() {
  const params = useParams<{ jobId: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();

  const lectureId = searchParams.get("lectureId");
  const { data: job, isLoading } = useProcessingJob(params.jobId);

  // Auto-redirect to lecture dashboard on completion
  useEffect(() => {
    if (job?.status === "completed" && lectureId) {
      router.push(`/lecture/${lectureId}`);
    }
  }, [job?.status, lectureId, router]);

  const showTranscriptCard =
    job &&
    (job.steps_completed.includes("downloading") ||
      job.current_step === "transcribing" ||
      job.steps_completed.includes("transcribing"));

  const progressPct =
    job
      ? Math.round((job.steps_completed.length / job.steps_total) * 100)
      : 0;

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
            className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-lens-gradient text-white text-2xl font-bold shadow-lg shadow-lens-purple/20"
          >
            L
          </motion.div>
          <h1 className="text-xl font-bold text-foreground">Analyzing Lecture</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Our AI agents are building your study system…
          </p>

          {/* Progress bar */}
          {job && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mx-auto mt-4 h-1 w-48 overflow-hidden rounded-full bg-white/10"
            >
              <motion.div
                className="h-full rounded-full bg-lens-gradient"
                initial={{ width: 0 }}
                animate={{ width: `${progressPct}%` }}
                transition={{ duration: 0.6, ease: "easeOut" }}
              />
            </motion.div>
          )}
        </div>

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

        {/* Transcript status card — appears after download step */}
        <AnimatePresence>
          {showTranscriptCard && (
            <TranscriptStatusCard job={job!} />
          )}
        </AnimatePresence>

        {/* Helpful tip while waiting */}
        <AnimatePresence>
          {job && !["completed", "failed"].includes(job.status) && (
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
