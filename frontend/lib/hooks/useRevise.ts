"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { reviseApi } from "@/lib/api/revise";
import type { Confidence } from "@/lib/types/revise";

// ── Query keys ────────────────────────────────────────────────────────────────

export const reviseKeys = {
  all:          (lectureId: string)               => ["revise", lectureId] as const,
  flashcards:   (lectureId: string, filters?: object) => ["revise", lectureId, "flashcards", filters] as const,
  quiz:         (lectureId: string)               => ["revise", lectureId, "quiz"] as const,
  mastery:      (lectureId: string)               => ["revise", lectureId, "mastery"] as const,
  oralQuestion: (lectureId: string, conceptId: string) => ["revise", lectureId, "oral", conceptId] as const,
  plan:         (lectureId: string)               => ["revise", lectureId, "plan"] as const,
  summary:      (lectureId: string)               => ["revise", lectureId, "summary"] as const,
};

// ── Flashcards ────────────────────────────────────────────────────────────────

export function useFlashcards(
  lectureId: string,
  filters?: { question_type?: string; difficulty?: string; concept_id?: string }
) {
  return useQuery({
    queryKey: reviseKeys.flashcards(lectureId, filters),
    queryFn: () => reviseApi.getFlashcards(lectureId, filters),
    enabled: Boolean(lectureId),
    staleTime: 5 * 60 * 1000,
  });
}

// ── Quiz ──────────────────────────────────────────────────────────────────────

export function useQuizQuestions(
  lectureId: string,
  params?: { question_type?: string; concept_id?: string }
) {
  return useQuery({
    queryKey: reviseKeys.quiz(lectureId),
    queryFn: () => reviseApi.getQuizQuestions(lectureId, params),
    enabled: Boolean(lectureId),
    staleTime: 5 * 60 * 1000,
  });
}

// ── Mastery ───────────────────────────────────────────────────────────────────

export function useMastery(lectureId: string) {
  return useQuery({
    queryKey: reviseKeys.mastery(lectureId),
    queryFn: () => reviseApi.getMastery(lectureId),
    enabled: Boolean(lectureId),
    staleTime: 30 * 1000,
  });
}

export function useUpdateConfidence(lectureId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      flashcard_id,
      confidence,
    }: {
      flashcard_id: string;
      confidence: Confidence;
    }) => reviseApi.updateConfidence(flashcard_id, confidence),
    onSuccess: () => {
      // Invalidate mastery + summary so progress bar re-renders
      qc.invalidateQueries({ queryKey: reviseKeys.mastery(lectureId) });
      qc.invalidateQueries({ queryKey: reviseKeys.summary(lectureId) });
      qc.invalidateQueries({ queryKey: reviseKeys.plan(lectureId) });
    },
  });
}

// ── Oral Exam ─────────────────────────────────────────────────────────────────

export function useOralQuestion(lectureId: string, conceptId: string) {
  return useQuery({
    queryKey: reviseKeys.oralQuestion(lectureId, conceptId),
    queryFn: () => reviseApi.getOralQuestion(lectureId, conceptId),
    enabled: Boolean(lectureId) && Boolean(conceptId),
    staleTime: 0, // always fresh (random template)
  });
}

export function useEvaluateOralAnswer() {
  return useMutation({
    mutationFn: reviseApi.evaluateOralAnswer,
  });
}

// ── Revision Plan ─────────────────────────────────────────────────────────────

export function useRevisionPlan(lectureId: string) {
  return useQuery({
    queryKey: reviseKeys.plan(lectureId),
    queryFn: () => reviseApi.getRevisionPlan(lectureId),
    enabled: Boolean(lectureId),
    staleTime: 60 * 1000,
  });
}

// ── Summary ───────────────────────────────────────────────────────────────────

export function useReviseSummary(lectureId: string) {
  return useQuery({
    queryKey: reviseKeys.summary(lectureId),
    queryFn: () => reviseApi.getSummary(lectureId),
    enabled: Boolean(lectureId),
    staleTime: 30 * 1000,
  });
}
