import axios from 'axios';

const BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

const api = axios.create({
  baseURL: BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      if (window.location.pathname !== '/login') window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

const multipart = { headers: { 'Content-Type': 'multipart/form-data' } };
const downloadFile = async (url) => {
  const response = await api.get(url, { responseType: 'blob' });
  const objectUrl = URL.createObjectURL(response.data);
  const anchor = document.createElement('a');
  anchor.href = objectUrl;
  anchor.download = url.split('/').pop() || 'download';
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
  return response;
};

export const authAPI = {
  login: (data) => api.post('/api/auth/login', data),
  register: (data) => api.post('/api/auth/register', data),
  me: () => api.get('/api/auth/me'),
};

export const academicAPI = {
  getMarks: () => api.get('/api/academic/marks'),
  addMark: (data) => api.post('/api/academic/marks', data),
  deleteMark: (id) => api.delete(`/api/academic/marks/${id}`),
  getCGPA: () => api.get('/api/academic/cgpa'),
  getWeaknesses: () => api.get('/api/academic/weakness'),
  generateRoadmap: (data) => api.post('/api/roadmap/generate', data),
};

export const notesAPI = {
  getNotes: () => api.get('/api/notes/'),
  uploadNote: (file, subject, topic) => {
    const form = new FormData();
    form.append('file', file);
    if (subject) form.append('subject', subject);
    if (topic) form.append('topic', topic);
    return api.post('/api/notes/upload', form, multipart);
  },
  deleteNote: (id) => api.delete(`/api/notes/${id}`),
  askQuestion: (question, subject) => api.post('/api/notes/ask', { question, subject }),
};

export const contentAPI = {
  generatePPT: (data) => api.post('/api/content/generate/ppt', data),
  generateDoc: (data) => api.post('/api/content/generate/document', data),
  downloadPPT: (fileName) => downloadFile(`/api/content/download/ppt/${encodeURIComponent(fileName)}`),
  downloadDoc: (fileName) => downloadFile(`/api/content/download/doc/${encodeURIComponent(fileName)}`),
};

export const careerAPI = {
  generateResume: (data) => api.post('/api/career/resume/build', data),
  downloadResume: (fileName) => downloadFile(`/api/career/resume/download/${encodeURIComponent(fileName)}`),
  matchJD: (data) => api.post('/api/career/jd-match', data),
  getJobs: () => api.get('/api/career/applications'),
  addJob: (data) => api.post('/api/career/applications', data),
  updateJob: (id, data) => api.put(`/api/career/applications/${id}`, data),
  deleteJob: (id) => api.delete(`/api/career/applications/${id}`),
  getAnalytics: () => api.get('/api/career/analytics'),
};

export const roadmapAPI = {
  generateRoadmap: (data) => api.post('/api/roadmap/generate', data),
  getRoadmaps: () => api.get('/api/roadmap/'),
  markComplete: (id, topic) => api.post(`/api/roadmap/${id}/complete-topic`, { topic }),
  deleteRoadmap: (id) => api.delete(`/api/roadmap/${id}`),
};

export const chatAPI = {
  sendMessage: (data) => api.post('/api/chat/message', data),
  transcribeVoice: (blob) => {
    const form = new FormData();
    form.append('file', blob, 'voice.webm');
    return api.post('/api/chat/voice', form, multipart);
  },
};

export const vaultAPI = {
  getDocuments: () => api.get('/api/vault/'),
  uploadDocument: (file, docType) => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/api/vault/upload', form, {
      params: { doc_type: docType },
    });
  },
  downloadDocument: (id) => downloadFile(`/api/vault/download/${id}`),
  shareDocument: (id, hours) => api.post(`/api/vault/share/${id}`, null, {
    params: { expire_hours: hours },
  }),
  revokeShareDocument: (id) => api.delete(`/api/vault/share/${id}`),
  deleteDocument: (id) => api.delete(`/api/vault/${id}`),
};


export default api;
