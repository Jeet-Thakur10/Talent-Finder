import axios from "axios";
import type { InternalAxiosRequestConfig } from "axios";

import { ENV } from "../config/env";
import { emitLogout } from "../features/auth/services/authEvents";

interface RetryableRequestConfig
  extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

export const api = axios.create({
  baseURL: ENV.API_BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

interface RetryableRequestConfig {
  _retry?: boolean;
}

api.interceptors.response.use(
  (response) => response,

  async (error) => {
    const originalRequest =
      error.config as RetryableRequestConfig;

    const status = error.response?.status;

    const errorCode =
      error.response?.data?.error_code;

    const isTokenExpired =
      status === 401 &&
      errorCode === "TOKEN_EXPIRED";

    if (
      isTokenExpired &&
      !originalRequest._retry
    ) {
      originalRequest._retry = true;

      try {
        await axios.post(
          `${ENV.API_BASE_URL}/auth/refresh`,
          {},
          {
            withCredentials: true,
          },
        );

        return api(originalRequest);
      } catch {
        emitLogout();

        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  },
);