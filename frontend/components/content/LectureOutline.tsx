"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, BookOpen, GraduationCap } from "lucide-react";
import { TimestampButton } from "@/components/lectures/TimestampButton";
import { cn } from "@/lib/utils/cn";
import type { Chapter, Summary, Concept } from "@/lib/types/content";

interface OutlineChapterProps {
  chapter: Chapter;
  index: number;
  lectureId: string;
  sections: Summary["sections"];
  concepts: Concept[];
}

function OutlineChapter({
  chapter,
  index,
  lectureId,
  sections,
  concepts,
}: OutlineChapterProps) {
  const [open, setOpen] = useState(index === 0);

  // Sections that fall within this chapter's time range
  const chapterSections = sections.filter((s) => {
    const ts = s.timestamp_start ?? 0;
    const end = chapter.timestamp_end ?? Infinity;
    return ts >= chapter.timestamp_start && ts < end;
  });

  // Concepts belonging to this chapter
  const chapterConcepts = concepts.filter((c) =>
    chapter.concept_names.includes(c.name),
  );

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="rounded-xl border border-lens-glass-border bg-white/3 overflow-hidden"
    >
      {/* Chapter header */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left"
      >
        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-lens-purple/20 text-[10px] font-bold text-lens-purple-light">
          {index + 1}
        </div>
        <div className="flex-1 min-w-0 flex items-center gap-2 flex-wrap">
          <span className="text-sm font-semibold text-foreground">{chapter.title}</span>
          <TimestampButton
            seconds={chapter.timestamp_start}
            lectureId={lectureId}
            className="text-[10px] shrink-0"
          />
        </div>
        <ChevronRight
          className={cn(
            "h-4 w-4 shrink-0 text-muted-foreground transition-transform",
            open && "rotate-90",
          )}
        />
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="overflow-hidden"
          >
            <div className="flex flex-col gap-3 px-4 pb-4 border-t border-lens-glass-border pt-3">
              {chapter.summary && (
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {chapter.summary}
                </p>
              )}

              {/* Sections from this chapter */}
              {chapterSections.length > 0 && (
                <div className="flex flex-col gap-1.5 pl-2 border-l-2 border-lens-teal/20">
                  {chapterSections.map((s, i) => (
                    <div key={i} className="flex items-start gap-2">
                      {s.timestamp_start != null && (
                        <TimestampButton
                          seconds={s.timestamp_start}
                          lectureId={lectureId}
                          className="text-[9px] shrink-0 mt-0.5"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-foreground/80">{s.heading}</p>
                        {s.key_points && s.key_points.length > 0 && (
                          <ul className="mt-1 flex flex-col gap-0.5">
                            {s.key_points.slice(0, 3).map((kp, j) => (
                              <li key={j} className="text-[11px] text-muted-foreground flex gap-1.5">
                                <span className="text-lens-teal-light shrink-0">›</span>
                                {kp}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Concepts */}
              {chapterConcepts.length > 0 && (
                <div>
                  <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide mb-1.5 flex items-center gap-1">
                    <BookOpen className="h-3 w-3" /> Key Concepts
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {chapterConcepts.map((c) => (
                      <div
                        key={c.id}
                        className="inline-flex items-center gap-1 rounded-full border border-lens-glass-border bg-white/5 px-2 py-0.5 text-[10px] text-foreground/70"
                      >
                        {c.exam_likelihood >= 0.55 && (
                          <GraduationCap className="h-3 w-3 text-amber-400" />
                        )}
                        {c.name}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

interface LectureOutlineProps {
  chapters: Chapter[];
  summary: Summary | null;    // standard or detailed summary for section data
  concepts: Concept[];
  lectureId: string;
}

export function LectureOutline({
  chapters,
  summary,
  concepts,
  lectureId,
}: LectureOutlineProps) {
  const sections = summary?.sections ?? [];

  if (chapters.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center rounded-xl border border-dashed border-lens-glass-border text-sm text-muted-foreground">
        Outline not yet generated.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {chapters.map((ch, i) => (
        <OutlineChapter
          key={ch.id}
          chapter={ch}
          index={i}
          lectureId={lectureId}
          sections={sections}
          concepts={concepts}
        />
      ))}
    </div>
  );
}
