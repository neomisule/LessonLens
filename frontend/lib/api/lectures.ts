import { apiClient } from "./client";
import type { Lecture, AddLecturePayload, ProcessingJob } from "@/lib/types/lectures";
import type { PaginatedResponse } from "@/lib/types/api";

export const lecturesApi = {
  list: (subjectId?: string) => {
    const qs = subjectId ? `?subject_id=${subjectId}` : "";
    return apiClient.get<PaginatedResponse<Lecture>>(`/lectures/${qs}`);
  },
  get: (id: string) => apiClient.get<Lecture>(`/lectures/${id}`),
  add: (payload: AddLecturePayload) => apiClient.post<Lecture>("/lectures/", payload),
  analyze: (id: string) => apiClient.post<ProcessingJob>(`/lectures/${id}/analyze`, {}),
  getJob: (id: string) => apiClient.get<ProcessingJob>(`/processing/${id}`),
  delete: (id: string) => apiClient.delete(`/lectures/${id}`),
};
