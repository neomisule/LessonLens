"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PanelLeftClose, PanelLeft } from "lucide-react";
import { SubjectSelector } from "@/components/subjects/SubjectSelector";
import { CreateSubjectModal } from "@/components/subjects/CreateSubjectModal";
import { AddLectureUrlForm } from "@/components/lectures/AddLectureUrlForm";
import { LectureSidebar } from "@/components/lectures/LectureSidebar";
import { useAppStore } from "@/lib/store/appStore";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [createSubjectOpen, setCreateSubjectOpen] = useState(false);
  const { activeSubjectId, sidebarCollapsed, toggleSidebar } = useAppStore();
  const router = useRouter();

  const handleJobStarted = (jobId: string, lectureId: string) => {
    router.push(`/processing/${jobId}?lectureId=${lectureId}`);
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <AnimatePresence initial={false}>
        {!sidebarCollapsed && (
          <motion.aside
            key="sidebar"
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 272, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="flex flex-col border-r border-lens-glass-border bg-background/60 backdrop-blur-xl overflow-hidden shrink-0"
          >
            <div className="flex h-14 items-center justify-between px-4 border-b border-lens-glass-border">
              <Link href="/" className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-lens-gradient text-white text-xs font-bold">L</div>
                <span className="text-sm font-semibold">LectureLens</span>
              </Link>
              <Button variant="ghost" size="icon-sm" onClick={toggleSidebar}>
                <PanelLeftClose className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex flex-col gap-6 overflow-y-auto p-4">
              <SubjectSelector onCreateNew={() => setCreateSubjectOpen(true)} />
              {activeSubjectId && (
                <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-4">
                  <AddLectureUrlForm onJobStarted={handleJobStarted} />
                  <LectureSidebar subjectId={activeSubjectId} />
                </motion.div>
              )}
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {sidebarCollapsed && (
        <div className="flex flex-col items-center gap-4 border-r border-lens-glass-border p-2 shrink-0">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-lens-gradient text-white text-xs font-bold">L</div>
          <Button variant="ghost" size="icon-sm" onClick={toggleSidebar}><PanelLeft className="h-4 w-4" /></Button>
        </div>
      )}

      <main className="flex-1 overflow-y-auto">{children}</main>
      <CreateSubjectModal open={createSubjectOpen} onOpenChange={setCreateSubjectOpen} />
    </div>
  );
}
