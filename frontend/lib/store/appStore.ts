import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { LectureMode } from "@/lib/types/lectures";

interface AppState {
  activeSubjectId: string | null;
  activeLectureId: string | null;
  activeLectureMode: LectureMode;
  sidebarCollapsed: boolean;

  setActiveSubject: (id: string | null) => void;
  setActiveLecture: (id: string | null) => void;
  setLectureMode: (mode: LectureMode) => void;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      activeSubjectId: null,
      activeLectureId: null,
      activeLectureMode: "learn",
      sidebarCollapsed: false,

      setActiveSubject: (id) => set({ activeSubjectId: id }),
      setActiveLecture: (id) => set({ activeLectureId: id }),
      setLectureMode: (mode) => set({ activeLectureMode: mode }),
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
    }),
    { name: "lecturelens-app" }
  )
);
