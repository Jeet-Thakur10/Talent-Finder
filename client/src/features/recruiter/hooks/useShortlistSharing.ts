import { useState, useCallback } from "react";
import { dashboardService } from "../../dashboard/services/dashboard.service";

export function useShortlistSharing(
  jobDescriptionId: string | undefined,
  onSuccess?: () => void
) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [isSharing, setIsSharing] = useState(false);
  const [isShareDialogOpen, setIsShareDialogOpen] = useState(false);
  const [candidateNotes, setCandidateNotes] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  const toggleCandidate = useCallback((candidateId: string) => {
    setSelectedIds((current) => {
      const updated = new Set(current);
      if (updated.has(candidateId)) {
        updated.delete(candidateId);
      } else {
        updated.add(candidateId);
      }
      return updated;
    });
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedIds(new Set());
    setCandidateNotes({});
    setError(null);
  }, []);

  const openShareDialog = useCallback((initialNotes: Record<string, string>) => {
    setCandidateNotes(initialNotes);
    setIsShareDialogOpen(true);
  }, []);

  const closeShareDialog = useCallback(() => {
    setIsShareDialogOpen(false);
    setError(null);
  }, []);

  const updateCandidateNote = useCallback((candidateId: string, note: string) => {
    setCandidateNotes((current) => ({
      ...current,
      [candidateId]: note,
    }));
  }, []);

  const confirmShare = useCallback(async () => {
    if (!jobDescriptionId) return;

    try {
      setIsSharing(true);
      setError(null);

      const candidateIdsList = Array.from(selectedIds);
      
      // Filter out notes for candidates that are not selected anymore
      const filteredNotes: Record<string, string> = {};
      candidateIdsList.forEach((id) => {
        if (candidateNotes[id]) {
          filteredNotes[id] = candidateNotes[id];
        }
      });

      await dashboardService.shareShortlist(jobDescriptionId, {
        candidate_ids: candidateIdsList,
        notes_by_candidate: filteredNotes,
      });

      // Clear selections and close modal on success
      clearSelection();
      closeShareDialog();

      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Failed to share shortlist. Please try again."
      );
    } finally {
      setIsSharing(false);
    }
  }, [jobDescriptionId, selectedIds, candidateNotes, clearSelection, closeShareDialog, onSuccess]);

  return {
    selectedIds,
    isSharing,
    isShareDialogOpen,
    candidateNotes,
    error,
    toggleCandidate,
    clearSelection,
    openShareDialog,
    closeShareDialog,
    updateCandidateNote,
    confirmShare,
  };
}
