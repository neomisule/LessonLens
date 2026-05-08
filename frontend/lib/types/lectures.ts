export type ProcessingStatus =
  | "queued"
  | "downloading"
  | "transcribing"
  | "segmenting"
  | "extracting_concepts"
  | "generating_flashcards"
  | "generating_summary"
  | "building_mindmap"
  | "completed"
  | "failed";

export type LectureMode = "learn" | "break_it_down" | "revise" | "search" | "mind_map";

export interface Lecture {
  id: string;
  subject_id: string;
  youtube_url: string;
  youtube_id: string;              // updated from youtube_video_id → youtube_id
  title: string | null;
  description: string | null;
  thumbnail_url: string | null;
  duration_seconds: number | null;
  channel_name: string | null;
  processing_status: ProcessingStatus;
  processing_error: string | null;
  processed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AddLecturePayload {
  subject_id: string;
  youtube_url: string;
}

export interface ProcessingJob {
  id: string;
  lecture_id: string;
  status: ProcessingStatus;
  current_step: string | null;
  steps_completed: string[];
  steps_total: number;
  error_message: string | null;
  progress_metadata: Record<string, unknown> | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface ProcessingStep {
  key: ProcessingStatus;
  label: string;
  description: string;
}

export const PROCESSING_STEPS: ProcessingStep[] = [
  { key: "downloading",          label: "Fetching Lecture",     description: "Retrieving video metadata from YouTube" },
  { key: "transcribing",         label: "Transcribing Audio",   description: "Converting speech to text with timestamps" },
  { key: "segmenting",           label: "Segmenting Content",   description: "Splitting transcript into semantic chunks" },
  { key: "extracting_concepts",  label: "Extracting Concepts",  description: "Identifying key ideas and terminology" },
  { key: "generating_flashcards",label: "Building Flashcards",  description: "Creating active recall cards" },
  { key: "generating_summary",   label: "Writing Summary",      description: "Composing structured lecture notes" },
  { key: "building_mindmap",     label: "Building Mind Map",    description: "Mapping concept relationships" },
];
