import { apiClient } from "./client";
import type {
  FlashcardList,
  QuizList,
  MasteryRecord,
  ConfidenceUpdateResult,
  OralExamQuestion,
  OralExamFeedback,
  RevisionPlan,
  ReviseSummary,
  Confidence,
} from "@/lib/types/revise";

const BASE = "/api/v1/revise";

export const reviseApi = {
  // ── Flashcards ────────────────────────────────────────────────────────────
  getFlashcards: (
    lectureId: string,
    params?: { question_type?: string; difficulty?: string; concept_id?: string }
  ) => {
    const qs = new URLSearchParams();
    if (params?.question_type) qs.set("question_type", params.question_type);
    if (params?.difficulty)    qs.set("difficulty",    params.difficulty);
    if (params?.concept_id)    qs.set("concept_id",    params.concept_id);
    const q = qs.toString();
    return apiClient.get<FlashcardList>(`${BASE}/${lectureId}/flashcards${q ? `?${q}` : ""}`);
  },

  // ── Quiz ──────────────────────────────────────────────────────────────────
  getQuizQuestions: (
    lectureId: string,
    params?: { question_type?: string; concept_id?: string; shuffle?: boolean }
  ) => {
    const qs = new URLSearchParams();
    if (params?.question_type) qs.set("question_type", params.question_type);
    if (params?.concept_id)    qs.set("concept_id",    params.concept_id);
    if (params?.shuffle === false) qs.set("shuffle", "false");
    const q = qs.toString();
    return apiClient.get<QuizList>(`${BASE}/${lectureId}/quiz${q ? `?${q}` : ""}`);
  },

  // ── Mastery ───────────────────────────────────────────────────────────────
  getMastery: (lectureId: string) =>
    apiClient.get<MasteryRecord[]>(`${BASE}/${lectureId}/mastery`),

  updateConfidence: (flashcard_id: string, confidence: Confidence) =>
    apiClient.post<ConfidenceUpdateResult>(`${BASE}/confidence`, {
      flashcard_id,
      confidence,
    }),

  // ── Oral Exam ─────────────────────────────────────────────────────────────
  getOralQuestion: (lectureId: string, conceptId: string) =>
    apiClient.get<OralExamQuestion>(`${BASE}/${lectureId}/oral/${conceptId}`),

  evaluateOralAnswer: (payload: {
    concept_id: string;
    question_text: string;
    student_answer: string;
  }) => apiClient.post<OralExamFeedback>(`${BASE}/oral/evaluate`, payload),

  // ── Revision Plan ─────────────────────────────────────────────────────────
  getRevisionPlan: (lectureId: string) =>
    apiClient.get<RevisionPlan>(`${BASE}/${lectureId}/plan`),

  // ── Summary ───────────────────────────────────────────────────────────────
  getSummary: (lectureId: string) =>
    apiClient.get<ReviseSummary>(`${BASE}/${lectureId}/summary`),
};
