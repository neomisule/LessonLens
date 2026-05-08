"use client";

import { useEffect } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useProcessingJob } from "@/lib/hooks/useLectures";
import { AgentProcessingTimeline } from "@/components/processing/AgentProcessingTimeline";
import { ErrorStateCard } from "@/components/shared/ErrorStateCard";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function ProcessingPage() {
  const params = useParams<{ jobId: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();

  const lectureId = searchParams.get("lectureId");
  const { data: job, isLoading } = useProcessingJob(params.jobId);

  useEffect(() => {
    if (job?.status === "completed" && lectureId) {
      router.push(`/lecture/${lectureId}`);
    }
  }, [job?.status, lectureId, router]);

  return (
    <div className="flex min-h-screen items-center justify-center px-6">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <div className="mb-8 text-center">
          <motion.div animate={{ rotate: 360 }} transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
            className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-lens-gradient text-white text-2xl font-bold shadow-lg shadow-lens-purple/20">
            L
          </motion.div>
          <h1 className="text-xl font-bold text-foreground">Analyzing Lecture</h1>
          <p className="mt-1 text-sm text-muted-foreground">Our AI agents are building your study system…</p>
        </div>

        <div className="glass-card p-6">
          {isLoading && (
            <div className="flex flex-col gap-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex gap-4">
                  <div className="mt-3 h-5 w-5 rounded-full bg-white/10 animate-shimmer shrink-0" />
                  <div className="flex-1 flex flex-col gap-1.5 pt-2.5">
                    <div className="h-3 w-32 rounded bg-white/10 animate-shimmer" />
                    <div className="h-2.5 w-48 rounded bg-white/5 animate-shimmer" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {job && <AgentProcessingTimeline job={job} />}

          {job?.status === "failed" && (
            <div className="mt-4 flex flex-col gap-3">
              <ErrorStateCard message={job.error_message ?? "An unknown error occurred during processing."} compact />
              <Button variant="outline" asChild><Link href="/dashboard">Back to Dashboard</Link></Button>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
