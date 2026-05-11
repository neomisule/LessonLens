/**
 * Zustand store for the per-lecture YouTube player.
 *
 * TimestampButton calls `seekTo(seconds)` → the YouTubePlayer component
 * watches `seekTarget + seekVersion` and issues a postMessage seek.
 */
import { create } from "zustand";

interface PlayerState {
  /** Seconds to seek to (set by TimestampButton). */
  seekTarget: number | null;
  /**
   * Monotonically-increasing counter so re-seeking to the same timestamp
   * still fires the effect (0 === no seek yet).
   */
  seekVersion: number;
  /** Whether the video panel is currently visible. */
  isPlayerVisible: boolean;

  seekTo: (seconds: number) => void;
  togglePlayer: () => void;
  showPlayer: () => void;
  hidePlayer: () => void;
}

export const usePlayerStore = create<PlayerState>()((set) => ({
  seekTarget: null,
  seekVersion: 0,
  isPlayerVisible: false,

  seekTo: (seconds) =>
    set((s) => ({
      seekTarget: seconds,
      seekVersion: s.seekVersion + 1,
      isPlayerVisible: true, // auto-reveal the player on any seek
    })),

  togglePlayer: () => set((s) => ({ isPlayerVisible: !s.isPlayerVisible })),
  showPlayer: () => set({ isPlayerVisible: true }),
  hidePlayer: () => set({ isPlayerVisible: false }),
}));
