export type TranscriptMethod = "youtube_captions" | "whisper_fallback";

export interface TranscriptQuality {
  method: TranscriptMethod;
  is_fallback: boolean;
  confidence_avg: number;        // 0-1
  confidence_min: number;        // 0-1
  noise_ratio: number;           // 0-1
  coverage_pct: number;          // 0-100
  gap_count: number;
  gap_locations: [number, number][] | null;  // [[start, end], ...]
  word_count: number;
  segment_count: number;
  total_duration: number;
  created_at: string;
}

export interface TranscriptSegment {
  id: string;
  lecture_id: string;
  sequence_index: number;
  content: string;
  timestamp_start: number;
  timestamp_end: number;
  source: TranscriptMethod;
  confidence: number | null;
}

/** Subset of progress_metadata[key] stored on ProcessingJob for transcription step */
export interface TranscriptProgressDetail {
  segment_count?: number;
  word_count?: number;
  coverage_pct?: number;
  confidence_avg?: number;
  gap_count?: number;
  is_fallback?: boolean;
  method?: TranscriptMethod;
  title?: string;
  channel?: string;
}
