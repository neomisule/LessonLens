"use client";

import { Badge } from "@/components/ui/badge";
import { Mic, Captions, AlertCircle } from "lucide-react";
import type { TranscriptMethod } from "@/lib/types/transcript";
import { cn } from "@/lib/utils/cn";

interface TranscriptQualityBadgeProps {
  method: TranscriptMethod;
  confidenceAvg: number;
  coveragePct: number;
  className?: string;
}

export function TranscriptQualityBadge({
  method,
  confidenceAvg,
  coveragePct,
  className,
}: TranscriptQualityBadgeProps) {
  const isWhisper = method === "whisper_fallback";
  const isLowConf = confidenceAvg < 0.65;
  const isLowCov = coveragePct < 70;

  const label = isWhisper ? "AI Transcribed" : "Auto-Captions";
  const Icon = isWhisper ? Mic : Captions;

  const variant =
    isLowConf || isLowCov ? "destructive" : isWhisper ? "accent" : "success";

  return (
    <Badge
      variant={variant}
      className={cn("inline-flex items-center gap-1.5 py-0.5", className)}
    >
      {isLowConf || isLowCov ? (
        <AlertCircle className="h-3 w-3" />
      ) : (
        <Icon className="h-3 w-3" />
      )}
      {label}
    </Badge>
  );
}
