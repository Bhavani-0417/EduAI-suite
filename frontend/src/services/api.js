import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Auto-attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-redirect on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// ─── Auth ───────────────────────────────────────────────────────────────────
export const authAPI = {
  login: (data) => api.post('/api/auth/login', data),
  register: (data) => api.post('/api/auth/register', data),
  me: () => api.get('/api/auth/me'),
};

// ─── Academic Dashboard ──────────────────────────────────────────────────────
export const academicAPI = {
  getMarks: () => api.get('/api/academic/marks'),
  addMark: (data) => api.post('/api/academic/marks', data),
  deleteMark: (id) => api.delete(`/api/academic/marks/${id}`),
  getCGPA: () => api.get('/api/academic/cgpa'),
  getWeaknesses: () => api.get('/api/academic/weaknesses'),
  getRoadmap: () => api.get('/api/academic/roadmap'),
  uploadMarksheet: (file) => {
    const fd = new FormData(); fd.append('file', file);
    return api.post('/api/academic/upload-marksheet', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
};

// ─── Knowledge Hub ───────────────────────────────────────────────────────────
export const notesAPI = {
  getNotes: () => api.get('/api/notes'),
  uploadNote: (file, subject, topic) => {
    const fd = new FormData();
    fd.append('file', file); fd.append('subject', subject); fd.append('topic', topic || '');
    return api.post('/api/notes/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
  deleteNote: (id) => api.delete(`/api/notes/${id}`),
  askQuestion: (question, subject) => api.post('/api/notes/ask', { question, subject }),
  summarize: (noteId) => api.post(`/api/notes/${noteId}/summarize`),
};

// ─── Content Generator ───────────────────────────────────────────────────────
export const contentAPI = {
  generatePPT: (data) => api.post('/api/content/generate-ppt', data, { responseType: 'blob' }),
  generateDoc: (data) => api.post('/api/content/generate-doc', data, { responseType: 'blob' }),
  generateLabManual: (data) => api.post('/api/content/generate-lab-manual', data, { responseType: 'blob' }),
  getTemplates: () => api.get('/api/content/templates'),
};

// ─── Career Center ───────────────────────────────────────────────────────────
export const careerAPI = {
  generateResume: (data) => api.post('/api/career/resume/generate', data, { responseType: 'blob' }),
  parseResume: (file) => {
    const fd = new FormData(); fd.append('file', file);
    return api.post('/api/career/resume/parse', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
  matchJD: (data) => api.post('/api/career/resume/match-jd', data),
  getJobs: () => api.get('/api/career/jobs'),
  addJob: (data) => api.post('/api/career/jobs', data),
  updateJob: (id, data) => api.put(`/api/career/jobs/${id}`, data),
  deleteJob: (id) => api.delete(`/api/career/jobs/${id}`),
  getAnalytics: () => api.get('/api/career/analytics'),
};

// ─── Goal & Roadmap ──────────────────────────────────────────────────────────
export const roadmapAPI = {
  generateRoadmap: (data) => api.post('/api/roadmap/generate', data),
  getRoadmaps: () => api.get('/api/roadmap'),
  markComplete: (id, topicId) => api.put(`/api/roadmap/${id}/topic/${topicId}/complete`),
};

// ─── Chatbot ─────────────────────────────────────────────────────────────────
export const chatAPI = {
  sendMessage: (data) => api.post('/api/chat/message', data),
  getHistory: () => api.get('/api/chat/history'),
  clearHistory: () => api.delete('/api/chat/history'),
  transcribeVoice: (blob) => {
    const fd = new FormData(); fd.append('audio', blob, 'voice.webm');
    return api.post('/api/chat/voice', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
};

// ─── Document Vault ──────────────────────────────────────────────────────────
export const vaultAPI = {
  getDocuments: () => api.get('/api/vault/documents'),
  uploadDocument: (file, docType) => {
    const fd = new FormData(); fd.append('file', file); fd.append('doc_type', docType);
    return api.post('/api/vault/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
  shareDocument: (id, hours) => api.post(`/api/vault/documents/${id}/share`, { expiry_hours: hours }),
  deleteDocument: (id) => api.delete(`/api/vault/documents/${id}`),
};

// ─── Code Explainer ──────────────────────────────────────────────────────────
export const codeAPI = {
  explainError: (data) => api.post('/api/code/explain', data),
  fixCode: (data) => api.post('/api/code/fix', data),
  reviewCode: (data) => api.post('/api/code/review', data),
};

export default api;