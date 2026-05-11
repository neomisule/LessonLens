"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Star, Lightbulb, Loader2, Volume2, VolumeX } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TimestampButton } from "@/components/lectures/TimestampButton";
import { ConceptExamBadge } from "@/components/content/ConceptExamBadge";
import { ExplanationStyleSelector } from "@/components/content/ExplanationStyleSelector";
import { LanguageSelector } from "@/components/content/LanguageSelector";
import { AudioPlayer } from "@/components/content/AudioPlayer";
import { cn } from "@/lib/utils/cn";
import { useExplain, useGenerateAudio, useConceptExplanations } from "@/lib/hooks/useBreakdown";
import { breakdownApi } from "@/lib/api/breakdown";
import { DiagramView } from "@/components/content/DiagramView";
import type { DiagramData } from "@/components/content/DiagramView";
import type { Concept } from "@/lib/types/content";
import type { ExplanationStyle, Explanation } from "@/lib/types/breakdown";

const IMPORTANCE_CONFIG = {
  core:         { label: "Core",         icon: Star,       variant: "default"    as const },
  supporting:   { label: "Supporting",   icon: Lightbulb,  variant: "secondary"  as const },
  supplemental: { label: "Supplemental", icon: Lightbulb,  variant: "outline"    as const },
};

// Plain text explanation
function TypedText({ text }: { text: string }) {
  return (
    <motion.p
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="text-sm text-muted-foreground leading-relaxed"
    >
      {text}
    </motion.p>
  );
}

/**
 * Renders either a DiagramView (if content is diagram JSON) or plain TypedText.
 */
function ExplanationContent({ exp }: { exp: Explanation }) {
  if (exp.style === "diagram") {
    try {
      const data = JSON.parse(exp.content) as DiagramData;
      if (Array.isArray(data?.nodes) && data.nodes.length > 0) {
        return <DiagramView data={data} />;
      }
    } catch {
      // Fall through to plain text if JSON parse fails
    }
  }
  return <TypedText text={exp.content} />;
}

interface ConfusionRepairCardProps {
  concept: Concept;
  lectureId: string;
}

