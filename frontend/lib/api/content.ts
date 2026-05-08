import { apiClient } from "./client";
import type {
  Summary, SummaryLevel, Concept, Flashcard, FlashcardSession,
  QuizQuestion, LectureMasteryStats, MindMap, SearchResult, SearchQuery,
} from "@/lib/types/content";

export const contentApi = {
  getSummary: (lectureId: string, level: SummaryLevel = "standard") =>
    apiClient.get<Summary>(`/summaries/?lecture_id=${lectureId}&level=${level}`),
  getConcepts: (lectureId: string) =>
    apiClient.get<Concept[]>(`/concepts/?lecture_id=${lectureId}`),
  getFlashcards: (lectureId: string) =>
    apiClient.get<Flashcard[]>(`/flashcards/?lecture_id=${lectureId}`),
  submitFlashcardSession: (sessions: FlashcardSession[]) =>
    apiClient.post<void>("/flashcards/sessions", sessions),
  getQuestions: (lectureId: string) =>
    apiClient.get<QuizQuestion[]>(`/quizzes/?lecture_id=${lectureId}`),
  getMastery: (lectureId: string) =>
    apiClient.get<LectureMasteryStats>(`/mastery/${lectureId}`),
  getMindMap: (lectureId: string) =>
    apiClient.get<MindMap>(`/mindmap/${lectureId}`),
  search: (query: SearchQuery) =>
    apiClient.post<SearchResult[]>("/search/", query),
};
