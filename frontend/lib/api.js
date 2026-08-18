import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8080/api/v1";

export const api = axios.create({ baseURL: API_BASE_URL });

// --- Token saqlash --------------------------------------------------------
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
  localStorage.removeItem("user");
}

// --- Keshlangan profil (sahifa yangilanganda rolni darhol bilish uchun) ---
export function getCachedUser() {
  if (typeof window === "undefined") return null;
  try {
    return JSON.parse(localStorage.getItem("user") || "null");
  } catch {
    return null;
  }
}

export function setCachedUser(user) {
  if (typeof window === "undefined") return;
  if (user) localStorage.setItem("user", JSON.stringify(user));
}

api.interceptors.request.use((config) => {
  const { access } = getTokens();
  if (access) config.headers.Authorization = `Bearer ${access}`;
  return config;
});

// --- Refresh rotation: 401 bo'lsa bitta marta yangilashga urinadi ---------
let refreshPromise = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && original && !original._retry) {
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

/** Backend RFC7807 yoki {detail: ...} qaytaradi — ikkalasini ham o'qiydi. */
export function errorMessage(err, fallback = "Xatolik yuz berdi") {
  const data = err?.response?.data;
  if (!data) return err?.message || fallback;
  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  if (data.title) return data.title;
  const firstField = Object.values(data).find((v) => Array.isArray(v) && v.length);
  if (firstField) return firstField[0];
  return fallback;
}

// --- Endpointlar ----------------------------------------------------------

export const authApi = {
  login: (identifier, password) => api.post("/auth/login/", { identifier, password }),
  register: (payload) => api.post("/auth/register/", payload),
  logout: (refresh) => api.post("/auth/logout/", { refresh }),
  me: () => api.get("/me/profile/"),
};

export const groupsApi = {
  open: () => api.get("/groups/open/"),
  my: () => api.get("/groups/my/"),
};

export const mentorApi = {
  groups: () => api.get("/mentor/groups/"),
  members: (groupId) => api.get(`/mentor/groups/${groupId}/members/`),
  requests: () => api.get("/mentor/requests/"),
  approve: (id) => api.post(`/mentor/requests/${id}/approve/`),
  reject: (id, note) => api.post(`/mentor/requests/${id}/reject/`, { note }),
  // Uy vazifalari
  submissions: (params) => api.get("/mentor/submissions/", { params }),
  setStatus: (id, status) => api.post(`/mentor/submissions/${id}/status/`, { status }),
  grade: (id, payload) => api.post(`/mentor/submissions/${id}/grade/`, payload),
  // O'quvchilar monitoringi
  students: (params) => api.get("/mentor/students/", { params }),
  // Kontent: material va test
  courses: () => api.get("/mentor/courses/"),
  createModule: (courseId, title) => api.post(`/mentor/courses/${courseId}/modules/`, { title }),
  createLesson: (moduleId, payload) => api.post(`/mentor/modules/${moduleId}/lessons/`, payload),
  uploadMaterial: (lessonId, file, isDownloadable = true) => {
    const form = new FormData();
    form.append("file", file);
    form.append("is_downloadable", isDownloadable);
    return api.post(`/mentor/lessons/${lessonId}/material/`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  createQuiz: (lessonId, settings) => api.post(`/mentor/lessons/${lessonId}/quiz/`, settings),
  quizDetail: (quizId) => api.get(`/mentor/quizzes/${quizId}/`),
  updateQuiz: (quizId, settings) => api.put(`/mentor/quizzes/${quizId}/`, settings),
  quizQuestions: (quizId) => api.get(`/mentor/quizzes/${quizId}/questions/`),
  addQuestion: (quizId, payload) => api.post(`/mentor/quizzes/${quizId}/questions/`, payload),
  updateQuestion: (questionId, payload) => api.put(`/mentor/questions/${questionId}/`, payload),
  deleteQuestion: (questionId) => api.delete(`/mentor/questions/${questionId}/`),
  transfer: (studentId, fromGroupId, toGroupId) =>
    api.post("/mentor/transfer/", {
      student_id: studentId,
      from_group_id: fromGroupId,
      to_group_id: toGroupId,
    }),
  remove: (groupId, studentId) =>
    api.post(`/mentor/groups/${groupId}/students/${studentId}/remove/`),
};

export const managerApi = {
  groups: () => api.get("/manager/groups/"),
  createGroup: (payload) => api.post("/manager/groups/", payload),
  setSchedule: (groupId, slots) => api.put(`/manager/groups/${groupId}/schedule/`, slots),
  assignMentor: (groupId, mentorId) =>
    api.post(`/manager/groups/${groupId}/mentor/`, { mentor_id: mentorId }),
};

export const catalogApi = {
  courses: (params) => api.get("/catalog/courses/", { params }),
  categories: () => api.get("/catalog/categories/"),
};

export const meApi = {
  courses: () => api.get("/me/courses/"),
};
