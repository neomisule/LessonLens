// ─── Flashcard ────────────────────────────────────────────────────────────────

export type QuestionType = "surface" | "deep" | "application";
export type Difficulty   = "easy" | "medium" | "hard";
export type Confidence   = "mastered" | "shaky" | "confused" | "not_started";

export interface Flashcard {
  id: string;
  lecture_id: string;
  concept_id: string | null;
  front: string;
  back: string;
  hint: string | null;
  difficulty: Difficulty;
  tags: string[];
  question_type: QuestionType;
  timestamp_start: number | null;
  timestamp_end: number | null;
  time_spent_seconds: number | null;
  exam_likelihood: number;
  evidence_quote: string | null;
}

export interface FlashcardList {
  flashcards: Flashcard[];
  total: number;
}

// ─── Quiz ─────────────────────────────────────────────────────────────────────

export interface QuizQuestion {
  id: string;
  lecture_id: string;
  concept_id: string | null;
  question_text: string;
  question_type: "multiple_choice" | "true_false";
  options: string[] | null;
  correct_answer: string;
  explanation: string;
  difficulty: Difficulty;
  timestamp_start: number | null;
  evidence_quote: string | null;
}

export interface QuizList {
  questions: QuizQuestion[];
  total: number;
}

export interface QuizAnswerResult {
  question_id: string;
  correct: boolean;
  correct_answer: string;
  explanation: string;
  evidence_quote: string | null;
}

// ─── Mastery ──────────────────────────────────────────────────────────────────

export interface MasteryRecord {
  id: string;
  lecture_id: string;
  concept_id: string | null;
  flashcard_id: string | null;
  mastery_level: string;
  confidence: Confidence;
  attempts: number;
  correct_count: number;
  ease_factor: number;
  next_review_interval_days: number;
  last_reviewed_at: string | null;
  next_review_at: string | null;
}

export interface ConfidenceUpdateResult {
  flashcard_id: string;
  confidence: Confidence;
  new_interval_days: number;
  new_ease_factor: number;
  next_review_at: string;
}

// ─── Oral Exam ────────────────────────────────────────────────────────────────

export interface OralExamQuestion {
  concept_id: string;
  concept_name: string;
  question_text: string;
  expected_points: string[];
  timestamp_start: number | null;
}

export interface OralExamFeedback {
  score: number;
  feedback: string;
  strong_points: string[];
  missed_points: string[];
  timestamp_citations: { ts: number; quote: string }[];
  suggested_review_ts: number | null;
}

// ─── Revision Plan ────────────────────────────────────────────────────────────

export interface RevisionEntry {
  concept_id: string | null;
  concept_name: string;
  due_in_days: number;
  reason: string;
  priority: number;
  timestamp_start: number | null;
  exam_likelihood: number;
  confidence: Confidence;
}

export interface RevisionPlan {
  lecture_id: string;
  entries: RevisionEntry[];
  due_today: number;
  due_this_week: number;
}

// ─── Summary ──────────────────────────────────────────────────────────────────

export interface ReviseSummary {
  lecture_id: string;
  flashcard_count: number;
  quiz_count: number;
  mastered_count: number;
  shaky_count: number;
  confused_count: number;
  not_started_count: number;
  overall_progress: number;
}

// ─── UI helpers ───────────────────────────────────────────────────────────────

export const CONFIDENCE_CONFIG: Record<
  Confidence,
  { label: string; color: string; bg: string; emoji: string }
> = {
  mastered:    { label: "Mastered",    color: "text-emerald-400", bg: "bg-emerald-500/15", emoji: "✓" },
  shaky:       { label: "Shaky",       color: "text-amber-400",   bg: "bg-amber-500/15",   emoji: "~" },
  confused:    { label: "Confused",    color: "text-red-400",     bg: "bg-red-500/15",     emoji: "✗" },
  not_started: { label: "Not started", color: "text-zinc-400",    bg: "bg-zinc-500/15",    emoji: "○" },
};

export const QUESTION_TYPE_CONFIG: Record<
  QuestionType,
  { label: string; color: string }
> = {
  surface:     { label: "Recall",      color: "text-blue-400"   },
  deep:        { label: "Understand",  color: "text-purple-400" },
  application: { label: "Apply",       color: "text-rose-400"   },
};
