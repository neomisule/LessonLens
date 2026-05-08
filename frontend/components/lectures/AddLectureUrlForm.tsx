"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Youtube, Loader2, ArrowRight, AlertCircle } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAddLecture, useAnalyzeLecture } from "@/lib/hooks/useLectures";
import { isValidYouTubeUrl } from "@/lib/utils/youtube";
import { useAppStore } from "@/lib/store/appStore";

interface AddLectureUrlFormProps {
  onJobStarted?: (jobId: string, lectureId: string) => void;
}

export function AddLectureUrlForm({ onJobStarted }: AddLectureUrlFormProps) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { activeSubjectId } = useAppStore();
  const { mutateAsync: addLecture, isPending: isAdding } = useAddLecture();
  const { mutateAsync: analyzeLecture, isPending: isAnalyzing } = useAnalyzeLecture();

  const isValid = isValidYouTubeUrl(url);
  const isPending = isAdding || isAnalyzing;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!activeSubjectId) { setError("Please select a subject first."); return; }
    if (!isValid) { setError("Please enter a valid YouTube URL."); return; }

    try {
      const lecture = await addLecture({ subject_id: activeSubjectId, youtube_url: url });
      const job = await analyzeLecture(lecture.id);
      onJobStarted?.(job.id, lecture.id);
      setUrl("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add lecture.");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <div className="relative flex items-center gap-2">
        <div className="relative flex-1">
          <Youtube className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-red-500" />
          <Input
            placeholder="Paste YouTube lecture URL…"
            value={url}
            onChange={(e) => { setUrl(e.target.value); setError(null); }}
            className="pl-9 pr-4"
            disabled={isPending}
          />
        </div>
        <Button type="submit" disabled={!url || isPending || !activeSubjectId} className="shrink-0">
          {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <><span>Analyze</span><ArrowRight className="h-4 w-4" /></>}
        </Button>
      </div>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-red-400"
          >
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {!activeSubjectId && (
        <p className="text-xs text-muted-foreground">
          Select or create a subject before adding a lecture.
        </p>
      )}
    </form>
  );
}
