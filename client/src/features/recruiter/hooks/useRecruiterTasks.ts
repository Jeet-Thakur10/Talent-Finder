import { useEffect, useState, useCallback, useRef } from "react";
import { dashboardService } from "../../dashboard/services/dashboard.service";
import type { PipelineTaskStatus } from "../../dashboard/services/dashboard.types";

export function useRecruiterTasks() {
  const [tasks, setTasks] = useState<PipelineTaskStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const pollingIntervalRef = useRef<any | null>(null);

  const fetchTasks = useCallback(async (isAutoRefresh = false) => {
    try {
      if (!isAutoRefresh) {
        setError(null);
      }
      const data = await dashboardService.listRecruiterTasks();
      setTasks(data);
    } catch {
      if (!isAutoRefresh) {
        setError("Failed to load background tasks.");
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Determine if polling is needed (any task is PENDING or RUNNING)
  const hasActiveTasks = tasks.some(
    (t) => t.status === "PENDING" || t.status === "RUNNING"
  );

  // Start polling
  const startPolling = useCallback(() => {
    if (pollingIntervalRef.current) return;
    setIsPolling(true);

    pollingIntervalRef.current = setInterval(() => {
      void fetchTasks(true);
    }, 5000);
  }, [fetchTasks]);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  // Fetch once on mount
  useEffect(() => {
    void fetchTasks();
  }, [fetchTasks]);

  // Polling lifecycle sync
  useEffect(() => {
    if (hasActiveTasks) {
      startPolling();
    } else {
      stopPolling();
    }

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [hasActiveTasks, startPolling, stopPolling]);

  return {
    tasks,
    isLoading,
    error,
    isPolling,
    refetch: () => fetchTasks(false),
  };
}
