import { createContext } from "react";

import type { User } from "../services/auth.types";

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login: (user: User) => void;
  logout: () => Promise<void>;
}

export const AuthContext =
  createContext<AuthContextType | null>(null);