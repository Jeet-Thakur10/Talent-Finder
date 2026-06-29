import { useRecruiterTasks } from "./useRecruiterTasks";

export function useLatestJobTask(jobDescriptionId: string | undefined) {
  const { tasks, isLoading, error, isPolling, refetch } = useRecruiterTasks();

  const latestTask = jobDescriptionId
    ? tasks.find((t) => t.job_description_id === jobDescriptionId)
    : undefined;

  return {
    latestTask,
    isLoading,
    error,
    isPolling,
    refetch,
  };
}
