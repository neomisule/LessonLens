"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Layers, HelpCircle, Mic, Calendar } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { MasteryHeatMap }   from "./MasteryHeatMap";
import { FlashcardDeckV2 }  from "./FlashcardDeckV2";
import { QuizMode }         from "./QuizMode";
import { OralExamMode }     from "./OralExamMode";
import { RevisionPlanCard } from "./RevisionPlanCard";

type ReviseTab = "flashcards" | "quiz" | "oral" | "plan";

const TABS: { id: ReviseTab; label: string; icon: React.ElementType }[] = [
  { id: "flashcards", label: "Flashcards", icon: Layers      },
  { id: "quiz",       label: "Quiz",       icon: HelpCircle  },
  { id: "oral",       label: "Oral Exam",  icon: Mic         },
  { id: "plan",       label: "Plan",       icon: Calendar    },
];

interface ReviseModeProps {
  lectureId: string;
  className?: string;
}

export function ReviseMode({ lectureId, className }: ReviseModeProps) {
  const [activeTab, setActiveTab] = useState<ReviseTab>("flashcards");

  return (
    <div className={cn("flex flex-col gap-5 max-w-2xl mx-auto", className)}>
      {/* Mastery overview */}
      <MasteryHeatMap lectureId={lectureId} />

      {/* Tab bar */}
      <div className="flex gap-1 rounded-xl bg-white/5 p-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition-all",
              activeTab === tab.id
                ? "bg-lens-primary/20 text-lens-primary shadow-sm"
                : "text-muted-foreground hover:text-foreground hover:bg-white/5"
            )}
          >
            <tab.icon className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.18 }}
        >
          {activeTab === "flashcards" && <FlashcardDeckV2 lectureId={lectureId} />}
          {activeTab === "quiz"       && <QuizMode         lectureId={lectureId} />}
          {activeTab === "oral"       && <OralExamMode     lectureId={lectureId} />}
          {activeTab === "plan"       && <RevisionPlanCard  lectureId={lectureId} />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
