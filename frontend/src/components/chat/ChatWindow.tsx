"use client"

import React, { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { useAuth } from "@/hooks/useAuth"
import { Send, MessageSquare } from "lucide-react"

interface ChatWindowProps {
  bookingId: string
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ bookingId }) => {
  const { user } = useAuth()
  const [content, setContent] = useState("")
  const queryClient = useQueryClient()

  const { data: messages = [] } = useQuery<any[]>({
    queryKey: ["chat-messages", bookingId],
    queryFn: () => api.get(`/chat/${bookingId}/messages`),
    refetchInterval: 3000,
  })

  const sendMutation = useMutation({
    mutationFn: (msg: string) => api.post(`/chat/${bookingId}/messages`, { content: msg }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat-messages", bookingId] })
      setContent("")
    },
  })

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault()
    if (!content.trim()) return
    sendMutation.mutate(content)
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden flex flex-col h-[520px] shadow-sm">
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center gap-2">
        <MessageSquare className="w-4 h-4 text-blue-600" />
        <h4 className="text-xs font-bold text-gray-800">Booking Channel</h4>
      </div>

      <div className="flex-1 p-4 overflow-y-auto space-y-3">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-gray-400">
            No messages yet. Send a note to coordinate handover.
          </div>
        ) : (
          messages.map((m) => {
            const isMe = m.sender_id === user?.id
            return (
              <div key={m.id} className={`flex flex-col ${isMe ? "items-end" : "items-start"}`}>
                <div
                  className={`max-w-[80%] rounded-xl px-3 py-2 text-xs ${
                    isMe
                      ? "bg-blue-600 text-white rounded-br-none"
                      : "bg-gray-100 text-gray-800 rounded-bl-none"
                  }`}
                >
                  {m.content}
                </div>
                <span className="text-[10px] text-gray-400 mt-0.5">
                  {new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            )
          })
        )}
      </div>

      <form onSubmit={handleSend} className="p-3 bg-gray-50 border-t border-gray-200 flex gap-2">
        <input
          type="text"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Type message..."
          className="flex-1 bg-white border border-gray-200 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={!content.trim() || sendMutation.isPending}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white p-2 rounded-lg transition"
        >
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  )
}
