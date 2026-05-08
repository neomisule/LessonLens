"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  GitBranch, RotateCcw, AlertTriangle, BookOpen, Flame, ArrowRight
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { useLectureMindMap, useSubjectGraph, useRecurringConcepts, useWeakTopics } from "@/lib/hooks/useSearch";
import { MindMapCanvas } from "./MindMapCanvas";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { MindMapNode, GraphNode, GraphEdge } from "@/lib/types/graph";

// ── Props ─────────────────────────────────────────────────────────────────────

interface SubjectMindMapProps {
  lectureId: string;
  subjectId?: string;
}

// ── Convert subject graph nodes/edges to MindMap format for canvas ────────────

function subjectToMindMap(
  nodes: GraphNode[],
  edges: GraphEdge[],
): { nodes: MindMapNode[]; edges: any[] } {
  // Assign positions radially: lectures in outer ring, concepts in inner rings
  const lectures  = nodes.filter((n) => n.kind === "lecture");
  const concepts  = nodes.filter((n) => n.kind === "concept");

  const CX = 400, CY = 300;
  const LEC_R  = 220;
  const CON_R  = 120;

  const posMap: Record<string, { x: number; y: number }> = {};

  // Lecture positions: outer ring
  lectures.forEach((n, i) => {
    const angle = (2 * Math.PI * i / Math.max(lectures.length, 1)) - Math.PI / 2;
    posMap[n.id] = {
      x: CX + LEC_R * Math.cos(angle),
      y: CY + LEC_R * Math.sin(angle),
    };
  });

  // Concept positions: clustered around their first lecture
  const conceptsByLecture: Record<string, GraphNode[]> = {};
  edges
    .filter((e) => e.kind === "belongs_to")
    .forEach((e) => {
      const cid = e.source;  // concept
      const lid = e.target;  // lecture
      conceptsByLecture[lid] = conceptsByLecture[lid] || [];
      const concept = nodes.find((n) => n.id === cid);
      if (concept) conceptsByLecture[lid].push(concept);
    });

  Object.entries(conceptsByLecture).forEach(([lid, cons]) => {
    const lp = posMap[lid];
    if (!lp) return;
    cons.forEach((c, i) => {
      const angle = (2 * Math.PI * i / Math.max(cons.length, 1));
      posMap[c.id] = {
        x: lp.x + CON_R * Math.cos(angle),
        y: lp.y + CON_R * Math.sin(angle),
      };
    });
  });

  // Any remaining concepts without a lecture → near centre
  concepts
    .filter((c) => !posMap[c.id])
    .forEach((c, i) => {
      const angle = (2 * Math.PI * i / Math.max(concepts.length, 1));
      posMap[c.id] = { x: CX + 80 * Math.cos(angle), y: CY + 80 * Math.sin(angle) };
    });

  const mmNodes: MindMapNode[] = nodes.map((n) => {
    const pos = posMap[n.id] ?? { x: CX, y: CY };
    return {
      id: n.id,
      lecture_id: n.lecture_id ?? "",
      concept_id: n.kind === "concept" ? n.id.replace("concept:", "") : null,
      label: n.label,
      description: null,
      node_type: n.kind === "lecture" ? "lecture" : (n.is_recurring ? "branch" : "leaf"),
      position_x: Math.round(pos.x),
      position_y: Math.round(pos.y),
      color: n.color,
      importance: n.importance,
      exam_likelihood: n.exam_likelihood,
      timestamp_start: n.timestamp_start,
    };
  });

  const mmEdges = edges.map((e) => ({
    id: e.id,
    lecture_id: "",
    source_node_id: e.source,
    target_node_id: e.target,
    label: e.label,
    edge_type: e.kind,
  }));

  return { nodes: mmNodes, edges: mmEdges };
}

// ── Recurring concepts panel ──────────────────────────────────────────────────

