import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const setupService = {
  listSetups: async () => {
    const response = await api.get('/setups');
    return response.data;
  },
  createSetup: async (setup: any) => {
    const response = await api.post('/setups', setup);
    return response.data;
  },
  getSetup: async (id: number) => {
    const response = await api.get(`/setups/${id}`);
    return response.data;
  },
};

export const dataService = {
  triggerIngestion: async (startDate: string, endDate: string, setupId: number) => {
    const response = await api.post('/data/ingest', { start_date: startDate, end_date: endDate, setup_id: setupId });
    return response.data;
  },
  getIngestionStatus: async () => {
    const response = await api.get('/data/ingest/status');
    return response.data;
  },
  getDashboardData: async (setupId: number, startDate?: string, endDate?: string) => {
    const params: any = { setup_id: setupId };
    if (startDate && endDate) {
      params.start_date = startDate;
      params.end_date = endDate;
    }
    const response = await api.get('/data/dashboard-data', { params });
    return response.data;
  },
};

export const optimizationService = {
  triggerOptimization: async (setupId: number, alpha: number = 0.001, gridFee: number = 0.01) => {
    const response = await api.post('/optimization/trigger', { alpha, grid_fee: gridFee, setup_id: setupId });
    return response.data;
  },
  getStatus: async (taskId: string) => {
    const response = await api.get(`/optimization/status/${taskId}`);
    return response.data;
  },
};

export const jobService = {
  listJobs: async (setupId?: number, page: number = 1, pageSize: number = 7) => {
    const params: any = { page, page_size: pageSize };
    if (setupId) params.setup_id = setupId;
    const response = await api.get('/jobs', { params });
    return response.data;
  },
  triggerFullJob: async (startDate: string, endDate: string, setupId: number, alpha: number = 0.001, gridFee: number = 0.01) => {
    const response = await api.post('/jobs/trigger-full', { start_date: startDate, end_date: endDate, setup_id: setupId, alpha, grid_fee: gridFee });
    return response.data;
  },
};

export default api;
