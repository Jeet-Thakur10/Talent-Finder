import { useState, useEffect, useCallback } from "react";
import { notificationService } from "../services/notification.service";
import type { Notification } from "../types/notification.types";

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNotifications = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await notificationService.listNotifications();
      setNotifications(data);
    } catch (err: any) {
      setError(err.message || "Failed to load notifications");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const markAsRead = async (id: string) => {
    try {
      const updated = await notificationService.markAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? updated : n))
      );
      window.dispatchEvent(new Event("unread-notifications-changed"));
    } catch (err: any) {
      console.error("Failed to mark notification as read:", err);
    }
  };

  const markAllAsRead = async () => {
    try {
      await notificationService.markAllAsRead();
      setNotifications((prev) =>
        prev.map((n) => ({ ...n, is_read: true }))
      );
      window.dispatchEvent(new Event("unread-notifications-changed"));
    } catch (err: any) {
      console.error("Failed to mark all as read:", err);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  return {
    notifications,
    isLoading,
    error,
    refetch: fetchNotifications,
    markAsRead,
    markAllAsRead,
  };
}
