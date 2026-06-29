import { useState, useEffect, useCallback } from "react";
import { notificationService } from "../services/notification.service";

export function useUnreadNotificationCount() {
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const count = await notificationService.getUnreadCount();
      setUnreadCount(count);
    } catch (err) {
      console.error("Failed to fetch unread notification count:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUnreadCount();

    const handleCountChange = () => {
      fetchUnreadCount();
    };

    window.addEventListener("unread-notifications-changed", handleCountChange);
    return () => {
      window.removeEventListener("unread-notifications-changed", handleCountChange);
    };
  }, [fetchUnreadCount]);

  return {
    unreadCount,
    isLoading,
    refetch: fetchUnreadCount,
  };
}
