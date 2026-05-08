import { apiClient } from "./client";
import type {
  Summary, SummaryLevel, Concept, Flashcard, FlashcardSession,
  QuizQuestion, LectureMasteryStats, MindMap, SearchResult, SearchQuery,
  Chapter, LearnModeData,
} from "@/lib/types/content";

const BASE = "/api/v1/content";

export const contentApi = {
  // ── Learn Mode (aggregate) ───────────────────────────────────────────────
  getLearnMode: (lectureId: string) =>
    apiClient.get<LearnModeData>(`${BASE}/lectures/${lectureId}/learn`),

  // ── Summaries ────────────────────────────────────────────────────────────
  getSummary: (lectureId: string, level: SummaryLevel = "standard") =>
    apiClient.get<Summary>(`${BASE}/lectures/${lectureId}/summary?level=${level}`),

  getAllSummaries: (lectureId: string) =>
    apiClient.get<Summary[]>(`${BASE}/lectures/${lectureId}/summaries`),

  // ── Chapters ─────────────────────────────────────────────────────────────
  getChapters: (lectureId: string) =>
    apiClient.get<Chapter[]>(`${BASE}/lectures/${lectureId}/chapters`),

  // ── Concepts ─────────────────────────────────────────────────────────────
  getConcepts: (lectureId: string) =>
    apiClient.get<Concept[]>(`${BASE}/lectures/${lectureId}/concepts`),

  // ── Flashcards ───────────────────────────────────────────────────────────
  getFlashcards: (lectureId: string) =>
    apiClient.get<Flashcard[]>(`${BASE}/lectures/${lectureId}/flashcards`),

  submitFlashcardSession: (lectureId: string, sessions: FlashcardSession[]) =>
    apiClient.post<void>(`${BASE}/lectures/${lectureId}/flashcards/session`, {
      items: sessions.map((s) => ({
        flashcard_id: s.flashcard_id,
        result: s.user_response,
      })),
    }),

  // ── Quiz ─────────────────────────────────────────────────────────────────
  getQuestions: (lectureId: string) =>
    apiClient.get<QuizQuestion[]>(`${BASE}/lectures/${lectureId}/quiz`),

  // ── Mastery ──────────────────────────────────────────────────────────────
  getMastery: (lectureId: string) =>
    apiClient.get<LectureMasteryStats>(`${BASE}/lectures/${lectureId}/mastery`),

  // ── Mind Map ─────────────────────────────────────────────────────────────
  getMindMap: (lectureId: string) =>
    apiClient.get<MindMap>(`${BASE}/lectures/${lectureId}/mindmap`),

  // ── Search ───────────────────────────────────────────────────────────────
  search: (query: SearchQuery) =>
    apiClient.post<SearchResult[]>(`${BASE}/search/`, query),
};
