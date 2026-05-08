"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Globe, ChevronDown, Check } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { useSupportedLanguages } from "@/lib/hooks/useBreakdown";

// Fallback list so the UI renders even without the API call
const FALLBACK_LANGUAGES: Record<string, string> = {
  en: "English", es: "Spanish", fr: "French", de: "German",
  pt: "Portuguese", it: "Italian", ja: "Japanese", zh: "Chinese",
  ko: "Korean", ar: "Arabic", hi: "Hindi",
};

interface LanguageSelectorProps {
  value: string;
  onChange: (code: string) => void;
  className?: string;
  compact?: boolean;
}

export function LanguageSelector({
  value,
  onChange,
  className,
  compact = false,
}: LanguageSelectorProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const { data } = useSupportedLanguages();
  const languages = data?.languages ?? FALLBACK_LANGUAGES;
  const currentLabel = languages[value] ?? "English";

  // Close on outside click
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={ref} className={cn("relative", className)}>
      <button
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "flex items-center gap-1.5 rounded-lg border border-lens-glass-border bg-white/5 text-xs text-muted-foreground transition-all hover:bg-white/8 hover:text-foreground",
          compact ? "px-2 py-1.5" : "px-3 py-2",
        )}
      >
        <Globe className="h-3.5 w-3.5 shrink-0" />
        <span>{compact ? value.toUpperCase() : currentLabel}</span>
        <ChevronDown className={cn("h-3 w-3 transition-transform", open && "rotate-180")} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -4, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.96 }}
            transition={{ duration: 0.12 }}
            className="absolute left-0 top-full z-50 mt-1 max-h-64 w-44 overflow-y-auto rounded-xl border border-lens-glass-border bg-lens-bg shadow-xl"
          >
            {Object.entries(languages).map(([code, name]) => (
              <button
                key={code}
                onClick={() => { onChange(code); setOpen(false); }}
                className={cn(
                  "flex w-full items-center justify-between px-3 py-2 text-xs transition-colors hover:bg-white/8",
                  value === code ? "text-lens-teal-light" : "text-muted-foreground",
                )}
              >
                <span>{name}</span>
                {value === code && <Check className="h-3 w-3" />}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
