"use client";

import { motion } from "framer-motion";
import { CheckCircle2, XCircle, Loader2, Circle } from "lucide-react";
import { PROCESSING_STEPS } from "@/lib/types/lectures";
import type { ProcessingJob, ProcessingStatus } from "@/lib/types/lectures";
import { cn } from "@/lib/utils/cn";

interface AgentProcessingTimelineProps {
  job: ProcessingJob;
}

type StepState = "completed" | "active" | "error" | "pending";

function getStepState(stepKey: ProcessingStatus, job: ProcessingJob): StepState {
  if (job.status === "failed" && job.current_step === stepKey) return "error";
  if (job.steps_completed.includes(stepKey)) return "completed";
  if (job.current_step === stepKey) return "active";
  return "pending";
}

const STEP_ICON = {
  completed: CheckCircle2,
  active: Loader2,
  error: XCircle,
  pending: Circle,
};

const STEP_COLOR: Record<StepState, string> = {
  completed: "text-green-400",
  active: "text-lens-purple-light",
  error: "text-red-400",
  pending: "text-muted-foreground/40",
};

/** Extract a one-line detail string from progress_metadata for a completed step. */
function getStepDetail(
  stepKey: string,
  job: ProcessingJob,
): string | null {
  const meta = job.progress_metadata;
  if (!meta) return null;
  const d = meta[stepKey] as Record<string, unknown> | undefined;
  if (!d) return null;

  switch (stepKey) {
    case "downloading":
      return d.title ? String(d.title) : null;
    case "transcribing": {
      const words = d.word_count ? `${Number(d.word_count).toLocaleString()} words` : null;
      const cov   = d.coverage_pct ? `${Math.round(Number(d.coverage_pct))}% coverage` : null;
      const parts = [words, cov].filter(Boolean);
      return parts.length ? parts.join(" · ") : null;
    }
    case "segmenting": {
      const segs = d.segment_count ? `${d.segment_count} segments` : null;
      const emb  = d.embeddings_generated ? "embeddings generated" : null;
      const parts = [segs, emb].filter(Boolean);
      return parts.length ? parts.join(" · ") : null;
    }
    default:
      return null;
  }
}

export function AgentProcessingTimeline({ job }: AgentProcessingTimelineProps) {
  return (
    <div className="flex flex-col gap-0">
      {PROCESSING_STEPS.map((step, i) => {
        const state = getStepState(step.key, job);
        const Icon = STEP_ICON[state];
        const isLast = i === PROCESSING_STEPS.length - 1;
        const detail = state === "completed" ? getStepDetail(step.key, job) : null;

        return (
          <div key={step.key} className="flex gap-4">
            {/* Icon + connector */}
            <div className="flex flex-col items-center">
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: i * 0.08 }}
                className={cn("mt-3 shrink-0", STEP_COLOR[state])}
              >
                <Icon
                  className={cn("h-5 w-5", state === "active" && "animate-spin")}
                />
              </motion.div>
              {!isLast && (
                <div
                  className={cn(
                    "mt-1 w-0.5 flex-1 min-h-[1.5rem] rounded-full transition-colors duration-500",
                    state === "completed" ? "bg-green-400/40" : "bg-white/10",
                  )}
                />
              )}
            </div>

            {/* Label + description + optional detail */}
            <motion.div
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.08 }}
              className={cn("pb-5", isLast && "pb-0")}
            >
              <p
                className={cn(
                  "mt-2.5 text-sm font-medium transition-colors",
                  state === "active" && "text-lens-purple-light",
                  state === "completed" && "text-foreground",
                  state === "pending" && "text-muted-foreground/50",
                  state === "error" && "text-red-400",
                )}
              >
                {step.label}
                {state === "active" && (
                  <span className="ml-2 inline-flex gap-0.5">
                    {[0, 1, 2].map((dot) => (
                      <motion.span
                        key={dot}
                        className="inline-block h-1 w-1 rounded-full bg-lens-purple-light"
                        animate={{ opacity: [0.3, 1, 0.3] }}
                        transition={{
                          duration: 1.2,
                          repeat: Infinity,
                          delay: dot * 0.2,
                        }}
                      />
                    ))}
                  </span>
                )}
              </p>

              <p className="text-xs text-muted-foreground/60">{step.description}</p>

              {/* Per-step completion detail */}
              {detail && (
                <motion.p
                  initial={{ opacity: 0, y: 2 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="mt-0.5 text-[11px] text-green-400/80"
                >
                  {detail}
                </motion.p>
              )}
            </motion.div>
          </div>
        );
      })}

      {/* Failed job error banner */}
      {job.status === "failed" && job.error_message && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-xs text-red-400"
        >
          {job.error_message}
        </motion.div>
      )}
    </div>
  );
}
