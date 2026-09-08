import axios from 'axios';
import type { ChatRequest, ChatResponse, Template, TemplateSearchResult, PolicySearchResult, Generation, User, FacultyProfile, TemplateSchema, FillTemplateResponse } from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  login: async (email: string, password: string) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  mockOidcLogin: async (email: string) => {
    const response = await api.post('/auth/mock-oidc-login', null, {
      params: { email },
    });
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

export const chatApi = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post('/chat', request);
    return response.data;
  },
};

export const templateApi = {
  list: async (department?: string, activeOnly = true): Promise<Template[]> => {
    const response = await api.get('/admin/templates', {
      params: { department, active_only: activeOnly },
    });
    return response.data;
  },

  search: async (query: string, limit = 5): Promise<TemplateSearchResult[]> => {
    const response = await api.get('/admin/templates/search', {
      params: { q: query, limit },
    });
    return response.data;
  },

  get: async (id: string): Promise<Template> => {
    const response = await api.get(`/admin/templates/${id}`);
    return response.data;
  },

  create: async (formData: FormData): Promise<Template> => {
    const response = await api.post('/admin/templates', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  update: async (id: string, data: Partial<Template>): Promise<Template> => {
    const response = await api.patch(`/admin/templates/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/admin/templates/${id}`);
  },
};

export const policyApi = {
  upload: async (file: File, sourceDoc: string, department?: string, tags?: string[]): Promise<PolicySearchResult[]> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_doc', sourceDoc);
    if (department) formData.append('department', department);
    if (tags) formData.append('tags', tags.join(','));
    
    const response = await api.post('/admin/policy-docs', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  search: async (query: string, department?: string, limit = 5): Promise<PolicySearchResult[]> => {
    const response = await api.get('/admin/policy-docs/search', {
      params: { q: query, department, limit },
    });
    return response.data;
  },
};

export const generationApi = {
  getUserGenerations: async (userId: string): Promise<Generation[]> => {
    const response = await api.get(`/generations/${userId}`);
    return response.data;
  },
};

export const fileApi = {
  downloadUrl: (path: string) => `/api/files/${path}`,
};

export const facultyApi = {
  getProfile: async (userId: string): Promise<FacultyProfile> => {
    const response = await api.get(`/chat/tools/faculty-profile/${userId}`);
    return response.data;
  },
};

export default api;