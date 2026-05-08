"use client";

import { motion } from "framer-motion";
import { AlertTriangle, RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils/cn";

interface ErrorStateCardProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
  compact?: boolean;
}

export function ErrorStateCard({ title = "Something went wrong", message, onRetry, className, compact = false }: ErrorStateCardProps) {
  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
      className={cn("flex items-start gap-4 rounded-xl border border-red-500/20 bg-red-500/5 p-4",
        compact && "items-center", className)}>
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-red-500/10 text-red-400">
        <AlertTriangle className="h-4 w-4" />
      </div>
      <div className="flex-1 min-w-0">
        {!compact && <p className="text-sm font-medium text-foreground">{title}</p>}
        <p className={cn("text-xs text-muted-foreground", !compact && "mt-0.5")}>{message}</p>
      </div>
      {onRetry && (
        <Button variant="ghost" size="icon-sm" onClick={onRetry} title="Retry">
          <RefreshCcw className="h-3.5 w-3.5" />
        </Button>
      )}
    </motion.div>
  );
}
