"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Clock, CheckCircle2, XCircle, Loader2, PlayCircle } from "lucide-react";
import { useLectures } from "@/lib/hooks/useLectures";
import { useAppStore } from "@/lib/store/appStore";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils/cn";
import type { Lecture, ProcessingStatus } from "@/lib/types/lectures";
import { formatTimestamp } from "@/lib/utils/youtube";

function StatusIcon({ status }: { status: ProcessingStatus }) {
  if (status === "completed") return <CheckCircle2 className="h-3.5 w-3.5 text-green-400" />;
  if (status === "failed") return <XCircle className="h-3.5 w-3.5 text-red-400" />;
  if (status === "queued") return <Clock className="h-3.5 w-3.5 text-muted-foreground" />;
  return <Loader2 className="h-3.5 w-3.5 text-lens-purple-light animate-spin" />;
}

interface LectureSidebarProps {
  subjectId: string;
}

export function LectureSidebar({ subjectId }: LectureSidebarProps) {
  const { data, isLoading } = useLectures(subjectId);
  const { activeLectureId, setActiveLecture } = useAppStore();
  const lectures = data?.items ?? [];

  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground px-1">
        Lectures
      </h3>

      {isLoading && (
        <div className="flex flex-col gap-2">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="h-16 rounded-lg bg-white/5 animate-shimmer" />
          ))}
        </div>
      )}

      <AnimatePresence initial={false}>
        {lectures.map((lecture, i) => (
          <motion.button
            key={lecture.id}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.04 }}
            onClick={() => lecture.processing_status === "completed" && setActiveLecture(lecture.id)}
            disabled={lecture.processing_status !== "completed"}
            className={cn(
              "flex flex-col gap-1.5 rounded-lg border p-3 text-left transition-all",
              "disabled:opacity-60 disabled:cursor-not-allowed",
              activeLectureId === lecture.id
                ? "border-lens-purple/30 bg-lens-purple/10"
                : "border-lens-glass-border bg-white/3 hover:bg-white/5"
            )}
          >
            <div className="flex items-start justify-between gap-2">
              <span className="line-clamp-2 text-xs font-medium text-foreground leading-snug">
                {lecture.title ?? "Untitled Lecture"}
              </span>
              <StatusIcon status={lecture.processing_status} />
            </div>
            <div className="flex items-center gap-2">
              {lecture.duration_seconds && (
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <PlayCircle className="h-3 w-3" />
                  {formatTimestamp(lecture.duration_seconds)}
                </span>
              )}
              {lecture.processing_status !== "completed" && lecture.processing_status !== "queued" && (
                <Badge variant="default" className="text-[10px] py-0 px-1.5 capitalize">
                  {lecture.processing_status.replace(/_/g, " ")}
                </Badge>
              )}
            </div>
          </motion.button>
        ))}
      </AnimatePresence>

      {!isLoading && lectures.length === 0 && (
        <p className="text-xs text-muted-foreground px-1">No lectures yet.</p>
      )}
    </div>
  );
}
