"use client";

import { useEffect } from "react";
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

const _TERMINAL = new Set(["complete", "completed", "failed"]);

export function useProcessingJob(jobId: string | null) {
  const qc = useQueryClient();

  // WebSocket for real-time push updates
  useEffect(() => {
    if (!jobId) return;

    const base = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
      .replace(/^http/, "ws");
    const ws = new WebSocket(`${base}/api/v1/jobs/${jobId}/ws`);

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        qc.setQueryData(["processing", jobId], data);
      } catch {}
    };

    ws.onerror = () => ws.close();

    return () => ws.close();
  }, [jobId, qc]);

  // REST fallback: poll every 3 s in case WS is blocked (e.g. Railway free tier)
  return useQuery({
    queryKey: ["processing", jobId],
    queryFn: () => lecturesApi.getJob(jobId!),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (!status || _TERMINAL.has(status)) return false;
      return 3000; // WS is primary; this is just a safety net
    },
  });
}
