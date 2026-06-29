import { api } from "../../../lib/api";
import type { Notification, UnreadCountResponse } from "../types/notification.types";

export const notificationService = {
  async listNotifications(): Promise<Notification[]> {
    const response = await api.get<Notification[]>("/notifications");
    return response.data;
  },

  async markAsRead(notificationId: string): Promise<Notification> {
    const response = await api.patch<Notification>(
      `/notifications/${notificationId}/read`
    );
    return response.data;
  },

  async markAllAsRead(): Promise<{ message: string }> {
    const response = await api.patch<{ message: string }>(
      "/notifications/read-all"
    );
    return response.data;
  },

  async getUnreadCount(): Promise<number> {
    const response = await api.get<UnreadCountResponse>(
      "/notifications/unread-count"
    );
    return response.data.unread_count;
  },
};
