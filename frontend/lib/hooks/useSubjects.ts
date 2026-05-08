"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { subjectsApi } from "@/lib/api/subjects";
import type { CreateSubjectPayload, UpdateSubjectPayload } from "@/lib/types/subjects";

const SUBJECTS_KEY = ["subjects"] as const;

export function useSubjects() {
  return useQuery({
    queryKey: SUBJECTS_KEY,
    queryFn: () => subjectsApi.list(),
  });
}

export function useSubject(id: string) {
  return useQuery({
    queryKey: [...SUBJECTS_KEY, id],
    queryFn: () => subjectsApi.get(id),
    enabled: Boolean(id),
  });
}

export function useCreateSubject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateSubjectPayload) => subjectsApi.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: SUBJECTS_KEY }),
  });
}

export function useUpdateSubject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateSubjectPayload }) =>
      subjectsApi.update(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: SUBJECTS_KEY }),
  });
}

export function useDeleteSubject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => subjectsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: SUBJECTS_KEY }),
  });
}
