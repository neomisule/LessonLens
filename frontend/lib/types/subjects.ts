export interface Subject {
  id: string;
  name: string;
  description: string | null;
  color: string;
  icon: string | null;
  lecture_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateSubjectPayload {
  name: string;
  description?: string;
  color?: string;
  icon?: string;
}

export interface UpdateSubjectPayload {
  name?: string;
  description?: string;
  color?: string;
  icon?: string;
}
