// ─── Explanation styles ───────────────────────────────────────────────────────

export type ExplanationStyle =
  | "simple"
  | "analogy"
  | "example"
  | "prerequisite"
  | "diagram"
  | "eli5";

export const EXPLANATION_STYLES: {
  id: ExplanationStyle;
  label: string;
  description: string;
  icon: string;
}[] = [
  { id: "simple",       label: "Simpler",     description: "Plain language, no jargon",          icon: "Feather"   },
  { id: "analogy",      label: "Analogy",      description: "Relatable comparison",               icon: "GitCompare" },
  { id: "example",      label: "Example",      description: "Concrete real-world scenario",       icon: "Lightbulb" },
  { id: "prerequisite", label: "Prerequisites",description: "What to know first",                 icon: "BookOpen"  },
  { id: "diagram",      label: "Diagram",      description: "Visual / structural description",    icon: "LayoutTemplate" },
  { id: "eli5",         label: "ELI5",         description: "Like I'm 5 years old",               icon: "Baby"      },
];

// ─── Languages ────────────────────────────────────────────────────────────────

export interface SupportedLanguages {
  languages: Record<string, string>; // { code: name }
}

export const DEFAULT_LANGUAGE = "en";

// ─── Explanation ──────────────────────────────────────────────────────────────

export interface Explanation {
  id: string;
  concept_id: string;
  style: ExplanationStyle;
  language: string;
  content: string;
  source_quote: string | null;
  timestamp_start: number | null;
  audio_url: string | null;
  audio_duration_ms: number | null;
  cached: boolean;
  generated_at: string | null;
}

// ─── Audio ────────────────────────────────────────────────────────────────────

export interface AudioResult {
  explanation_id: string;
  audio_url: string;
  duration_ms: number | null;
  cached: boolean;
  error: string | null;
}

// ─── Revisit recommendations ──────────────────────────────────────────────────

export interface RevisitRecommendation {
  concept_id: string;
  concept_name: string;
  reason: string;
  priority: number;
  timestamp_start: number | null;
  exam_likelihood: number;
  importance: string;
}

// ─── Request payloads ─────────────────────────────────────────────────────────

export interface ExplainRequest {
  concept_id: string;
  style: ExplanationStyle;
  language: string;
}

export interface AudioRequest {
  explanation_id: string;
}
