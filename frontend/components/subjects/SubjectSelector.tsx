"use client";

import { motion } from "framer-motion";
import { BookOpen, Plus, ChevronRight } from "lucide-react";
import { useSubjects } from "@/lib/hooks/useSubjects";
import { useAppStore } from "@/lib/store/appStore";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Subject } from "@/lib/types/subjects";
import { cn } from "@/lib/utils/cn";

interface SubjectSelectorProps {
  onCreateNew: () => void;
  onSelect?: (subject: Subject) => void;
}

export function SubjectSelector({ onCreateNew, onSelect }: SubjectSelectorProps) {
  const { data, isLoading } = useSubjects();
  const { activeSubjectId, setActiveSubject } = useAppStore();
  const subjects = data?.items ?? [];

  const handleSelect = (subject: Subject) => {
    setActiveSubject(subject.id);
    onSelect?.(subject);
  };

  return (
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
            <div key={i} className="h-10 rounded-lg bg-white/5 animate-shimmer" />
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
            <motion.button
              key={subject.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => handleSelect(subject)}
              className={cn(
                "sidebar-item w-full text-left",
                activeSubjectId === subject.id && "sidebar-item-active"
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
            </motion.button>
          ))}
        </div>
      )}
    </div>
  );
}
