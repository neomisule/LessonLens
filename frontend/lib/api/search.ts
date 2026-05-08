import { apiClient } from "./client";
import type {
  SearchQuery,
  CombinedSearchResponse,
  ConceptSearchResult,
  SearchResult,
} from "@/lib/types/search";
import type {
  SubjectGraph,
  MindMap,
  RecurringConcept,
  SubjectConceptRead,
  PrerequisiteChain,
} from "@/lib/types/graph";

const SEARCH_BASE  = "/api/v1/search";
const SUBJECT_BASE = "/api/v1/subjects";
const CONTENT_BASE = "/api/v1/content";

export const searchApi = {
  // ── Semantic search ────────────────────────────────────────────────────────
  search: (payload: SearchQuery) =>
    apiClient.post<CombinedSearchResponse>(`${SEARCH_BASE}/`, payload),

  conceptSearch: (payload: SearchQuery) =>
    apiClient.post<ConceptSearchResult[]>(`${SEARCH_BASE}/concepts/`, payload),

  relatedMoments: (segmentId: string, limit = 5, sameLectureOnly = false) =>
    apiClient.get<SearchResult[]>(
      `${SEARCH_BASE}/related/${segmentId}?limit=${limit}&same_lecture_only=${sameLectureOnly}`
    ),

  // ── Per-lecture mind map ───────────────────────────────────────────────────
  getLectureMindMap: (lectureId: string) =>
    apiClient.get<MindMap>(`${CONTENT_BASE}/lectures/${lectureId}/mindmap`),

  // ── Subject graph ──────────────────────────────────────────────────────────
  getSubjectGraph: (subjectId: string) =>
    apiClient.get<SubjectGraph>(`${SUBJECT_BASE}/${subjectId}/graph`),

  rebuildSubjectGraph: (subjectId: string) =>
    apiClient.post<{ status: string }>(`${SUBJECT_BASE}/${subjectId}/graph/rebuild`, {}),

  // ── Subject intelligence ───────────────────────────────────────────────────
  getRecurringConcepts: (subjectId: string) =>
    apiClient.get<RecurringConcept[]>(`${SUBJECT_BASE}/${subjectId}/recurring`),

  getWeakTopics: (subjectId: string, threshold = 0.3) =>
    apiClient.get<SubjectConceptRead[]>(
      `${SUBJECT_BASE}/${subjectId}/weak-topics?threshold=${threshold}`
    ),

  getPrerequisiteChains: (subjectId: string) =>
    apiClient.get<PrerequisiteChain[]>(`${SUBJECT_BASE}/${subjectId}/prerequisites`),
};
