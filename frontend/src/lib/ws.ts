import { useNotificationStore } from "@/store/notificationStore"
import toast from "react-hot-toast"

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"

class WebSocketClient {
  private ws: WebSocket | null = null
  private reconnectTimeout: any = null
  private retryDelay = 2000
  private maxRetryDelay = 30000
  private userId: string | null = null
  private token: string | null = null

  connect(userId: string, token: string) {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return
    }
    this.userId = userId
    this.token = token

    const url = `${WS_BASE_URL}/ws/${userId}?token=${encodeURIComponent(token)}`
    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      this.retryDelay = 2000
      // Keep alive ping
      setInterval(() => {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send("ping")
        }
      }, 30000)
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        useNotificationStore.getState().addNotification(data)
        if (data.title) {
          toast(data.title, {
            icon: "🔔",
            duration: 4000,
          })
        }
      } catch {}
    }

    this.ws.onclose = () => {
      this.reconnect()
    }

    this.ws.onerror = () => {
      if (this.ws) {
        this.ws.close()
      }
    }
  }

  private reconnect() {
    if (this.reconnectTimeout) clearTimeout(this.reconnectTimeout)
    if (!this.userId || !this.token) return

    this.reconnectTimeout = setTimeout(() => {
      this.retryDelay = Math.min(this.retryDelay * 1.5, this.maxRetryDelay)
      this.connect(this.userId!, this.token!)
    }, this.retryDelay)
  }

  disconnect() {
    if (this.reconnectTimeout) clearTimeout(this.reconnectTimeout)
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}

export const wsClient = new WebSocketClient()
