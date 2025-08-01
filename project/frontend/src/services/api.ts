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

// 物料管理API
export const materialApi = {
  // 获取物料列表
  getMaterials: (params?: any) => {
    return api.get('/api/materials/', { params });
  },
  
  // 创建物料
  createMaterial: (data: any) => {
    return api.post('/api/materials/', data);
  },
  
  // 更新物料
  updateMaterial: (id: string, data: any) => {
    return api.put(`/api/materials/${id}`, data);
  },
  
  // 删除物料
  deleteMaterial: (id: string) => {
    return api.delete(`/api/materials/${id}`);
  },
  
  // 物料入库
  stockIn: (data: any) => {
    return api.post('/api/materials/stock-in', data);
  },
  
  // 物料出库
  stockOut: (data: any) => {
    return api.post('/api/materials/stock-out', data);
  },
  
  // 物料调拨
  stockTransfer: (data: any) => {
    return api.post('/api/materials/stock-transfer', data);
  },
  
  // 物料盘点
  stockCheck: (data: any) => {
    return api.post('/api/materials/stock-check', data);
  },
  
  // 获取物料统计
  getMaterialStats: () => {
    return api.get('/api/materials/stats');
  },
  
  // 获取库存预警
  getStockAlerts: () => {
    return api.get('/api/materials/stock-alerts');
  }
};

// BOM管理API
export const bomApi = {
  // 获取BOM列表
  getBOMs: (params?: any) => {
    return api.get('/api/bom/', { params });
  },
  
  // 创建BOM
  createBOM: (data: any) => {
    return api.post('/api/bom/', data);
  },
  
  // 更新BOM
  updateBOM: (id: string, data: any) => {
    return api.put(`/api/bom/${id}`, data);
  },
  
  // 删除BOM
  deleteBOM: (id: string) => {
    return api.delete(`/api/bom/${id}`);
  },
  
  // 获取BOM详情
  getBOMDetail: (id: string) => {
    return api.get(`/api/bom/${id}`);
  }
};

// 生产计划API
export const productionApi = {
  // 获取生产计划列表
  getProductionPlans: (params?: any) => {
    return api.get('/api/production/plans', { params });
  },
  
  // 创建生产计划
  createProductionPlan: (data: any) => {
    return api.post('/api/production/plans', data);
  },
  
  // 更新生产计划
  updateProductionPlan: (id: string, data: any) => {
    return api.put(`/api/production/plans/${id}`, data);
  },
  
  // 删除生产计划
  deleteProductionPlan: (id: string) => {
    return api.delete(`/api/production/plans/${id}`);
  },
  
  // 更新生产进度
  updateProgress: (id: string, data: any) => {
    return api.put(`/api/production/plans/${id}/progress`, data);
  },
  
  // 完成生产
  completeProduction: (id: string, data: any) => {
    return api.put(`/api/production/plans/${id}/complete`, data);
  }
};

// 订单管理API
export const orderApi = {
  // 获取订单列表
  getOrders: (params?: any) => {
    return api.get('/api/orders/', { params });
  },
  
  // 创建订单
  createOrder: (data: any) => {
    return api.post('/api/orders/', data);
  },
  
  // 更新订单
  updateOrder: (id: string, data: any) => {
    return api.put(`/api/orders/${id}`, data);
  },
  
  // 删除订单
  deleteOrder: (id: string) => {
    return api.delete(`/api/orders/${id}`);
  },
  
  // 获取订单详情
  getOrderDetail: (id: string) => {
    return api.get(`/api/orders/${id}`);
  }
};

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