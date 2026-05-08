import { apiClient } from "./client";
import type {
  Explanation,
  AudioResult,
  RevisitRecommendation,
  SupportedLanguages,
  ExplainRequest,
  AudioRequest,
} from "@/lib/types/breakdown";

const BASE = "/api/v1/breakdown";

export const breakdownApi = {
  // Supported TTS languages
  getLanguages: () =>
    apiClient.get<SupportedLanguages>(`${BASE}/languages`),

  // Generate (or retrieve cached) explanation
  explain: (payload: ExplainRequest) =>
    apiClient.post<Explanation>(`${BASE}/explain`, payload),

  // List all previously generated explanations for a concept
  listExplanations: (conceptId: string) =>
    apiClient.get<Explanation[]>(`${BASE}/${conceptId}/explanations`),

  // Generate TTS audio for an explanation
  generateAudio: (payload: AudioRequest) =>
    apiClient.post<AudioResult>(`${BASE}/audio`, payload),

  // Revisit recommendations for a lecture
  getRevisit: (lectureId: string, limit = 5) =>
    apiClient.get<RevisitRecommendation[]>(
      `${BASE}/${lectureId}/revisit?limit=${limit}`
    ),

  // Absolute URL for streaming audio (used in <audio src>)
  audioStreamUrl: (explanationId: string) =>
    `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/breakdown/audio/${explanationId}`,
};
