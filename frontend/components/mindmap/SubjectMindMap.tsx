"use client";

import { useQuery } from "@tanstack/react-query";
import { contentApi } from "@/lib/api/content";
import { motion } from "framer-motion";
import { GitBranch } from "lucide-react";

interface SubjectMindMapProps { lectureId: string; }

export function SubjectMindMap({ lectureId }: SubjectMindMapProps) {
  const { data: mindMap, isLoading } = useQuery({
    queryKey: ["mindmap", lectureId],
    queryFn: () => contentApi.getMindMap(lectureId),
  });

  if (isLoading) return <div className="h-80 rounded-xl bg-white/5 animate-shimmer" />;

  if (!mindMap || mindMap.nodes.length === 0) return (
    <div className="flex h-80 flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-lens-glass-border text-muted-foreground">
      <GitBranch className="h-10 w-10 opacity-30" />
      <p className="text-sm">Mind map will appear after processing.</p>
    </div>
  );

  return (
    <div className="relative h-80 w-full overflow-hidden rounded-xl border border-lens-glass-border bg-black/20">
      <svg className="h-full w-full" viewBox="0 0 800 400">
        {mindMap.edges.map((edge) => {
          const src = mindMap.nodes.find((n) => n.id === edge.source_node_id);
          const tgt = mindMap.nodes.find((n) => n.id === edge.target_node_id);
          if (!src || !tgt) return null;
          return (
            <line key={edge.id} x1={src.position_x} y1={src.position_y}
              x2={tgt.position_x} y2={tgt.position_y} stroke="rgba(124,58,237,0.3)" strokeWidth={1.5} />
          );
        })}
        {mindMap.nodes.map((node, i) => (
          <motion.g key={node.id} initial={{ opacity: 0, scale: 0.6 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.04 }} transform={`translate(${node.position_x}, ${node.position_y})`}>
            <circle r={node.node_type === "root" ? 24 : node.node_type === "branch" ? 16 : 10}
              fill={node.color ?? "#7C3AED"} opacity={0.8} />
            <text textAnchor="middle" dy="0.35em" className="fill-white" fontSize={node.node_type === "root" ? 9 : 7}>
              {node.label.length > 14 ? node.label.slice(0, 14) + "…" : node.label}
            </text>
          </motion.g>
        ))}
      </svg>
    </div>
  );
}
