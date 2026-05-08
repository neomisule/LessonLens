// ─── Summaries ────────────────────────────────────────────────────────────────

export type SummaryLevel = "brief" | "standard" | "detailed";

export interface Summary {
  id: string;
  lecture_id: string;
  level: SummaryLevel;
  title: string;
  content: string;
  sections: SummarySection[];
  created_at: string;
}

export interface SummarySection {
  heading: string;
  content: string;
  timestamp_start: number | null;
  timestamp_end: number | null;
}

// ─── Concepts ─────────────────────────────────────────────────────────────────

export interface Concept {
  id: string;
  lecture_id: string;
  name: string;
  definition: string;
  explanation: string;
  examples: string[];
  timestamp_start: number | null;
  importance: "core" | "supporting" | "supplemental";
  tags: string[];
}

// ─── Flashcards ───────────────────────────────────────────────────────────────

export type FlashcardDifficulty = "easy" | "medium" | "hard";
export type MasteryLevel = "unseen" | "learning" | "familiar" | "mastered";

export interface Flashcard {
  id: string;
  lecture_id: string;
  concept_id: string | null;
  front: string;
  back: string;
  hint: string | null;
  difficulty: FlashcardDifficulty;
  tags: string[];
}

export interface FlashcardSession {
  flashcard_id: string;
  user_response: "correct" | "incorrect" | "skipped";
  time_taken_ms: number;
}

// ─── Quizzes ──────────────────────────────────────────────────────────────────

export type QuestionType = "multiple_choice" | "true_false" | "short_answer";

export interface QuizQuestion {
  id: string;
  lecture_id: string;
  question_text: string;
  question_type: QuestionType;
  options: string[] | null;
  correct_answer: string;
  explanation: string;
  difficulty: FlashcardDifficulty;
}

// ─── Mastery ──────────────────────────────────────────────────────────────────

export interface UserMastery {
  id: string;
  lecture_id: string;
  concept_id: string | null;
  flashcard_id: string | null;
  mastery_level: MasteryLevel;
  attempts: number;
  correct_count: number;
  last_reviewed_at: string | null;
  next_review_at: string | null;
}

export interface LectureMasteryStats {
  lecture_id: string;
  total_concepts: number;
  mastered_concepts: number;
  familiar_concepts: number;
  learning_concepts: number;
  unseen_concepts: number;
  mastery_percentage: number;
  last_reviewed_at: string | null;
}

// ─── Mind Map ─────────────────────────────────────────────────────────────────

export interface MindMapNode {
  id: string;
  lecture_id: string;
  concept_id: string | null;
  label: string;
  description: string | null;
  node_type: "root" | "branch" | "leaf";
  position_x: number;
  position_y: number;
  color: string | null;
}

export interface MindMapEdge {
  id: string;
  lecture_id: string;
  source_node_id: string;
  target_node_id: string;
  label: string | null;
  edge_type: "hierarchical" | "associative" | "causal";
}

export interface MindMap {
  lecture_id: string;
  nodes: MindMapNode[];
  edges: MindMapEdge[];
}

// ─── Search ───────────────────────────────────────────────────────────────────

export interface SearchResult {
  segment_id: string;
  lecture_id: string;
  content: string;
  timestamp_start: number;
  timestamp_end: number;
  similarity: number;
  highlights: string[];
}

export interface SearchQuery {
  query: string;
  lecture_id?: string;
  subject_id?: string;
  limit?: number;
}
