import axios from "axios";

export const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
export const WS_BASE = API_BASE.replace(/^http/, "ws");

const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    const status = error?.response?.status;
    const detail = error?.response?.data?.detail || "";
    const tokenExpired = status === 401 && /token|expired/i.test(detail);
    if (tokenExpired) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      if (error.response?.data) error.response.data.detail = "Please Login again";
      if (window.location.pathname !== "/login") {
        window.location.assign("/login");
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  register: (data) => api.post("/auth/register", data),
  login: (email, password) => api.post("/auth/login", { email, password }),
  logout: (refresh_token) => api.post("/auth/logout", { refresh_token }),
  me: () => api.get("/auth/me"),
};

export const adminApi = {
  list: () => api.get("/quizzes"),
  get: (quizId) => api.get(`/quizzes/${quizId}`),
  create: (body) => api.post("/quizzes", body),
  update: (quizId, body) => api.put(`/quizzes/${quizId}`, body),
  remove: (quizId) => api.delete(`/quizzes/${quizId}`),
  start: (quizId) => api.post(`/quizzes/${quizId}/start`),
};

export const quizApi = {
  browse: () => api.get("/play/quizzes"),
  myAttempts: () => api.get("/play/my/attempts"),
  register: (quizId, display_name) =>
    api.post(`/play/quizzes/${quizId}/register`, { display_name }),
  lobby: (quizId) => api.get(`/play/quizzes/${quizId}/lobby`),
  join: (quizId) => api.post(`/play/quizzes/${quizId}/join`),
  state: (quizId) => api.get(`/play/quizzes/${quizId}/state`),
  answer: (quizId, selected_index, time_ms) =>
    api.post(`/play/quizzes/${quizId}/answer`, { selected_index, time_ms }),
  leaderboard: (quizId) => api.get(`/play/quizzes/${quizId}/leaderboard`),
  leaderboardTop: (quizId) => api.get(`/play/quizzes/${quizId}/leaderboard/top`),
  presence: (quizId) => api.get(`/play/quizzes/${quizId}/presence`),
  result: (quizId) => api.get(`/play/quizzes/${quizId}/result`),
};

export default api;
