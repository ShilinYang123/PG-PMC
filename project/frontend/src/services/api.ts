// API服务模块
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 报表API
export const reportApi = {
  // 生成报表
  generateReport: (data: any) => {
    return api.post('/api/reports/generate', data);
  },
  
  // 导出报表
  exportReport: (type: string, format: string) => {
    return api.get(`/api/reports/export/${type}`, {
      params: { format },
      responseType: 'blob'
    });
  },
  
  // 获取报表数据
  getReportData: (type: string, params: any) => {
    return api.get(`/api/reports/${type}`, { params });
  }
};

export default api;