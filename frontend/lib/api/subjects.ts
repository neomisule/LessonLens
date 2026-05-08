import { apiClient } from "./client";
import type { Subject, CreateSubjectPayload, UpdateSubjectPayload } from "@/lib/types/subjects";
import type { PaginatedResponse } from "@/lib/types/api";

export const subjectsApi = {
  list: () => apiClient.get<PaginatedResponse<Subject>>("/subjects/"),
  get: (id: string) => apiClient.get<Subject>(`/subjects/${id}`),
  create: (payload: CreateSubjectPayload) => apiClient.post<Subject>("/subjects/", payload),
  update: (id: string, payload: UpdateSubjectPayload) =>
    apiClient.patch<Subject>(`/subjects/${id}`, payload),
  delete: (id: string) => apiClient.delete(`/subjects/${id}`),
};