function RecurringPanel({ subjectId }: { subjectId: string }) {
  const { data, isLoading } = useRecurringConcepts(subjectId);

  if (isLoading) return <div className="h-32 rounded-xl bg-white/5 animate-shimmer" />;
  if (!data?.length) return (
    <p className="text-sm text-muted-foreground text-center py-4">
      No recurring concepts yet — add more lectures.
    </p>
  );

  return (
    <div className="space-y-2">
      {data.slice(0, 8).map((c, i) => (
        <motion.div
          key={c.id}
          initial={{ opacity: 0, x: -4 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.04 }}
          className="flex items-center gap-3 rounded-xl bg-white/5 border border-white/5 px-3 py-2.5"
        >
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{c.name}</p>
            <p className="text-[11px] text-muted-foreground">
              Appears in {c.frequency} lectures
            </p>
          </div>
          <div className="flex flex-col items-end gap-1 shrink-0">
            <Badge variant="outline" className="text-[10px]">
              {Math.round(c.avg_exam_likelihood * 100)}% exam
            </Badge>
            <div
              className={cn(
                "h-1.5 w-16 rounded-full",
                c.avg_mastery >= 0.8 ? "bg-emerald-500" :
                c.avg_mastery >= 0.4 ? "bg-amber-500"  :
                c.avg_mastery >  0.0 ? "bg-red-500"    : "bg-zinc-600"
              )}
              style={{ width: `${Math.max(c.avg_mastery * 64, 4)}px` }}
            />
          </div>
        </motion.div>
      ))}
    </div>
  );
}

// ── Weak topics panel ─────────────────────────────────────────────────────────

