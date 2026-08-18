import axios from "axios";
import { ElMessage } from "element-plus";

const client = axios.create({
  baseURL: "/api/v1",
  timeout: 180000,
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("bstar_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (error) => {
    const detail = error.response?.data?.detail;
    const message = typeof detail === "string" ? detail : error.message || "请求失败";
    if (error.response?.status === 401) {
      localStorage.removeItem("bstar_token");
      if (!location.pathname.startsWith("/login")) {
        location.href = "/login";
      }
    } else {
      ElMessage.error(message);
    }
    return Promise.reject(error);
  },
);

export default client;
