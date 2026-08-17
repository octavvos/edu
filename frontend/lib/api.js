import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export const api = axios.create({ baseURL: API_BASE_URL });

// --- Token saqlash (A-02: access 15 daq, refresh 30 kun) -------------------
export function getTokens() {
  if (typeof window === "undefined") return { access: null, refresh: null };
  return {
    access: localStorage.getItem("access_token"),
    refresh: localStorage.getItem("refresh_token"),
  };
}

export function setTokens({ access, refresh }) {
  if (typeof window === "undefined") return;
  if (access) localStorage.setItem("access_token", access);
  if (refresh) localStorage.setItem("refresh_token", refresh);
}

export function clearTokens() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

api.interceptors.request.use((config) => {
  const { access } = getTokens();
  if (access) config.headers.Authorization = `Bearer ${access}`;
  return config;
});

// --- A-03: refresh rotation — 401 bo'lsa bitta marta yangilashga urinadi ---
let refreshPromise = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const { refresh } = getTokens();
      if (!refresh) {
        clearTokens();
        return Promise.reject(error);
      }
      try {
        if (!refreshPromise) {
          refreshPromise = axios
            .post(`${API_BASE_URL}/auth/refresh/`, { refresh })
            .finally(() => {
              refreshPromise = null;
            });
        }
        const { data } = await refreshPromise;
        setTokens(data);
        original.headers.Authorization = `Bearer ${data.access}`;
        return api(original);
      } catch (refreshError) {
        clearTokens();
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  },
);

// --- Yordamchi funksiyalar (TZ 5.6 endpoint guruhlari) ---------------------
export const authApi = {
  sendOtp: (phone) => api.post("/auth/otp/send/", { phone }),
  verifyOtp: (phone, code, deviceId) => api.post("/auth/otp/verify/", { phone, code, device_id: deviceId }),
  registerEmail: (email, password, fullName) =>
    api.post("/auth/register/", { email, password, full_name: fullName }),
  login: (identifier, password, deviceId) =>
    api.post("/auth/login/", { identifier, password, device_id: deviceId }),
  logout: (refresh) => api.post("/auth/logout/", { refresh }),
};

export const catalogApi = {
  categories: () => api.get("/catalog/categories/"),
  searchCourses: (params) => api.get("/catalog/courses/", { params }),
};

export const courseApi = {
  detail: (slug) => api.get(`/courses/${slug}/`),
  preview: (slug) => api.get(`/courses/${slug}/preview/`),
  enroll: (slug) => api.post(`/courses/${slug}/enroll/`),
};

export const meApi = {
  profile: () => api.get("/me/profile/"),
  courses: () => api.get("/me/courses/"),
  certificates: () => api.get("/me/certificates/"),
  payments: () => api.get("/me/payments/"),
};

export const learnApi = {
  lesson: (enrollmentId, lessonId) => api.get(`/learn/${enrollmentId}/lessons/${lessonId}/`),
  playbackToken: (enrollmentId, lessonId) => api.get(`/learn/${enrollmentId}/lessons/${lessonId}/playback-token/`),
  updateProgress: (enrollmentId, lessonId, payload) =>
    api.post(`/learn/${enrollmentId}/lessons/${lessonId}/progress/`, payload),
};

export const paymentApi = {
  checkout: (courseId, promoCode, idempotencyKey) =>
    api.post(
      "/payments/checkout/",
      { course_id: courseId, promo_code: promoCode },
      { headers: { "Idempotency-Key": idempotencyKey } },
    ),
};
