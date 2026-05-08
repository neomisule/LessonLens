"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Cache for 5 minutes by default; high-churn hooks override per-query.
        staleTime: 5 * 60 * 1000,
        // Keep unused data in cache for 10 minutes so navigating back is instant.
        gcTime: 10 * 60 * 1000,
        // Retry up to 3 times with exponential backoff (1s, 2s, 4s).
        retry: 3,
        retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 10_000),
        // Don't re-fetch when the tab re-gains focus during dev.
        refetchOnWindowFocus: process.env.NODE_ENV === "production",
      },
      mutations: {
        // Single retry for mutations (idempotent ones only; non-idempotent should
        // override with retry: false in their useMutation call).
        retry: 1,
        retryDelay: 1000,
      },
    },
  });
}

export function QueryProvider({ children }: { children: React.ReactNode }) {
  // useState ensures the QueryClient is only created once per component mount,
  // even in React Strict Mode's double-invoke.
  const [client] = useState(makeQueryClient);

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
