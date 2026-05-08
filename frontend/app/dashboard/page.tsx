"use client";

import { motion } from "framer-motion";
import { BookOpen, Clock, Layers, TrendingUp, Youtube, ArrowRight } from "lucide-react";
import { useSubjects } from "@/lib/hooks/useSubjects";
import { useLectures } from "@/lib/hooks/useLectures";
import { useAppStore } from "@/lib/store/appStore";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MasteryTracker } from "@/components/tracking/MasteryTracker";
import Link from "next/link";
import type { Lecture } from "@/lib/types/lectures";

function LectureCard({ lecture }: { lecture: Lecture }) {
  const { setActiveLecture } = useAppStore();
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-4 flex flex-col gap-3">
      {lecture.thumbnail_url && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={lecture.thumbnail_url} alt={lecture.title ?? "Lecture thumbnail"} className="w-full rounded-lg aspect-video object-cover" />
      )}
      <div>
        <p className="text-sm font-medium text-foreground line-clamp-2">{lecture.title ?? "Untitled Lecture"}</p>
        {lecture.channel_name && <p className="text-xs text-muted-foreground mt-0.5">{lecture.channel_name}</p>}
      </div>
      {lecture.processing_status === "completed" ? (
        <>
          <MasteryTracker lectureId={lecture.id} compact />
          <Button size="sm" variant="outline" onClick={() => setActiveLecture(lecture.id)} asChild>
            <Link href={`/lecture/${lecture.id}`}>Open <ArrowRight className="h-3.5 w-3.5" /></Link>
          </Button>
        </>
      ) : (
        <Badge variant={lecture.processing_status === "failed" ? "destructive" : "default"} className="capitalize w-fit">
          {lecture.processing_status.replace(/_/g, " ")}
        </Badge>
      )}
    </motion.div>
  );
}

export default function DashboardPage() {
  const { data: subjectsData } = useSubjects();
  const { activeSubjectId } = useAppStore();
  const { data: lecturesData } = useLectures(activeSubjectId ?? undefined);

  const subjects = subjectsData?.items ?? [];
  const lectures = lecturesData?.items ?? [];

  if (subjects.length === 0) return (
    <div className="flex h-full flex-col items-center justify-center gap-6 p-12 text-center">
      <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }}
        className="flex h-24 w-24 items-center justify-center rounded-3xl bg-lens-purple/10 text-lens-purple-light">
        <BookOpen className="h-12 w-12" />
      </motion.div>
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="flex flex-col gap-2">
        <h2 className="text-2xl font-bold">Welcome to LectureLens</h2>
        <p className="text-muted-foreground max-w-sm">Create a subject in the sidebar to start organizing your lectures, then paste a YouTube URL to analyze your first lecture.</p>
      </motion.div>
    </div>
  );

  return (
    <div className="flex flex-col gap-8 p-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          { label: "Subjects", value: subjects.length, icon: Layers, color: "text-lens-purple-light" },
          { label: "Lectures", value: lectures.length, icon: Youtube, color: "text-red-400" },
          { label: "Processed", value: lectures.filter((l) => l.processing_status === "completed").length, icon: TrendingUp, color: "text-green-400" },
          { label: "In Progress", value: lectures.filter((l) => !["completed", "failed", "queued"].includes(l.processing_status)).length, icon: Clock, color: "text-amber-400" },
        ].map((stat, i) => (
          <motion.div key={stat.label} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }} className="glass-card p-4 flex items-center gap-3">
            <div className={`${stat.color} opacity-80`}><stat.icon className="h-5 w-5" /></div>
            <div>
              <p className="text-xl font-bold text-foreground">{stat.value}</p>
              <p className="text-xs text-muted-foreground">{stat.label}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {activeSubjectId && (
        <div>
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-muted-foreground">
            {subjects.find((s) => s.id === activeSubjectId)?.name ?? "Lectures"}
          </h2>
          {lectures.length === 0 ? (
            <div className="flex h-40 items-center justify-center rounded-xl border border-dashed border-lens-glass-border text-sm text-muted-foreground">
              No lectures in this subject yet. Paste a YouTube URL to get started.
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {lectures.map((lecture) => <LectureCard key={lecture.id} lecture={lecture} />)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
