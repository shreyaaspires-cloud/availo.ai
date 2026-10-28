import { create } from "zustand"

export interface NotificationItem {
  id: string
  type: string
  title: string
  body: string
  booking_id?: string
  is_read: boolean
  created_at: string
}

interface NotificationState {
  notifications: NotificationItem[]
  addNotification: (item: NotificationItem) => void
  markRead: (id: string) => void
  setNotifications: (items: NotificationItem[]) => void
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  addNotification: (item) =>
    set((state) => ({
      notifications: [item, ...state.notifications],
    })),
  markRead: (id) =>
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, is_read: true } : n
      ),
    })),
  setNotifications: (items) => set({ notifications: items }),
}))
