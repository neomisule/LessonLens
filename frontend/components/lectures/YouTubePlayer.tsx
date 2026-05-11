"use client";

import { useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Youtube } from "lucide-react";
import { usePlayerStore } from "@/lib/store/playerStore";
import { cn } from "@/lib/utils/cn";

interface YouTubePlayerProps {
  youtubeId: string;
  className?: string;
}

/**
 * Collapsible YouTube embed that responds to `usePlayerStore.seekTo()`.
 *
 * Uses the YouTube IFrame API postMessage protocol — no extra packages needed.
 * Automatically shows itself when a TimestampButton is clicked.
 */
export function YouTubePlayer({ youtubeId, className }: YouTubePlayerProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const { seekTarget, seekVersion, isPlayerVisible, togglePlayer } = usePlayerStore();
  const prevVersionRef = useRef(0);

  // Seek whenever a new seekTo() is dispatched
  useEffect(() => {
    if (seekTarget === null || seekVersion === prevVersionRef.current) return;
    prevVersionRef.current = seekVersion;

    const win = iframeRef.current?.contentWindow;
    if (!win) return;

    // Seek to timestamp
    win.postMessage(
      JSON.stringify({ event: "command", func: "seekTo", args: [seekTarget, true] }),
      "*",
    );
    // Auto-play after seek so the student immediately sees the context
    win.postMessage(
      JSON.stringify({ event: "command", func: "playVideo", args: [] }),
      "*",
    );
  }, [seekTarget, seekVersion]);

  const origin =
    typeof window !== "undefined" ? encodeURIComponent(window.location.origin) : "";

  return (
    <div className={cn("w-full", className)}>
      <AnimatePresence initial={false}>
        {isPlayerVisible ? (
          <motion.div
            key="player"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
            className="relative overflow-hidden rounded-xl border border-lens-glass-border bg-black"
          >
            <div className="aspect-video w-full">
              <iframe
                ref={iframeRef}
                src={`https://www.youtube.com/embed/${youtubeId}?enablejsapi=1&origin=${origin}&rel=0&modestbranding=1`}
                className="h-full w-full"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                title="Lecture video"
              />
            </div>
            {/* Hide button */}
            <button
              onClick={togglePlayer}
              className="absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full bg-black/70 text-white hover:bg-black/90 transition-colors"
              aria-label="Hide video player"
            >
              <X className="h-3 w-3" />
            </button>
          </motion.div>
        ) : (
          <motion.button
            key="show-btn"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={togglePlayer}
            className="flex items-center gap-2 rounded-lg border border-lens-glass-border bg-white/3 px-3 py-2 text-xs text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
          >
            <Youtube className="h-3.5 w-3.5 text-red-400" />
            Show video — click any timestamp to jump
          </motion.button>
        )}
      </AnimatePresence>
    </div>
  );
}
