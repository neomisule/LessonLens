"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  Mic,
  Captions,
  Clock,
  Hash,
  BarChart3,
  Zap,
} from "lucide-react";
import { TranscriptQualityBadge } from "./TranscriptQualityBadge";
import type { ProcessingJob } from "@/lib/types/lectures";
import type { TranscriptProgressDetail } from "@/lib/types/transcript";
import { cn } from "@/lib/utils/cn";

interface TranscriptStatusCardProps {
  job: ProcessingJob;
  className?: string;
}

/** Pull transcript-step detail from progress_metadata. */
function useTranscriptDetail(job: ProcessingJob): TranscriptProgressDetail | null {
  const meta = job.progress_metadata;
  if (!meta) return null;
  return (meta["transcribing"] as TranscriptProgressDetail) ?? null;
}

function StatPill({ icon: Icon, label, value, className }: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  className?: string;
}) {
  return (
    <div className={cn(
      "flex items-center gap-2 rounded-lg border border-white/5 bg-white/[0.03] px-3 py-2",
      className,
    )}>
      <Icon className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="ml-auto text-xs font-medium text-foreground tabular-nums">{value}</span>
    </div>
  );
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 80 ? "bg-green-400" : pct >= 60 ? "bg-yellow-400" : "bg-red-400";

  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/10">
        <motion.div
          className={cn("h-full rounded-full", color)}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>
      <span className="shrink-0 text-xs font-medium tabular-nums text-foreground">{pct}%</span>
    </div>
  );
}

export function TranscriptStatusCard({ job, className }: TranscriptStatusCardProps) {
  const detail = useTranscriptDetail(job);

  const isTranscribingDone = job.steps_completed.includes("transcribing");
  const isTranscribingActive = job.current_step === "transcribing";
  const isDownloadingDone = job.steps_completed.includes("downloading");

  const downloadDetail = job.progress_metadata?.["downloading"] as
    | { title?: string; channel?: string; method?: string }
    | undefined;

  // Don't render if we haven't even started downloading
  if (!isDownloadingDone && !isTranscribingActive && !isTranscribingDone) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn("glass-card overflow-hidden", className)}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/5 px-4 py-3">
          <div className="flex items-center gap-2.5">
            <div className={cn(
              "flex h-7 w-7 items-center justify-center rounded-lg",
              isTranscribingDone ? "bg-green-500/15 text-green-400"
                : isTranscribingActive ? "bg-lens-purple/15 text-lens-purple-light"
                : "bg-white/5 text-muted-foreground",
            )}>
              <FileText className="h-3.5 w-3.5" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">Transcript</p>
              {downloadDetail?.title && (
                <p className="max-w-[220px] truncate text-[11px] text-muted-foreground">
                  {downloadDetail.title}
                </p>
              )}
            </div>
          </div>

          {isTranscribingDone && detail ? (
            <TranscriptQualityBadge
              method={detail.method ?? "youtube_captions"}
              confidenceAvg={detail.confidence_avg ?? 0.85}
              coveragePct={detail.coverage_pct ?? 100}
            />
          ) : isTranscribingActive ? (
            <span className="flex items-center gap-1.5 text-xs text-lens-purple-light">
              <motion.span
                className="inline-block h-1.5 w-1.5 rounded-full bg-lens-purple-light"
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 1.2, repeat: Infinity }}
              />
              Processing…
            </span>
          ) : null}
        </div>

        {/* Body — only shown after transcription completes */}
        <AnimatePresence>
          {isTranscribingDone && detail && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="overflow-hidden"
            >
              <div className="space-y-3 p-4">
                {/* Confidence bar */}
                <div>
                  <div className="mb-1.5 flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                      <Zap className="h-3 w-3" />
                      Confidence
                    </span>
                    {detail.is_fallback && (
                      <span className="text-[10px] text-accent">AI fallback used</span>
                    )}
                  </div>
                  <ConfidenceBar value={detail.confidence_avg ?? 0.85} />
                </div>

                {/* Stats grid */}
                <div className="grid grid-cols-2 gap-2">
                  {detail.word_count != null && (
                    <StatPill
                      icon={Hash}
                      label="Words"
                      value={detail.word_count.toLocaleString()}
                    />
                  )}
                  {detail.coverage_pct != null && (
                    <StatPill
                      icon={BarChart3}
                      label="Coverage"
                      value={`${Math.round(detail.coverage_pct)}%`}
                    />
                  )}
                  {detail.segment_count != null && (
                    <StatPill
                      icon={FileText}
                      label="Segments"
                      value={detail.segment_count}
                    />
                  )}
                  {detail.gap_count != null && detail.gap_count > 0 && (
                    <StatPill
                      icon={AlertTriangle}
                      label="Gaps"
                      value={detail.gap_count}
                      className="border-yellow-500/15"
                    />
                  )}
                </div>

                {/* Fallback notice */}
                {detail.is_fallback && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex items-start gap-2 rounded-lg border border-accent/15 bg-accent/5 px-3 py-2"
                  >
                    <Mic className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent" />
                    <p className="text-xs text-muted-foreground">
                      YouTube captions were unavailable or low quality. The audio was
                      transcribed by OpenAI Whisper for better accuracy.
                    </p>
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Active state loading skeleton */}
        <AnimatePresence>
          {isTranscribingActive && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-2.5 p-4"
            >
              {[80, 60, 72].map((w, i) => (
                <div
                  key={i}
                  className="h-2 rounded-full bg-white/5 animate-pulse"
                  style={{ width: `${w}%` }}
                />
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </AnimatePresence>
  );
}
