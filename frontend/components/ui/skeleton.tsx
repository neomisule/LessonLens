import { cn } from "@/lib/utils/cn";

interface SkeletonProps {
  className?: string;
}

/** Reusable skeleton loader with a smooth moving shimmer. */
export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn("skeleton rounded-md", className)}
      aria-hidden="true"
    />
  );
}

/** A stack of skeleton rows — useful for card/list placeholders. */
export function SkeletonLines({
  lines = 3,
  className,
}: {
  lines?: number;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={cn("h-4", i === lines - 1 && "w-3/4")}
        />
      ))}
    </div>
  );
}

/** Lecture card skeleton that mirrors the real LectureCard shape. */
export function LectureCardSkeleton() {
  return (
    <div className="glass-card p-4 flex flex-col gap-3" aria-hidden="true">
      <Skeleton className="w-full aspect-video" />
      <div className="flex flex-col gap-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-3 w-2/3" />
      </div>
      <Skeleton className="h-2 w-full rounded-full" />
      <Skeleton className="h-8 w-24 rounded-lg" />
    </div>
  );
}

/** Stat tile skeleton. */
export function StatSkeleton() {
  return (
    <div className="glass-card p-4 flex items-center gap-3" aria-hidden="true">
      <Skeleton className="h-5 w-5 rounded-md shrink-0" />
      <div className="flex flex-col gap-1.5">
        <Skeleton className="h-6 w-8 rounded" />
        <Skeleton className="h-3 w-16 rounded" />
      </div>
    </div>
  );
}
