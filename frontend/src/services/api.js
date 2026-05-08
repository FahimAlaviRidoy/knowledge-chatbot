import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach token from localStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const { data } = await axios.post(`${BASE_URL}/auth/refresh`, {
            refresh_token: refresh,
          })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch {
          localStorage.clear()
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

// ─── Auth ─────────────────────────────────────────────────────────────────
export const authApi = {
  login: (username, password) =>
    api.post('/auth/login', { username, password }),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
  refresh: (refresh_token) =>
    api.post('/auth/refresh', { refresh_token }),
}

// ─── Chat ─────────────────────────────────────────────────────────────────
export const chatApi = {
  send: (message, session_id) =>
    api.post('/chat', { message, session_id }),
  clearSession: (session_id) =>
    api.delete(`/chat/session/${session_id}`),
}

// ─── Knowledge Base ───────────────────────────────────────────────────────
export const knowledgeApi = {
  uploadFile: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/knowledge/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  ingestUrl: (url, title) =>
    api.post('/knowledge/ingest-url', { url, title }),
  listDocuments: () => api.get('/knowledge/documents'),
  deleteDocument: (doc_id) => api.delete(`/knowledge/documents/${doc_id}`),
  getStats: () => api.get('/knowledge/stats'),
}

// ─── Admin ────────────────────────────────────────────────────────────────
export const adminApi = {
  listUsers: () => api.get('/admin/users'),
  activeSessions: () => api.get('/admin/sessions/active'),
}

export default api
