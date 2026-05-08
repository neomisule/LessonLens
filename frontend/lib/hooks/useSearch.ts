"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { searchApi } from "@/lib/api/search";
import type { SearchQuery } from "@/lib/types/search";

// ── Semantic search ───────────────────────────────────────────────────────────

export function useSemanticSearch() {
  const [lastQuery, setLastQuery] = useState<SearchQuery | null>(null);

  const mutation = useMutation({
    mutationFn: (query: SearchQuery) => {
      setLastQuery(query);
      return searchApi.search(query);
    },
  });

  return {
    search: mutation.mutate,
    searchAsync: mutation.mutateAsync,
    data: mutation.data,
    isPending: mutation.isPending,
    lastQuery,
    reset: mutation.reset,
  };
}

// ── Related moments ───────────────────────────────────────────────────────────

export function useRelatedMoments(
  segmentId: string | null,
  sameLectureOnly = false
) {
  return useQuery({
    queryKey: ["related-moments", segmentId, sameLectureOnly],
    queryFn: () => searchApi.relatedMoments(segmentId!, 5, sameLectureOnly),
    enabled: Boolean(segmentId),
    staleTime: 5 * 60 * 1000,
  });
}

// ── Per-lecture mind map ──────────────────────────────────────────────────────

export function useLectureMindMap(lectureId: string) {
  return useQuery({
    queryKey: ["mindmap", lectureId],
    queryFn: () => searchApi.getLectureMindMap(lectureId),
    staleTime: 10 * 60 * 1000,
    enabled: Boolean(lectureId),
  });
}

// ── Subject graph ─────────────────────────────────────────────────────────────

export function useSubjectGraph(subjectId: string | null) {
  return useQuery({
    queryKey: ["subject-graph", subjectId],
    queryFn: () => searchApi.getSubjectGraph(subjectId!),
    enabled: Boolean(subjectId),
    staleTime: 5 * 60 * 1000,
  });
}

// ── Subject intelligence ──────────────────────────────────────────────────────

export function useRecurringConcepts(subjectId: string | null) {
  return useQuery({
    queryKey: ["recurring-concepts", subjectId],
    queryFn: () => searchApi.getRecurringConcepts(subjectId!),
    enabled: Boolean(subjectId),
    staleTime: 5 * 60 * 1000,
  });
}

export function useWeakTopics(subjectId: string | null) {
  return useQuery({
    queryKey: ["weak-topics", subjectId],
    queryFn: () => searchApi.getWeakTopics(subjectId!),
    enabled: Boolean(subjectId),
    staleTime: 5 * 60 * 1000,
  });
}

export function usePrerequisiteChains(subjectId: string | null) {
  return useQuery({
    queryKey: ["prerequisite-chains", subjectId],
    queryFn: () => searchApi.getPrerequisiteChains(subjectId!),
    enabled: Boolean(subjectId),
    staleTime: 5 * 60 * 1000,
  });
}
