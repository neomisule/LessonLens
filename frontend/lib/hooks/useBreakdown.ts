"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { breakdownApi } from "@/lib/api/breakdown";
import type { ExplainRequest, AudioRequest } from "@/lib/types/breakdown";

// ── Supported languages ───────────────────────────────────────────────────────

export function useSupportedLanguages() {
  return useQuery({
    queryKey: ["breakdown", "languages"],
    queryFn: breakdownApi.getLanguages,
    staleTime: Infinity,  // languages don't change
  });
}

// ── Explanations list for a concept ──────────────────────────────────────────

export function useConceptExplanations(conceptId: string | null) {
  return useQuery({
    queryKey: ["breakdown", "explanations", conceptId],
    queryFn: () => breakdownApi.listExplanations(conceptId!),
    enabled: Boolean(conceptId),
    staleTime: 30_000,
  });
}

// ── Generate explanation mutation ─────────────────────────────────────────────

export function useExplain(conceptId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ExplainRequest) => breakdownApi.explain(payload),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: ["breakdown", "explanations", conceptId],
      });
    },
  });
}

// ── Generate audio mutation ───────────────────────────────────────────────────

export function useGenerateAudio() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AudioRequest) => breakdownApi.generateAudio(payload),
    onSuccess: (data) => {
      qc.invalidateQueries({
        queryKey: ["breakdown", "explanations"],
      });
    },
  });
}

// ── Revisit recommendations ───────────────────────────────────────────────────

export function useRevisitRecommendations(lectureId: string, limit = 5) {
  return useQuery({
    queryKey: ["breakdown", "revisit", lectureId, limit],
    queryFn: () => breakdownApi.getRevisit(lectureId, limit),
    enabled: Boolean(lectureId),
    staleTime: 5 * 60_000,
  });
}
