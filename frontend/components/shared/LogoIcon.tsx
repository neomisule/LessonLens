"use client";

import { useState } from "react";
import { cn } from "@/lib/utils/cn";

interface LogoIconProps {
  /** Visual size preset */
  size?: "xs" | "sm" | "md" | "lg";
  className?: string;
  /** Apply a continuous spin animation (used on the processing page) */
  spinning?: boolean;
}

const SIZE_MAP: Record<NonNullable<LogoIconProps["size"]>, { px: number; fallback: string }> = {
  xs: { px: 20, fallback: "h-5 w-5 rounded-md text-[9px]" },
  sm: { px: 24, fallback: "h-6 w-6 rounded-md text-[10px]" },
  md: { px: 28, fallback: "h-7 w-7 rounded-lg text-xs" },
  lg: { px: 64, fallback: "h-16 w-16 rounded-2xl text-2xl" },
};

/**
 * Renders `/logo.png` with a gradient "L" fallback.
 * Place the logo at `frontend/public/logo.png` to activate it.
 */
export function LogoIcon({ size = "md", className, spinning }: LogoIconProps) {
  const [failed, setFailed] = useState(false);
  const { px, fallback } = SIZE_MAP[size];

  if (!failed) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src="/logo.png"
        alt="LectureLens logo"
        width={px}
        height={px}
        className={cn(
          "rounded-lg object-contain shrink-0",
          spinning && "animate-spin",
          className,
        )}
        onError={() => setFailed(true)}
      />
    );
  }

  // Fallback gradient "L" div (matches original branding)
  return (
    <div
      aria-label="LectureLens logo"
      className={cn(
        "flex shrink-0 items-center justify-center bg-lens-gradient text-white font-bold shadow-sm",
        fallback,
        spinning && "animate-spin",
        className,
      )}
    >
      L
    </div>
  );
}
