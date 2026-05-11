"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { BookOpen, Plus, ChevronRight, Trash2, AlertTriangle } from "lucide-react";
import { useSubjects, useDeleteSubject } from "@/lib/hooks/useSubjects";
import { useAppStore } from "@/lib/store/appStore";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog, DialogContent, DialogHeader,
  DialogTitle, DialogDescription,
} from "@/components/ui/dialog";
import type { Subject } from "@/lib/types/subjects";
import { cn } from "@/lib/utils/cn";

interface SubjectSelectorProps {
  onCreateNew: () => void;
  onSelect?: (subject: Subject) => void;
}

// ── Delete confirmation dialog ────────────────────────────────────────────────

interface DeleteDialogProps {
  subject: Subject | null;
  onClose: () => void;
}

function DeleteSubjectDialog({ subject, onClose }: DeleteDialogProps) {
  const { activeSubjectId, setActiveSubject } = useAppStore();
  const { mutate: deleteSubject, isPending, error } = useDeleteSubject();

  const handleConfirm = () => {
    if (!subject) return;
    deleteSubject(subject.id, {
      onSuccess: () => {
        if (activeSubjectId === subject.id) setActiveSubject(null);
        onClose();
      },
    });
  };

  return (
    <Dialog open={Boolean(subject)} onOpenChange={(open) => { if (!open) onClose(); }}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-red-400" />
            Delete &ldquo;{subject?.name}&rdquo;?
          </DialogTitle>
          <DialogDescription>
            This will permanently delete this subject and{" "}
            <span className="text-foreground font-medium">
              all its lectures, flashcards, summaries, concepts, and study data
            </span>
            . This cannot be undone.
          </DialogDescription>
        </DialogHeader>

        {error && (
          <p className="rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2 text-xs text-red-400">
            Failed to delete: {String((error as Error).message ?? error)}
          </p>
        )}

        <div className="flex gap-2 justify-end mt-2">
          <Button variant="ghost" size="sm" onClick={onClose} disabled={isPending}>
            Cancel
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleConfirm}
            disabled={isPending}
            className="border-red-500/30 bg-red-500/15 text-red-400 hover:bg-red-500/25 hover:text-red-300"
          >
            {isPending ? "Deleting…" : "Delete subject"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ── SubjectSelector ───────────────────────────────────────────────────────────

export function SubjectSelector({ onCreateNew, onSelect }: SubjectSelectorProps) {
  const { data, isLoading }              = useSubjects();
  const { activeSubjectId, setActiveSubject } = useAppStore();
  const [hoveredId, setHoveredId]        = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget]  = useState<Subject | null>(null);

  const subjects = data ?? [];

  const handleSelect = (subject: Subject) => {
    setActiveSubject(subject.id);
    onSelect?.(subject);
  };

  return (
    <>
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Subjects
          </h3>
          <Button variant="ghost" size="icon-sm" onClick={onCreateNew} title="New subject">
            <Plus className="h-3.5 w-3.5" />
          </Button>
        </div>

        {isLoading ? (
          <div className="flex flex-col gap-2">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-10 rounded-lg bg-white/5 animate-pulse" />
            ))}
          </div>
        ) : subjects.length === 0 ? (
          <motion.button
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            onClick={onCreateNew}
            className="flex items-center gap-3 rounded-lg border border-dashed border-lens-glass-border p-3 text-sm text-muted-foreground hover:text-foreground hover:border-lens-purple/30 hover:bg-lens-purple/5 transition-all"
          >
            <Plus className="h-4 w-4 shrink-0" />
            Create your first subject
          </motion.button>
        ) : (
          <div className="flex flex-col gap-1">
            {subjects.map((subject, i) => (
              <motion.div
                key={subject.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="relative group"
                onMouseEnter={() => setHoveredId(subject.id)}
                onMouseLeave={() => setHoveredId(null)}
              >
                <button
                  onClick={() => handleSelect(subject)}
                  className={cn(
                    "sidebar-item w-full text-left pr-8",
                    activeSubjectId === subject.id && "sidebar-item-active",
                  )}
                >
                  <span
                    className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-base"
                    style={{ backgroundColor: `${subject.color}20` }}
                  >
                    {subject.icon ?? <BookOpen className="h-3.5 w-3.5" />}
                  </span>
                  <span className="flex-1 truncate">{subject.name}</span>
                  {subject.lecture_count > 0 && (
                    <Badge variant="outline" className="text-xs px-1.5 py-0">
                      {subject.lecture_count}
                    </Badge>
                  )}
                  {activeSubjectId === subject.id && (
                    <ChevronRight className="h-3 w-3 shrink-0 text-lens-purple-light" />
                  )}
                </button>

                {/* Delete button — single click → confirmation dialog */}
                {hoveredId === subject.id && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeleteTarget(subject);
                    }}
                    title="Delete subject"
                    className="absolute right-1 top-1/2 -translate-y-1/2 flex h-6 w-6 items-center justify-center rounded text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-all"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                )}
              </motion.div>
            ))}
          </div>
        )}
      </div>

      <DeleteSubjectDialog
        subject={deleteTarget}
        onClose={() => setDeleteTarget(null)}
      />
    </>
  );
}
