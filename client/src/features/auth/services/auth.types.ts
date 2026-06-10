export type UserRole = "recruiter" | "hiring_manager";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: User;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ForgotPasswordResponse {
  message: string;
}

export interface VerifyOTPRequest {
  email: string;
  otp: string;
}

export interface VerifyOTPResponse {
  reset_token: string;
}

export interface ResetPasswordRequest {
  reset_token: string;
  new_password: string;
}

export interface ResetPasswordResponse {
  message: string;
}

export interface LogoutResponse {
  message: string;
}

export interface RefreshResponse {
  message: string;
}