"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import { motion } from "framer-motion";
import { ZoomIn, ZoomOut, Maximize2, RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { Button } from "@/components/ui/button";
import type { MindMapNode, MindMapEdge } from "@/lib/types/graph";

interface MindMapCanvasProps {
  nodes: MindMapNode[];
  edges: MindMapEdge[];
  onNodeClick?: (node: MindMapNode) => void;
  showMasteryOverlay?: boolean;
  className?: string;
}

interface Transform { x: number; y: number; scale: number }

const CANVAS_W = 800;
const CANVAS_H = 600;

const INITIAL_TRANSFORM: Transform = { x: 0, y: 0, scale: 1 };

function nodeRadius(type: string): number {
  if (type === "root")   return 28;
  if (type === "branch") return 18;
  if (type === "lecture") return 22;
  return 10;
}

function masteryColor(examLikelihood: number, type: string): string | undefined {
  if (type === "root" || type === "lecture") return undefined;
  // Blend between concept color and mastery heat
  return undefined; // base color from node.color is used; mastery overlay via opacity
}

export function MindMapCanvas({
  nodes,
  edges,
  onNodeClick,
  showMasteryOverlay = false,
  className,
}: MindMapCanvasProps) {
  const svgRef        = useRef<SVGSVGElement>(null);
  const [tf, setTf]   = useState<Transform>(INITIAL_TRANSFORM);
  const [dragging, setDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0, tx: 0, ty: 0 });
  const [hovered, setHovered] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  // ── Zoom helpers ────────────────────────────────────────────────────────────
  const zoom = useCallback((delta: number) => {
    setTf((t) => ({
      ...t,
      scale: Math.max(0.3, Math.min(3.0, t.scale + delta)),
    }));
  }, []);

  const reset = useCallback(() => setTf(INITIAL_TRANSFORM), []);

  // Fit: compute scale so all nodes are visible
  const fitView = useCallback(() => {
    if (!nodes.length) return;
    const xs = nodes.map((n) => n.position_x);
    const ys = nodes.map((n) => n.position_y);
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    const padX = 60, padY = 60;
    const wScale = CANVAS_W / (maxX - minX + padX * 2);
    const hScale = CANVAS_H / (maxY - minY + padY * 2);
    const scale  = Math.min(wScale, hScale, 1.5);
    const tx = (CANVAS_W - (maxX + minX) * scale) / 2;
    const ty = (CANVAS_H - (maxY + minY) * scale) / 2;
    setTf({ x: tx, y: ty, scale });
  }, [nodes]);

  useEffect(() => { fitView(); }, [fitView]);

  // ── Wheel zoom ──────────────────────────────────────────────────────────────
  useEffect(() => {
    const el = svgRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      zoom(-e.deltaY * 0.001);
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [zoom]);

  // ── Drag pan ────────────────────────────────────────────────────────────────
  const onMouseDown = (e: React.MouseEvent) => {
    if ((e.target as SVGElement).closest("[data-node]")) return; // don't pan on node click
    setDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY, tx: tf.x, ty: tf.y });
  };

  const onMouseMove = (e: React.MouseEvent) => {
    if (!dragging) return;
    setTf((t) => ({
      ...t,
      x: dragStart.tx + (e.clientX - dragStart.x),
      y: dragStart.ty + (e.clientY - dragStart.y),
    }));
  };

  const onMouseUp = () => setDragging(false);

  // ── Node id → node map ──────────────────────────────────────────────────────
  const nodeMap: Record<string, MindMapNode> = {};
  nodes.forEach((n) => { nodeMap[n.id] = n; });

  // ── Render ──────────────────────────────────────────────────────────────────
  const transform = `translate(${tf.x}, ${tf.y}) scale(${tf.scale})`;

  return (
    <div className={cn("relative overflow-hidden rounded-xl border border-lens-glass-border bg-black/20", className)}>
      {/* Controls */}
      <div className="absolute right-3 top-3 z-20 flex flex-col gap-1.5">
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => zoom(0.15)}
          className="bg-black/40 hover:bg-black/60"
        >
          <ZoomIn className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => zoom(-0.15)}
          className="bg-black/40 hover:bg-black/60"
        >
          <ZoomOut className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={fitView}
          className="bg-black/40 hover:bg-black/60"
        >
          <Maximize2 className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={reset}
          className="bg-black/40 hover:bg-black/60"
        >
          <RotateCcw className="h-3.5 w-3.5" />
        </Button>
      </div>

      {/* Zoom level */}
      <div className="absolute left-3 bottom-3 z-20 text-[10px] text-muted-foreground/60 font-mono">
        {Math.round(tf.scale * 100)}%
      </div>

      {/* SVG canvas */}
      <svg
        ref={svgRef}
        className={cn("w-full h-full", dragging ? "cursor-grabbing" : "cursor-grab")}
        viewBox={`0 0 ${CANVAS_W} ${CANVAS_H}`}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
      >
        <defs>
          {/* Glow filter for selected nodes */}
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          {/* Arrow marker for prerequisite edges */}
          <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="rgba(139,92,246,0.5)" />
          </marker>
        </defs>

        <g transform={transform}>
          {/* Edges */}
          {edges.map((edge) => {
            const src = nodeMap[edge.source_node_id];
            const tgt = nodeMap[edge.target_node_id];
            if (!src || !tgt) return null;

            const isPrereq = edge.edge_type === "prerequisite";
            const isCross  = edge.edge_type === "cross_lecture";

            return (
              <line
                key={edge.id}
                x1={src.position_x}
                y1={src.position_y}
                x2={tgt.position_x}
                y2={tgt.position_y}
                stroke={
                  isPrereq ? "rgba(139,92,246,0.5)" :
                  isCross  ? "rgba(16,185,129,0.4)"  :
                  "rgba(255,255,255,0.12)"
                }
                strokeWidth={isPrereq ? 1.5 : 1}
                strokeDasharray={isPrereq ? "4 3" : undefined}
                markerEnd={isPrereq ? "url(#arrow)" : undefined}
              />
            );
          })}

          {/* Nodes */}
          {nodes.map((node, i) => {
            const r          = nodeRadius(node.node_type);
            const isHovered  = hovered === node.id;
            const isSelected = selected === node.id;
            const baseColor  = node.color ?? "#6B7280";
            const opacity    = showMasteryOverlay && node.node_type === "leaf"
              ? 0.4 + node.exam_likelihood * 0.6
              : 0.85;

            return (
              <motion.g
                key={node.id}
                data-node="true"
                initial={{ opacity: 0, scale: 0.4 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.015, type: "spring", stiffness: 200, damping: 15 }}
                transform={`translate(${node.position_x}, ${node.position_y})`}
                style={{ cursor: onNodeClick ? "pointer" : "default" }}
                onMouseEnter={() => setHovered(node.id)}
                onMouseLeave={() => setHovered(null)}
                onClick={() => {
                  setSelected(node.id);
                  onNodeClick?.(node);
                }}
                filter={isSelected ? "url(#glow)" : undefined}
              >
                {/* Outer ring (hover / selected) */}
                {(isHovered || isSelected) && (
                  <circle
                    r={r + 5}
                    fill="none"
                    stroke={baseColor}
                    strokeWidth={1.5}
                    opacity={0.4}
                  />
                )}

                {/* Main circle */}
                <circle
                  r={r}
                  fill={baseColor}
                  opacity={opacity}
                  stroke={isSelected ? "#fff" : "none"}
                  strokeWidth={isSelected ? 1.5 : 0}
                />

                {/* Mastery overlay ring */}
                {showMasteryOverlay && node.exam_likelihood > 0.7 && (
                  <circle
                    r={r + 3}
                    fill="none"
                    stroke="#F59E0B"
                    strokeWidth={2}
                    opacity={0.6}
                    strokeDasharray="3 2"
                  />
                )}

                {/* Label */}
                <text
                  textAnchor="middle"
                  dy={node.node_type === "root" ? "0.35em" : r + 10}
                  fill="white"
                  fontSize={
                    node.node_type === "root" ? 9 :
                    node.node_type === "branch" ? 8 :
                    node.node_type === "lecture" ? 9 : 7
                  }
                  opacity={isHovered ? 1 : 0.85}
                  className="select-none pointer-events-none"
                >
                  {node.label.length > 16
                    ? node.label.slice(0, 16) + "…"
                    : node.label}
                </text>

                {/* Importance dot */}
                {node.node_type === "leaf" && node.importance === "core" && (
                  <circle cx={r - 3} cy={-(r - 3)} r={2.5} fill="#F59E0B" opacity={0.9} />
                )}
              </motion.g>
            );
          })}
        </g>
      </svg>

      {/* Selected node tooltip */}
      {selected && nodeMap[selected] && (
        <motion.div
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute bottom-8 left-3 z-20 max-w-[220px] rounded-xl bg-black/80 border border-white/10 p-3 space-y-1"
        >
          <p className="text-xs font-semibold">{nodeMap[selected].label}</p>
          {nodeMap[selected].description && (
            <p className="text-[11px] text-muted-foreground line-clamp-3">
              {nodeMap[selected].description}
            </p>
          )}
          {nodeMap[selected].timestamp_start !== null && (
            <p className="text-[10px] font-mono text-lens-primary">
              {Math.floor((nodeMap[selected].timestamp_start ?? 0) / 60)}:
              {String(Math.floor((nodeMap[selected].timestamp_start ?? 0) % 60)).padStart(2, "0")}
            </p>
          )}
          <button
            onClick={() => setSelected(null)}
            className="text-[10px] text-muted-foreground hover:text-foreground"
          >
            ✕ close
          </button>
        </motion.div>
      )}

      {/* Legend */}
      <div className="absolute left-3 top-3 z-20 flex flex-col gap-1 text-[9px] text-muted-foreground">
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-[#8B5CF6]" /> Core
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-[#3B82F6]" /> Supporting
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-[#6B7280]" /> Supplemental
        </div>
        {showMasteryOverlay && (
          <div className="flex items-center gap-1.5 mt-1">
            <span className="h-2 w-2 rounded-full border border-[#F59E0B]" /> High exam
          </div>
        )}
      </div>

      {/* Drag hint */}
      {!dragging && (
        <p className="absolute right-3 bottom-3 z-20 text-[9px] text-muted-foreground/40">
          Scroll to zoom · drag to pan · click to inspect
        </p>
      )}
    </div>
  );
}
