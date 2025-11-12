import React, { createContext, useContext } from 'react';
import axios from 'axios';

const ApiContext = createContext();

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const ApiProvider = ({ children }) => {
  const screensApi = {
    getAll: (params = {}) => api.get('/api/screens', { params }),
    getById: (id) => api.get(`/api/screens/${id}`),
    getByName: (name, platform = 'web', locale = 'ru') => 
      api.get(`/api/screens/by-name/${name}`, { params: { platform, locale } }),
    create: (data) => api.post('/api/screens', data),
    update: (id, data) => api.put(`/api/screens/${id}`, data),
    delete: (id) => api.delete(`/api/screens/${id}`),
    duplicate: (id, newName) => api.post(`/api/screens/${id}/duplicate`, null, { params: { new_name: newName } }),
    createFromTemplate: (templateId, screenName, options = {}) => 
      api.post('/api/screens/create-from-template', {
        template_id: templateId,
        screen_name: screenName,
        screen_title: options.screenTitle,
        template_variables: options.templateVariables,
        platform: options.platform || 'web',
        locale: options.locale || 'ru'
      }),
  };

  const componentsApi = {
    getAll: (params = {}) => api.get('/api/components', { params }),
    getById: (id) => api.get(`/api/components/${id}`),
    create: (data) => api.post('/api/components', data),
    update: (id, data) => api.put(`/api/components/${id}`, data),
    delete: (id) => api.delete(`/api/components/${id}`),
    getCategories: () => api.get('/api/components/categories/list'),
  };

  const analyticsApi = {
    track: (event) => api.post('/api/analytics/track', event),
    getEvents: (params = {}) => api.get('/api/analytics/events', { params }),
    getEventsCount: (params = {}) => api.get('/api/analytics/events/count', { params }),
    getStats: (screenId, days = 7) => api.get(`/api/analytics/stats/${screenId}`, { params: { days } }),
    getOverview: (days = 7) => api.get('/api/analytics/overview', { params: { days } }),
  };

  const abTestingApi = {
    getAll: (params = {}) => api.get('/api/ab-testing', { params }),
    getById: (id) => api.get(`/api/ab-testing/${id}`),
    create: (data) => api.post('/api/ab-testing', data),
    update: (id, data) => api.put(`/api/ab-testing/${id}`, data),
    delete: (id) => api.delete(`/api/ab-testing/${id}`),
    activate: (id) => api.post(`/api/ab-testing/${id}/activate`),
    deactivate: (id) => api.post(`/api/ab-testing/${id}/deactivate`),
    getVariant: (screenId, userId, sessionId) => 
      api.get(`/api/ab-testing/screen/${screenId}/variant`, { 
        params: { user_id: userId, session_id: sessionId } 
      }),
  };

  const templatesApi = {
    getAll: (params = {}) => api.get('/api/templates', { params }),
    getById: (id) => api.get(`/api/templates/${id}`),
    create: (data) => api.post('/api/templates', data),
    update: (id, data) => api.put(`/api/templates/${id}`, data),
    delete: (id) => api.delete(`/api/templates/${id}`),
    inherit: (id, newName) => api.post(`/api/templates/${id}/inherit`, null, { params: { new_name: newName } }),
    getCategories: () => api.get('/api/templates/categories/list'),
  };

