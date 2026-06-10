import { useNavigate } from "react-router-dom";

import { authService } from "../../auth/services/auth.service";
import { useAuth } from "../../auth/hooks/useAuth";

export function DashboardPage() {
  const navigate = useNavigate();

  const {
    user,
    logout,
  } = useAuth();

  const handleLogout = async () => {
    try {
      await authService.logout();
    } catch {
      // Ignore API errors and still clear local auth state.
    } finally {
      logout();

      navigate("/login", {
        replace: true,
      });
    }
  };

  return (
    <div className="min-h-screen p-8">
      <h1 className="mb-4 text-3xl font-bold">
        Dashboard
      </h1>

      <p className="mb-6">
        Welcome {user?.name}
      </p>

      <button
        onClick={handleLogout}
        className="rounded bg-black px-4 py-2 text-white"
      >
        Logout
      </button>
    </div>
  );
}