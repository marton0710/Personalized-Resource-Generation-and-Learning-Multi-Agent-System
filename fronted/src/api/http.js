import axios from "axios";

import router from "../router";
import { clearToken, getToken } from "../utils/auth";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8080/api";

const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

http.interceptors.request.use((config) => {
  const token = getToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

http.interceptors.response.use(
  (response) => response,
  (error) => {
    handleUnauthorized(error.response?.status);

    return Promise.reject(error);
  },
);

export function handleUnauthorized(status) {
  if (status === 401) {
    clearToken();
    router.push({
      name: "login",
    });
  }
}

export function getErrorMessage(error) {
  return error.response?.data?.detail?.message || error.message || "请求失败";
}

export default http;
