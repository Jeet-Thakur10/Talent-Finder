import {
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { useNavigate } from "react-router-dom";

import {subscribeToLogout} from "../services/authEvents";
import { AuthContext } from "./AuthContext";
import type { User } from "../services/auth.types";

import { authService } from "../services/auth.service";

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({
  children,
}: AuthProviderProps) {
  const navigate = useNavigate();
  const [user, setUser] =
    useState<User | null>(null);

  const [isLoading, setIsLoading] =
    useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const currentUser =
          await authService.me();

        setUser(currentUser);
      } catch {
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    void initializeAuth();
  }, []);

const login = (user: User) => {
  setUser(user);
};

const logout = () => {
  setUser(null);
};

  useEffect(() => {
    const unsubscribe =
      subscribeToLogout(() => {
        logout();

        navigate("/login", {
          replace: true,
        });
      });

    return unsubscribe;
  }, [navigate]);

const value = useMemo(
  () => ({
    user,
    isAuthenticated: Boolean(user),
    isLoading,
    login,
    logout,
  }),
  [user, isLoading],
);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}