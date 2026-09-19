import axios from 'axios';

const API_BASE_URL = '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const registerUser = async (email, password) => {
  const response = await api.post('/auth/register', { email, password });
  return response.data;
};

export const loginUser = async (email, password) => {
  const response = await api.post('/auth/login', { email, password });
  return response.data;
};

export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const fetchDocuments = async () => {
  const response = await api.get('/documents');
  return response.data;
};

export const fetchDocument = async (id) => {
  const response = await api.get(`/documents/${id}`);
  return response.data;
};

export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const deleteDocument = async (id) => {
  const response = await api.delete(`/documents/${id}`);
  return response.data;
};

export const processDocument = async (id) => {
  const response = await api.post(`/documents/${id}/process`);
  return response.data;
};

export const associateDocument = async (id, relatedDocumentId, relationshipType = 'ANSWER_KEY') => {
  const response = await api.put(`/documents/${id}/associate`, {
    related_document_id: relatedDocumentId,
    relationship_type: relationshipType,
  });
  return response.data;
};

export const fetchDocumentChunks = async (id) => {
  const response = await api.get(`/documents/${id}/chunks`);
  return response.data;
};

export const fetchDocumentQuestions = async (id, params = {}) => {
  const response = await api.get(`/documents/${id}/questions`, { params });
  return response.data;
};

export const addCustomQuestion = async (documentId, questionData) => {
  const response = await api.post(`/documents/${documentId}/questions`, questionData);
  return response.data;
};

export const updateQuestion = async (questionId, questionData) => {
  const response = await api.put(`/questions/${questionId}`, questionData);
  return response.data;
};

export const deleteQuestion = async (questionId) => {
  const response = await api.delete(`/questions/${questionId}`);
  return response.data;
};

export const getExportUrl = (documentId, format = 'json') => {
  return `${API_BASE_URL}/documents/${documentId}/export?format=${format}`;
};

export default api;
