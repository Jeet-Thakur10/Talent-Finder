import { useState, useEffect } from "react";
import { authService } from "../../auth/services/auth.service";
import type { UserRole } from "../../auth/services/auth.types";

export interface AddRecruiterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (message: string) => void;
}

export function AddRecruiterModal({
  isOpen,
  onClose,
  onSuccess,
}: AddRecruiterModalProps) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<UserRole>("recruiter");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Clear fields and errors when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setName("");
      setEmail("");
      setRole("recruiter");
      setPassword("");
      setError(null);
    }
  }, [isOpen]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim() || !email.trim() || !password.trim()) {
      setError("All fields are required");
      return;
    }

    try {
      setIsSubmitting(true);
      await authService.addUser({
        name,
        email,
        role,
        password,
      });
      onSuccess("User created successfully. Welcome email sent!");
      onClose();
    } catch (err: any) {
      const serverMessage = err.response?.data?.detail;
      setError(serverMessage || "An error occurred while creating the recruiter account.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/40 transition-opacity"
        onClick={onClose}
      />

      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="workspace-modal-panel animate-fade-in flex w-full max-w-md flex-col relative z-10">
          {/* Header */}
          <div className="mb-5 pb-3 border-b border-slate-100">
            <h3 className="text-lg font-bold text-slate-900 leading-tight">Add Recruiter</h3>
            <p className="text-xs text-slate-500 mt-1">
              Create a new user account and dispatch a welcome email with credentials.
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="auth-label text-[10px] text-slate-500 font-semibold tracking-wider uppercase block">
                Full Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="John Doe"
                className="auth-input !py-2.5 !rounded-xl text-sm focus:outline-none"
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="auth-label text-[10px] text-slate-500 font-semibold tracking-wider uppercase block">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="john.doe@company.com"
                className="auth-input !py-2.5 !rounded-xl text-sm focus:outline-none"
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="auth-label text-[10px] text-slate-500 font-semibold tracking-wider uppercase block">
                Role
              </label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as UserRole)}
                className="auth-input !py-2.5 !rounded-xl text-sm focus:outline-none bg-white text-slate-900 shadow-sm outline-none transition focus:border-blue-600 focus:bg-white focus:ring-4 focus:ring-blue-100"
                required
              >
                <option value="recruiter">Recruiter</option>
                <option value="hiring_manager">Hiring Manager</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="auth-label text-[10px] text-slate-500 font-semibold tracking-wider uppercase block">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="auth-input !py-2.5 !rounded-xl text-sm focus:outline-none"
                required
              />
            </div>

            {error && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 font-medium">
                {error}
              </div>
            )}

            {/* Footer / Buttons */}
            <div className="workspace-modal-footer shrink-0 pt-4 border-t border-slate-100 mt-5">
              <button
                type="button"
                disabled={isSubmitting}
                onClick={onClose}
                className="workspace-ghost-button !px-4 !py-2 text-xs font-semibold cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="workspace-primary-button !px-5 !py-2 text-xs font-semibold shadow-md shadow-slate-900/10 cursor-pointer"
              >
                {isSubmitting ? "Creating..." : "Create Recruiter"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