export function ConfusionRepairCard({ concept, lectureId }: ConfusionRepairCardProps) {
  const [expanded,     setExpanded]     = useState(false);
  const [selectedStyle, setSelectedStyle] = useState<ExplanationStyle | null>(null);
  const [language,      setLanguage]      = useState("en");
  const [activeExp,     setActiveExp]     = useState<Explanation | null>(null);
  const [loadingAudio,  setLoadingAudio]  = useState(false);
  const [audioUrl,      setAudioUrl]      = useState<string | null>(null);
  const [audioDuration, setAudioDuration] = useState<number | null>(null);

  const config = IMPORTANCE_CONFIG[concept.importance];

  const { data: cachedExplanations = [] } = useConceptExplanations(
    expanded ? concept.id : null,
  );

  const explainMutation  = useExplain(concept.id);
  const audioMutation    = useGenerateAudio();

  // Pick a cached explanation if it matches current style+language
  const matchedCache = cachedExplanations.find(
    (e) => e.style === selectedStyle && e.language === language,
  );

  async function handleStyleSelect(style: ExplanationStyle) {
    setSelectedStyle(style);
    setActiveExp(null);
    setAudioUrl(null);

    // Check cache first
    const cached = cachedExplanations.find(
      (e) => e.style === style && e.language === language,
    );
    if (cached) {
      setActiveExp(cached);
      if (cached.audio_url) {
        setAudioUrl(breakdownApi.audioStreamUrl(cached.id));
        setAudioDuration(cached.audio_duration_ms ?? null);
      }
      return;
    }

    // Generate via API
    const result = await explainMutation.mutateAsync({
      concept_id: concept.id,
      style,
      language,
    });
    setActiveExp(result);
    if (result.audio_url) {
      setAudioUrl(breakdownApi.audioStreamUrl(result.id));
      setAudioDuration(result.audio_duration_ms ?? null);
    }
  }

  async function handleGenerateAudio() {
    if (!activeExp) return;
    setLoadingAudio(true);
    try {
      const result = await audioMutation.mutateAsync({
        explanation_id: activeExp.id,
      });
      if (result.audio_url && !result.error) {
        setAudioUrl(breakdownApi.audioStreamUrl(activeExp.id));
        setAudioDuration(result.duration_ms ?? null);
      }
    } finally {
      setLoadingAudio(false);
    }
  }

  const isLoading = explainMutation.isPending
    ? selectedStyle ?? undefined
    : undefined;

  return (
    <motion.div
      layout
      className="glass-card overflow-hidden"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
    >
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-start gap-3 p-4 text-left"
      >
        <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-lens-purple/15 text-lens-purple-light">
          <config.icon className="h-3.5 w-3.5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="text-sm font-semibold text-foreground">{concept.name}</span>
            <Badge variant={config.variant} className="text-[10px]">{config.label}</Badge>
            {concept.exam_likelihood >= 0.3 && (
              <ConceptExamBadge likelihood={concept.exam_likelihood} showLabel={false} />
            )}
          </div>
          <p className="text-xs text-muted-foreground line-clamp-2">{concept.definition}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {cachedExplanations.length > 0 && (
            <Badge variant="outline" className="text-[10px] text-lens-teal-light border-lens-teal/30">
              {cachedExplanations.length} saved
            </Badge>
          )}
          <ChevronDown className={cn("h-4 w-4 text-muted-foreground transition-transform", expanded && "rotate-180")} />
        </div>
      </button>

      {/* ── Expanded breakdown panel ────────────────────────────────────────── */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22 }}
            className="overflow-hidden"
          >
            <div className="flex flex-col gap-4 border-t border-lens-glass-border px-4 pb-5 pt-4">

              {/* Style selector + language */}
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-medium text-muted-foreground">Explain another way</p>
                  <LanguageSelector
                    value={language}
                    onChange={(lang) => {
                      setLanguage(lang);
                      setActiveExp(null);
                      setAudioUrl(null);
                      setSelectedStyle(null);
                    }}
                    compact
                  />
                </div>
                <ExplanationStyleSelector
                  selected={selectedStyle}
                  onSelect={handleStyleSelect}
                  loading={isLoading ?? null}
                />
              </div>

              {/* Generated explanation */}
              <AnimatePresence mode="wait">
                {explainMutation.isPending && (
                  <motion.div
                    key="loading"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex flex-col gap-2"
                  >
                    {[80, 95, 60].map((w, i) => (
                      <div
                        key={i}
                        className="h-3.5 rounded-md bg-white/6 animate-shimmer"
                        style={{ width: `${w}%`, animationDelay: `${i * 80}ms` }}
                      />
                    ))}
                  </motion.div>
                )}

                {activeExp && !explainMutation.isPending && (
                  <motion.div
                    key={activeExp.id}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="flex flex-col gap-3 rounded-xl border border-lens-glass-border bg-white/3 p-4"
                  >
                    <ExplanationContent exp={activeExp} />

                    {/* Source quote */}
                    {activeExp.source_quote && (
                      <blockquote className="border-l-2 border-lens-teal/40 pl-3 text-[11px] italic text-muted-foreground/70">
                        "{activeExp.source_quote}"
                      </blockquote>
                    )}

                    {/* Footer: timestamp + audio controls */}
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-2">
                        {activeExp.timestamp_start != null && (
                          <TimestampButton
                            seconds={activeExp.timestamp_start}
                            lectureId={lectureId}
                            className="text-[10px]"
                          />
                        )}
                        {activeExp.cached && (
                          <Badge variant="outline" className="text-[9px] text-lens-teal-light border-lens-teal/30">
                            cached
                          </Badge>
                        )}
                      </div>

                      {/* Audio button */}
                      {audioUrl ? (
                        <div className="flex-1 min-w-0 max-w-xs">
                          <AudioPlayer src={audioUrl} durationMs={audioDuration} />
                        </div>
                      ) : (
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 gap-1.5 text-[11px] border-lens-glass-border"
                          onClick={handleGenerateAudio}
                          disabled={loadingAudio}
                        >
                          {loadingAudio
                            ? <Loader2 className="h-3 w-3 animate-spin" />
                            : <Volume2 className="h-3 w-3" />
                          }
                          {loadingAudio ? "Generating…" : "Listen"}
                        </Button>
                      )}
                    </div>
                  </motion.div>
                )}

                {explainMutation.isError && (
                  <motion.p
                    key="error"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-xs text-red-400"
                  >
                    Failed to generate explanation. Please try again.
                  </motion.p>
                )}
              </AnimatePresence>

              {/* Timestamp + tags row */}
              <div className="flex items-center gap-2 flex-wrap">
                {concept.timestamp_start != null && (
                  <TimestampButton seconds={concept.timestamp_start} lectureId={lectureId} />
                )}
                {concept.tags?.map((tag) => (
                  <Badge key={tag} variant="outline" className="text-[10px]">{tag}</Badge>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
