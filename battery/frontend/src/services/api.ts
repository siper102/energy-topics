import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const dataService = {
  triggerIngestion: async (startDate: string, endDate: string) => {
    const response = await api.post('/data/ingest', { start_date: startDate, end_date: endDate });
    return response.data;
  },
  getIngestionStatus: async () => {
    const response = await api.get('/data/ingest/status');
    return response.data;
  },
  getDashboardData: async (startDate?: string, endDate?: string) => {
    const params = startDate && endDate ? { start_date: startDate, end_date: endDate } : {};
    const response = await api.get('/data/dashboard-data', { params });
    return response.data;
  },
};

export const optimizationService = {
  triggerOptimization: async (alpha: number = 0.001, gridFee: number = 0.01) => {
    const response = await api.post('/optimization/trigger', { alpha, grid_fee: gridFee });
    return response.data;
  },
  getStatus: async (taskId: string) => {
    const response = await api.get(`/optimization/status/${taskId}`);
    return response.data;
  },
};

export const jobService = {
  listJobs: async () => {
    const response = await api.get('/jobs');
    return response.data;
  },
  triggerFullJob: async (startDate: string, endDate: string, alpha: number = 0.001, gridFee: number = 0.01) => {
    const response = await api.post('/jobs/trigger-full', { start_date: startDate, end_date: endDate, alpha, grid_fee: gridFee });
    return response.data;
  },
};

export default api;
