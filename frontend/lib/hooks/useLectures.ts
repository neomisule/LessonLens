"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { lecturesApi } from "@/lib/api/lectures";
import type { AddLecturePayload } from "@/lib/types/lectures";

const LECTURES_KEY = ["lectures"] as const;

export function useLectures(subjectId?: string) {
  return useQuery({
    queryKey: [...LECTURES_KEY, { subjectId }],
    queryFn: () => lecturesApi.list(subjectId),
  });
}

export function useLecture(id: string) {
  return useQuery({
    queryKey: [...LECTURES_KEY, id],
    queryFn: () => lecturesApi.get(id),
    enabled: Boolean(id),
  });
}

export function useAddLecture() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AddLecturePayload) => lecturesApi.add(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: LECTURES_KEY }),
  });
}

export function useAnalyzeLecture() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => lecturesApi.analyze(id),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: [...LECTURES_KEY, id] });
    },
  });
}

export function useProcessingJob(jobId: string | null) {
  return useQuery({
    queryKey: ["processing", jobId],
    queryFn: () => lecturesApi.getJob(jobId!),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (!status || status === "completed" || status === "failed") return false;
      return 2000;
    },
  });
}
