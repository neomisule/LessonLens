"use client";

import { motion } from "framer-motion";
import { CheckCircle2, XCircle, Loader2, Circle } from "lucide-react";
import { PROCESSING_STEPS } from "@/lib/types/lectures";
import type { ProcessingJob, ProcessingStatus } from "@/lib/types/lectures";
import { cn } from "@/lib/utils/cn";

interface AgentProcessingTimelineProps { job: ProcessingJob; }

type StepState = "completed" | "active" | "error" | "pending";

function getStepState(stepKey: ProcessingStatus, job: ProcessingJob): StepState {
  if (job.status === "failed" && job.current_step === stepKey) return "error";
  if (job.steps_completed.includes(stepKey)) return "completed";
  if (job.current_step === stepKey) return "active";
  return "pending";
}

const STEP_ICON = { completed: CheckCircle2, active: Loader2, error: XCircle, pending: Circle };
const STEP_COLOR: Record<StepState, string> = {
  completed: "text-green-400", active: "text-lens-purple-light",
  error: "text-red-400", pending: "text-muted-foreground/40",
};

export function AgentProcessingTimeline({ job }: AgentProcessingTimelineProps) {
  return (
    <div className="flex flex-col gap-0">
      {PROCESSING_STEPS.map((step, i) => {
        const state = getStepState(step.key, job);
        const Icon = STEP_ICON[state];
        const isLast = i === PROCESSING_STEPS.length - 1;

        return (
          <div key={step.key} className="flex gap-4">
            <div className="flex flex-col items-center">
              <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: i * 0.08 }} className={cn("mt-3 shrink-0", STEP_COLOR[state])}>
                <Icon className={cn("h-5 w-5", state === "active" && "animate-spin")} />
              </motion.div>
              {!isLast && (
                <div className={cn("mt-1 w-0.5 flex-1 min-h-[1.5rem] rounded-full transition-colors duration-500",
                  state === "completed" ? "bg-green-400/40" : "bg-white/10")} />
              )}
            </div>
            <motion.div initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.08 }} className={cn("pb-5", isLast && "pb-0")}>
              <p className={cn("mt-2.5 text-sm font-medium transition-colors",
                state === "active" && "text-lens-purple-light",
                state === "completed" && "text-foreground",
                state === "pending" && "text-muted-foreground/50",
                state === "error" && "text-red-400")}>
                {step.label}
                {state === "active" && (
                  <span className="ml-2 inline-flex gap-0.5">
                    {[0, 1, 2].map((dot) => (
                      <motion.span key={dot} className="inline-block h-1 w-1 rounded-full bg-lens-purple-light"
                        animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1.2, repeat: Infinity, delay: dot * 0.2 }} />
                    ))}
                  </span>
                )}
              </p>
              <p className="text-xs text-muted-foreground/60">{step.description}</p>
            </motion.div>
          </div>
        );
      })}
      {job.status === "failed" && job.error_message && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="mt-4 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-xs text-red-400">
          {job.error_message}
        </motion.div>
      )}
    </div>
  );
}
