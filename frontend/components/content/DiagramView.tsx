"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils/cn";

// ── Types ──────────────────────────────────────────────────────────────────────

export interface DiagramNode {
  id: string;
  label: string;
  description?: string;
  /** Row level: 0 = root / top, 1 = children, 2 = grandchildren … */
  level?: number;
}

export interface DiagramEdge {
  from: string;
  to: string;
  label?: string;
}

export interface DiagramData {
  title?: string;
  nodes: DiagramNode[];
  edges: DiagramEdge[];
  /** Optional overall timestamp reference */
  timestamp?: number;
}

// ── Layout constants ───────────────────────────────────────────────────────────

const NODE_W = 140;
const NODE_H = 48;
const H_GAP  = 24;   // horizontal gap between sibling nodes
const V_GAP  = 56;   // vertical gap between levels
const PAD    = 20;   // canvas padding

// ── Layout hook ────────────────────────────────────────────────────────────────

function useLayout(nodes: DiagramNode[], _edges: DiagramEdge[]) {
  return useMemo(() => {
    if (!nodes.length) return { positions: new Map(), svgW: 200, svgH: 100 };

    // Group by explicit level, fall back to 0
    const byLevel = new Map<number, DiagramNode[]>();
    for (const n of nodes) {
      const lvl = n.level ?? 0;
      if (!byLevel.has(lvl)) byLevel.set(lvl, []);
      byLevel.get(lvl)!.push(n);
    }

    const sortedLevels = Array.from(byLevel.keys()).sort((a, b) => a - b);
    const maxPerRow    = Math.max(...Array.from(byLevel.values()).map((l) => l.length));
    const canvasW      = maxPerRow * (NODE_W + H_GAP) - H_GAP;

    const positions = new Map<string, { x: number; y: number }>();

    sortedLevels.forEach((lvl, rowIdx) => {
      const rowNodes = byLevel.get(lvl)!;
      const rowW     = rowNodes.length * (NODE_W + H_GAP) - H_GAP;
      const startX   = (canvasW - rowW) / 2;

      rowNodes.forEach((node, colIdx) => {
        positions.set(node.id, {
          x: startX + colIdx * (NODE_W + H_GAP),
          y: rowIdx * (NODE_H + V_GAP),
        });
      });
    });

    const canvasH = sortedLevels.length * (NODE_H + V_GAP) - V_GAP;

    return {
      positions,
      svgW: canvasW + PAD * 2,
      svgH: canvasH + PAD * 2,
    };
  }, [nodes]);
}

// ── DiagramView ────────────────────────────────────────────────────────────────

interface DiagramViewProps {
  data: DiagramData;
  className?: string;
}

export function DiagramView({ data, className }: DiagramViewProps) {
  const { positions, svgW, svgH } = useLayout(data.nodes, data.edges);

  if (!data.nodes?.length) {
    return (
      <p className="text-xs text-muted-foreground italic">No diagram data available.</p>
    );
  }

  return (
    <div className={cn("overflow-x-auto rounded-xl border border-lens-glass-border bg-white/3 p-4", className)}>
      {data.title && (
        <p className="mb-3 text-center text-xs font-semibold text-foreground/80">{data.title}</p>
      )}

      <svg
        viewBox={`0 0 ${svgW} ${svgH}`}
        width={svgW}
        height={svgH}
        className="mx-auto block"
        style={{ maxWidth: "100%", height: "auto" }}
        aria-label={`Diagram for ${data.title ?? "concept"}`}
      >
        <defs>
          <marker
            id="diag-arrow"
            markerWidth="7"
            markerHeight="7"
            refX="6"
            refY="3.5"
            orient="auto"
          >
            <path d="M0,1 L0,6 L6,3.5 z" fill="rgba(99,102,241,0.65)" />
          </marker>
        </defs>

        {/* ── Edges ─────────────────────────────────────────────────────────── */}
        {(data.edges ?? []).map((edge, i) => {
          const from = positions.get(edge.from);
          const to   = positions.get(edge.to);
          if (!from || !to) return null;

          const x1 = from.x + NODE_W / 2 + PAD;
          const y1 = from.y + NODE_H + PAD;
          const x2 = to.x   + NODE_W / 2 + PAD;
          const y2 = to.y   + PAD;
          const cy = (y1 + y2) / 2;

          return (
            <g key={`edge-${i}`}>
              <path
                d={`M ${x1} ${y1} C ${x1} ${cy}, ${x2} ${cy}, ${x2} ${y2}`}
                fill="none"
                stroke="rgba(99,102,241,0.45)"
                strokeWidth="1.5"
                markerEnd="url(#diag-arrow)"
              />
              {edge.label && (
                <text
                  x={(x1 + x2) / 2}
                  y={cy - 4}
                  textAnchor="middle"
                  fontSize="8.5"
                  fill="rgba(148,163,184,0.8)"
                >
                  {edge.label}
                </text>
              )}
            </g>
          );
        })}

        {/* ── Nodes ─────────────────────────────────────────────────────────── */}
        {data.nodes.map((node) => {
          const pos = positions.get(node.id);
          if (!pos) return null;

          const x      = pos.x + PAD;
          const y      = pos.y + PAD;
          const isRoot = (node.level ?? 0) === 0;
          const hasDesc = Boolean(node.description);
          const labelY  = y + NODE_H / 2 + (hasDesc ? -7 : 0);
          const descY   = y + NODE_H / 2 + 9;

          // Truncate long labels to fit inside node
          const label = node.label.length > 17 ? node.label.slice(0, 15) + "…" : node.label;
          const desc  = node.description
            ? node.description.length > 22
              ? node.description.slice(0, 20) + "…"
              : node.description
            : "";

          return (
            <g key={node.id}>
              <rect
                x={x}
                y={y}
                width={NODE_W}
                height={NODE_H}
                rx="8"
                fill={isRoot ? "rgba(99,102,241,0.22)" : "rgba(255,255,255,0.06)"}
                stroke={isRoot ? "rgba(99,102,241,0.55)" : "rgba(255,255,255,0.13)"}
                strokeWidth="1"
              />
              <text
                x={x + NODE_W / 2}
                y={labelY}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="11"
                fontWeight={isRoot ? "600" : "500"}
                fill="rgba(248,250,252,0.92)"
              >
                {label}
              </text>
              {hasDesc && (
                <text
                  x={x + NODE_W / 2}
                  y={descY}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fontSize="9"
                  fill="rgba(148,163,184,0.72)"
                >
                  {desc}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
