"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils/cn";

interface WhyThisMattersCardProps {
  conceptName: string;
  whyItMatters: string;
  className?: string;
}

export function WhyThisMattersCard({
  conceptName,
  whyItMatters,
  className,
}: WhyThisMattersCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      layout
      className={cn(
        "rounded-lg border border-lens-purple/25 bg-lens-purple/8 overflow-hidden",
        className,
      )}
    >
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left"
      >
        <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-lens-purple/20 text-lens-purple-light">
          <Sparkles className="h-3 w-3" />
        </div>
        <span className="flex-1 text-xs font-medium text-lens-purple-light">
          Why this matters
        </span>
        <ChevronDown
          className={cn(
            "h-3.5 w-3.5 text-lens-purple-light/60 transition-transform",
            expanded && "rotate-180",
          )}
        />
      </button>

      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="overflow-hidden"
          >
            <p className="px-3 pb-3 text-xs leading-relaxed text-lens-purple-light/80">
              {whyItMatters}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