function WeakTopicsPanel({ subjectId }: { subjectId: string }) {
  const { data, isLoading } = useWeakTopics(subjectId);

  if (isLoading) return <div className="h-32 rounded-xl bg-white/5 animate-shimmer" />;
  if (!data?.length) return (
    <p className="text-sm text-muted-foreground text-center py-4">
      No weak topics detected — great mastery! 🎉
    </p>
  );

  return (
    <div className="space-y-2">
      {data.slice(0, 8).map((c, i) => (
        <motion.div
          key={c.id}
          initial={{ opacity: 0, x: -4 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.04 }}
          className="flex items-center gap-3 rounded-xl bg-red-500/5 border border-red-500/10 px-3 py-2.5"
        >
          <AlertTriangle className="h-4 w-4 text-red-400 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{c.name}</p>
            <p className="text-[11px] text-muted-foreground">{c.importance}</p>
          </div>
          <div className="flex flex-col items-end gap-1 shrink-0">
            <span className="text-[10px] text-red-400 font-medium">
              {Math.round(c.avg_mastery * 100)}% mastered
            </span>
            <span className="text-[10px] text-muted-foreground">
              {Math.round(c.avg_exam_likelihood * 100)}% exam
            </span>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

type GraphTab = "map" | "recurring" | "weak";

export function SubjectMindMap({ lectureId, subjectId }: SubjectMindMapProps) {
  const [tab, setTab] = useState<GraphTab>("map");
  const [showMastery, setShowMastery] = useState(false);
  const [selectedNode, setSelectedNode] = useState<MindMapNode | null>(null);

  // Per-lecture map (no subjectId needed)
  const { data: lectureMap, isLoading: lectureLoading } = useLectureMindMap(lectureId);

  // Subject graph (requires subjectId)
  const { data: subjectGraph, isLoading: subjectLoading } = useSubjectGraph(subjectId ?? null);

  const hasSubject = Boolean(subjectId);

  // Decide what to show in the canvas
  const canvasData = (() => {
    if (hasSubject && subjectGraph) {
      return subjectToMindMap(subjectGraph.nodes, subjectGraph.edges);
    }
    if (lectureMap) {
      return { nodes: lectureMap.nodes as MindMapNode[], edges: lectureMap.edges };
    }
    return null;
  })();

  const isLoading = hasSubject ? subjectLoading : lectureLoading;

  const TABS: { id: GraphTab; label: string; icon: React.ElementType }[] = [
    { id: "map",       label: "Graph",    icon: GitBranch   },
    { id: "recurring", label: "Recurring", icon: RotateCcw  },
    { id: "weak",      label: "Weak Topics", icon: AlertTriangle },
  ];

  return (
    <div className="flex flex-col gap-4">
      {/* Tabs */}
      {hasSubject && (
        <div className="flex gap-1 rounded-xl bg-white/5 p-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={cn(
                "flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition-all",
                tab === t.id
                  ? "bg-lens-primary/20 text-lens-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/5"
              )}
            >
              <t.icon className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{t.label}</span>
              {t.id === "recurring" && subjectGraph && subjectGraph.recurring_count > 0 && (
                <span className="rounded-full bg-lens-primary/30 px-1.5 py-0.5 text-[10px]">
                  {subjectGraph.recurring_count}
                </span>
              )}
              {t.id === "weak" && subjectGraph && subjectGraph.weak_topic_count > 0 && (
                <span className="rounded-full bg-red-500/30 text-red-300 px-1.5 py-0.5 text-[10px]">
                  {subjectGraph.weak_topic_count}
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      <AnimatePresence mode="wait">
        {tab === "map" && (
          <motion.div
            key="map"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-3"
          >
            {/* Graph stats */}
            {hasSubject && subjectGraph && (
              <div className="flex gap-3 text-xs">
                <div className="glass-card rounded-xl px-3 py-2 flex items-center gap-2">
                  <BookOpen className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-muted-foreground">{subjectGraph.lecture_count} lectures</span>
                </div>
                <div className="glass-card rounded-xl px-3 py-2 flex items-center gap-2">
                  <Flame className="h-3.5 w-3.5 text-amber-400" />
                  <span className="text-muted-foreground">{subjectGraph.concept_count} concepts</span>
                </div>
                <div className="ml-auto glass-card rounded-xl px-3 py-2 flex items-center gap-2">
                  <button
                    onClick={() => setShowMastery((s) => !s)}
                    className={cn(
                      "text-xs font-medium transition-colors",
                      showMastery ? "text-lens-primary" : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    {showMastery ? "Mastery ON" : "Mastery overlay"}
                  </button>
                </div>
              </div>
            )}

            {/* Canvas */}
            {isLoading ? (
              <div className="h-[420px] rounded-xl bg-white/5 animate-shimmer" />
            ) : canvasData && canvasData.nodes.length > 0 ? (
              <MindMapCanvas
                nodes={canvasData.nodes}
                edges={canvasData.edges}
                onNodeClick={setSelectedNode}
                showMasteryOverlay={showMastery}
                className="h-[420px]"
              />
            ) : (
              <div className="flex h-[420px] flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-lens-glass-border text-muted-foreground">
                <GitBranch className="h-10 w-10 opacity-30" />
                <p className="text-sm">Mind map will appear after processing completes.</p>
              </div>
            )}

            {/* Selected node detail */}
            <AnimatePresence>
              {selectedNode && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="glass-card rounded-xl p-4 space-y-2">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-sm font-semibold">{selectedNode.label}</p>
                        <p className="text-[11px] text-muted-foreground">{selectedNode.node_type} · {selectedNode.importance}</p>
                      </div>
                      <button
                        onClick={() => setSelectedNode(null)}
                        className="text-[11px] text-muted-foreground hover:text-foreground"
                      >✕</button>
                    </div>
                    {selectedNode.description && (
                      <p className="text-[12px] text-muted-foreground leading-relaxed">{selectedNode.description}</p>
                    )}
                    <div className="flex items-center gap-3 text-[11px]">
                      <span className="text-muted-foreground">
                        Exam: <span className="text-foreground font-medium">{Math.round(selectedNode.exam_likelihood * 100)}%</span>
                      </span>
                      {selectedNode.timestamp_start !== null && (
                        <span className="font-mono text-lens-primary">
                          {Math.floor((selectedNode.timestamp_start ?? 0) / 60)}:{String(Math.floor((selectedNode.timestamp_start ?? 0) % 60)).padStart(2, "0")}
                        </span>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}

        {tab === "recurring" && subjectId && (
          <motion.div key="recurring" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <p className="text-xs text-muted-foreground mb-3">
              Concepts appearing across multiple lectures — likely exam staples.
            </p>
            <RecurringPanel subjectId={subjectId} />
          </motion.div>
        )}

        {tab === "weak" && subjectId && (
          <motion.div key="weak" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <p className="text-xs text-muted-foreground mb-3">
              Topics with low mastery — prioritise these for revision.
            </p>
            <WeakTopicsPanel subjectId={subjectId} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
