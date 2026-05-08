"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PanelLeftClose, PanelLeft, Menu } from "lucide-react";
import { SubjectSelector } from "@/components/subjects/SubjectSelector";
import { CreateSubjectModal } from "@/components/subjects/CreateSubjectModal";
import { AddLectureUrlForm } from "@/components/lectures/AddLectureUrlForm";
import { LectureSidebar } from "@/components/lectures/LectureSidebar";
import { useAppStore } from "@/lib/store/appStore";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils/cn";

const SIDEBAR_W = 272;

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [createSubjectOpen, setCreateSubjectOpen] = useState(false);
  // Mobile overlay sidebar state (separate from desktop collapse)
  const [mobileOpen, setMobileOpen] = useState(false);

  const { activeSubjectId, sidebarCollapsed, toggleSidebar } = useAppStore();
  const router = useRouter();

  const handleJobStarted = (jobId: string, lectureId: string) => {
    router.push(`/processing/${jobId}?lectureId=${lectureId}`);
  };

  const SidebarContent = () => (
    <>
      {/* Header */}
      <div className="flex h-14 items-center justify-between px-4 border-b border-lens-glass-border shrink-0">
        <Link href="/" className="flex items-center gap-2 group" aria-label="LectureLens home">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-lens-gradient text-white text-xs font-bold shadow-sm group-hover:scale-105 transition-transform">
            L
          </div>
          <span className="text-sm font-semibold tracking-tight">LectureLens</span>
        </Link>
        {/* Desktop close */}
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={toggleSidebar}
          className="hidden lg:flex"
          aria-label="Collapse sidebar"
        >
          <PanelLeftClose className="h-4 w-4" />
        </Button>
        {/* Mobile close */}
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => setMobileOpen(false)}
          className="lg:hidden"
          aria-label="Close menu"
        >
          <PanelLeftClose className="h-4 w-4" />
        </Button>
      </div>

      {/* Body */}
      <div className="flex flex-col gap-6 overflow-y-auto p-4 flex-1">
        <SubjectSelector onCreateNew={() => setCreateSubjectOpen(true)} />
        <AnimatePresence>
          {activeSubjectId && (
            <motion.div
              key={activeSubjectId}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              className="flex flex-col gap-4"
            >
              <AddLectureUrlForm onJobStarted={handleJobStarted} />
              <LectureSidebar subjectId={activeSubjectId} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  );

  return (
    <div className="flex h-screen overflow-hidden">
      {/* ── Desktop sidebar ─────────────────────────────────────────────────── */}
      <AnimatePresence initial={false}>
        {!sidebarCollapsed && (
          <motion.aside
            key="sidebar"
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: SIDEBAR_W, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: [0.4, 0, 0.2, 1] }}
            className="hidden lg:flex flex-col border-r border-lens-glass-border bg-background/60 backdrop-blur-xl overflow-hidden shrink-0"
            aria-label="Sidebar navigation"
          >
            <SidebarContent />
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Desktop collapsed rail */}
      {sidebarCollapsed && (
        <div className="hidden lg:flex flex-col items-center gap-4 border-r border-lens-glass-border p-2 shrink-0">
          <Link href="/" aria-label="LectureLens home">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-lens-gradient text-white text-xs font-bold hover:scale-105 transition-transform">
              L
            </div>
          </Link>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={toggleSidebar}
            aria-label="Expand sidebar"
          >
            <PanelLeft className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* ── Mobile sidebar overlay ──────────────────────────────────────────── */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              key="backdrop"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="lg:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
              onClick={() => setMobileOpen(false)}
            />
            {/* Drawer */}
            <motion.aside
              key="mobile-sidebar"
              initial={{ x: -SIDEBAR_W }}
              animate={{ x: 0 }}
              exit={{ x: -SIDEBAR_W }}
              transition={{ duration: 0.22, ease: [0.4, 0, 0.2, 1] }}
              className="lg:hidden fixed left-0 top-0 z-50 h-full flex flex-col border-r border-lens-glass-border bg-background/95 backdrop-blur-xl overflow-hidden"
              style={{ width: SIDEBAR_W }}
              aria-label="Mobile navigation"
            >
              <SidebarContent />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* ── Main content ────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-hidden flex flex-col min-w-0">
        {/* Mobile top bar */}
        <div className="lg:hidden flex items-center gap-3 h-14 px-4 border-b border-lens-glass-border bg-background/60 backdrop-blur-xl shrink-0">
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setMobileOpen(true)}
            aria-label="Open menu"
          >
            <Menu className="h-4 w-4" />
          </Button>
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-lens-gradient text-white text-[10px] font-bold">
              L
            </div>
            <span className="text-sm font-semibold">LectureLens</span>
          </Link>
        </div>

        <main className={cn("flex-1 overflow-y-auto")} id="main-content">
          {children}
        </main>
      </div>

      <CreateSubjectModal
        open={createSubjectOpen}
        onOpenChange={setCreateSubjectOpen}
      />
    </div>
  );
}
