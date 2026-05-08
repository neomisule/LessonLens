"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { Play, Pause, Loader2, Volume2 } from "lucide-react";
import { cn } from "@/lib/utils/cn";

interface AudioPlayerProps {
  src: string;
  durationMs?: number | null;
  className?: string;
  onEnded?: () => void;
}

function formatTime(ms: number): string {
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}:${sec.toString().padStart(2, "0")}`;
}

export function AudioPlayer({
  src,
  durationMs,
  className,
  onEnded,
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);    // 0–1
  const [currentMs, setCurrentMs] = useState(0);
  const [totalMs, setTotalMs] = useState(durationMs ?? 0);
  const [error, setError] = useState(false);

  // Update total duration once audio metadata loads
  useEffect(() => {
    const el = audioRef.current;
    if (!el) return;

    const onMeta = () => setTotalMs(el.duration * 1000);
    const onTime = () => {
      setCurrentMs(el.currentTime * 1000);
      setProgress(el.duration ? el.currentTime / el.duration : 0);
    };
    const onEnd = () => {
      setPlaying(false);
      setProgress(0);
      setCurrentMs(0);
      onEnded?.();
    };
    const onError = () => { setError(true); setLoading(false); };

    el.addEventListener("loadedmetadata", onMeta);
    el.addEventListener("timeupdate", onTime);
    el.addEventListener("ended", onEnd);
    el.addEventListener("error", onError);
    return () => {
      el.removeEventListener("loadedmetadata", onMeta);
      el.removeEventListener("timeupdate", onTime);
      el.removeEventListener("ended", onEnd);
      el.removeEventListener("error", onError);
    };
  }, [onEnded]);

  const togglePlay = useCallback(async () => {
    const el = audioRef.current;
    if (!el || error) return;

    if (playing) {
      el.pause();
      setPlaying(false);
    } else {
      setLoading(true);
      try {
        await el.play();
        setPlaying(true);
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    }
  }, [playing, error]);

  const seek = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const el = audioRef.current;
    if (!el || !el.duration) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    el.currentTime = ratio * el.duration;
  }, []);

  if (error) {
    return (
      <div className={cn("flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-xs text-red-400", className)}>
        <Volume2 className="h-3.5 w-3.5 shrink-0" />
        Audio unavailable
      </div>
    );
  }

  return (
    <div className={cn("flex items-center gap-3 rounded-xl border border-lens-glass-border bg-white/5 px-3 py-2", className)}>
      <audio ref={audioRef} src={src} preload="none" />

      {/* Play/Pause button */}
      <button
        onClick={togglePlay}
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-lens-teal/20 text-lens-teal-light transition-all hover:bg-lens-teal/30 active:scale-95"
      >
        {loading
          ? <Loader2 className="h-4 w-4 animate-spin" />
          : playing
          ? <Pause className="h-4 w-4" />
          : <Play className="h-4 w-4 translate-x-0.5" />
        }
      </button>

      {/* Progress bar + time */}
      <div className="flex flex-1 flex-col gap-1 min-w-0">
        <div
          className="relative h-1.5 w-full cursor-pointer rounded-full bg-white/10 overflow-hidden"
          onClick={seek}
        >
          <motion.div
            className="absolute inset-y-0 left-0 rounded-full bg-lens-teal"
            animate={{ width: `${progress * 100}%` }}
            transition={{ duration: 0.1 }}
          />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-muted-foreground tabular-nums">
            {formatTime(currentMs)}
          </span>
          {totalMs > 0 && (
            <span className="text-[10px] text-muted-foreground tabular-nums">
              {formatTime(totalMs)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
