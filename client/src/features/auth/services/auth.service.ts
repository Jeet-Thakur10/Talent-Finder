import { api } from "../../../lib/api";

import type {
  ForgotPasswordRequest,
  ForgotPasswordResponse,
  LoginRequest,
  LoginResponse,
  LogoutResponse,
  RefreshResponse,
  ResetPasswordRequest,
  ResetPasswordResponse,
  User,
  VerifyOTPRequest,
  VerifyOTPResponse,
  AddUserRequest,
} from "./auth.types";

export const authService = {
  async login(data: LoginRequest): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>(
      "/auth/login",
      data,
    );

    return response.data;
  },

  async me(): Promise<User> {
    const response = await api.get<User>(
      "/auth/me",
    );

    return response.data;
  },

  async logout(): Promise<LogoutResponse> {
    const response = await api.post<LogoutResponse>(
      "/auth/logout",
    );

    return response.data;
  },

  async refresh(): Promise<RefreshResponse> {
    const response = await api.post<RefreshResponse>(
      "/auth/refresh",
    );

    return response.data;
  },

  async forgotPassword(
    data: ForgotPasswordRequest,
  ): Promise<ForgotPasswordResponse> {
    const response =
      await api.post<ForgotPasswordResponse>(
        "/otp/forgot-password",
        data,
      );

    return response.data;
  },

  async verifyOtp(
    data: VerifyOTPRequest,
  ): Promise<VerifyOTPResponse> {
    const response =
      await api.post<VerifyOTPResponse>(
        "/otp/verify",
        data,
      );

    return response.data;
  },

  async resetPassword(
    data: ResetPasswordRequest,
  ): Promise<ResetPasswordResponse> {
    const response =
      await api.post<ResetPasswordResponse>(
        "/auth/reset-password",
        data,
      );

    return response.data;
  },

  async addUser(data: AddUserRequest): Promise<User> {
    const response = await api.post<User>(
      "/auth/users",
      data,
    );

    return response.data;
  },
};