// ─── Search request ───────────────────────────────────────────────────────────

export interface SearchQuery {
  query: string;
  lecture_id?: string;
  subject_id?: string;
  limit?: number;
  include_concepts?: boolean;
}

// ─── Segment result ───────────────────────────────────────────────────────────

export type ConfidenceTier = "high" | "good" | "partial" | "weak";

export interface SearchResult {
  segment_id: string;
  lecture_id: string;
  lecture_title: string;
  content: string;
  similarity: number;
  confidence_tier: ConfidenceTier;
  timestamp_start: number | null;
  timestamp_end: number | null;
  topic_label: string | null;
}

// ─── Concept result ───────────────────────────────────────────────────────────

export interface ConceptSearchResult {
  concept_id: string;
  lecture_id: string;
  lecture_title: string;
  name: string;
  definition: string;
  importance: string;
  exam_likelihood: number;
  similarity: number;
  confidence_tier: ConfidenceTier;
  timestamp_start: number | null;
  evidence_quote: string | null;
}

// ─── Combined response ────────────────────────────────────────────────────────

export interface CombinedSearchResponse {
  query: string;
  segments: SearchResult[];
  concepts: ConceptSearchResult[];
  total_segments: number;
  total_concepts: number;
}

// ─── UI helpers ───────────────────────────────────────────────────────────────

export const CONFIDENCE_TIER_CONFIG: Record<
  ConfidenceTier,
  { label: string; color: string; bg: string }
> = {
  high:    { label: "High",    color: "text-emerald-400", bg: "bg-emerald-500/10" },
  good:    { label: "Good",    color: "text-blue-400",    bg: "bg-blue-500/10"    },
  partial: { label: "Partial", color: "text-amber-400",   bg: "bg-amber-500/10"   },
  weak:    { label: "Weak",    color: "text-zinc-400",    bg: "bg-zinc-500/10"    },
};
