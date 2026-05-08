// ─── Mind Map (per-lecture) ───────────────────────────────────────────────────

export interface MindMapNode {
  id: string;
  lecture_id: string;
  concept_id: string | null;
  label: string;
  description: string | null;
  node_type: "root" | "branch" | "leaf" | "lecture";
  position_x: number;
  position_y: number;
  color: string | null;
  importance: string;
  exam_likelihood: number;
  timestamp_start: number | null;
}

export interface MindMapEdge {
  id: string;
  lecture_id: string;
  source_node_id: string;
  target_node_id: string;
  label: string | null;
  edge_type: string;
}

export interface MindMap {
  nodes: MindMapNode[];
  edges: MindMapEdge[];
}

// ─── Subject Graph ────────────────────────────────────────────────────────────

export interface GraphNode {
  id: string;
  kind: "lecture" | "concept";
  label: string;
  importance: string;
  is_recurring: boolean;
  is_prerequisite: boolean;
  avg_mastery: number;
  exam_likelihood: number;
  lecture_id: string | null;
  timestamp_start: number | null;
  color: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  kind: "belongs_to" | "prerequisite" | "recurring" | "related";
  label: string | null;
}

export interface SubjectGraph {
  subject_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  lecture_count: number;
  concept_count: number;
  recurring_count: number;
  weak_topic_count: number;
}

// ─── Subject intelligence ─────────────────────────────────────────────────────

export interface RecurringConcept {
  id: string;
  name: string;
  frequency: number;
  lecture_ids: string[];
  avg_exam_likelihood: number;
  avg_mastery: number;
  importance: string;
}

export interface SubjectConceptRead {
  id: string;
  name: string;
  cluster_label: string;
  frequency: number;
  is_recurring: boolean;
  is_prerequisite: boolean;
  importance: string;
  avg_exam_likelihood: number;
  avg_mastery: number;
  lecture_ids: string[];
}

export interface PrerequisiteChainNode {
  concept_name: string;
  lecture_id: string;
  lecture_title: string;
  timestamp_start: number | null;
  is_mastered: boolean;
}

export interface PrerequisiteChain {
  concept_name: string;
  chain: PrerequisiteChainNode[];
}
