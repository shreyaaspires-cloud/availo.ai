"use client"

import React, { useState } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { Toaster } from "react-hot-toast"
import { useWebSocket } from "@/hooks/useWebSocket"

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            refetchOnWindowFocus: false,
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      <SocketWatcher />
      {children}
      <Toaster position="bottom-right" reverseOrder={false} />
    </QueryClientProvider>
  )
}

function SocketWatcher() {
  useWebSocket()
  return null
}
