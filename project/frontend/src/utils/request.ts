import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { message } from 'antd';
import { configManager } from '../config';
import { useAuthStore } from '../stores/authStore';

// 创建axios实例
const request: AxiosInstance = axios.create({
  baseURL: configManager.getApiBaseUrl(),
  timeout: configManager.getApiTimeout(),
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 添加认证token
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // 添加请求ID用于追踪
    if (config.headers) {
      config.headers['X-Request-ID'] = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    return config;
  },
  (error) => {
    console.error('请求拦截器错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    // 成功响应直接返回
    return response;
  },
  async (error) => {
    console.error('响应错误:', error);
    
    // 处理网络错误
    if (!error.response) {
      message.error('网络连接失败，请检查网络设置');
      return Promise.reject(new Error('网络连接失败'));
    }
    
    const { status, data } = error.response;
    const originalRequest = error.config;
    
    // 处理不同的HTTP状态码
    switch (status) {
      case 400:
        message.error(data?.detail || '请求参数错误');
        break;
      case 401:
        if (!originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            // 尝试刷新token
            await useAuthStore.getState().refreshAccessToken();
            
            // 重试原请求
            const newToken = localStorage.getItem('access_token');
            if (newToken && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
            }
            return request(originalRequest);
          } catch (refreshError) {
            // 刷新失败，清除认证信息并跳转到登录页
            useAuthStore.getState().clearAuth();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        } else {
          message.error('登录已过期，请重新登录');
          // 清除本地存储的token
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          // 跳转到登录页
          window.location.href = '/login';
        }
        break;
      case 403:
        message.error('没有权限访问该资源');
        break;
      case 404:
        message.error('请求的资源不存在');
        break;
      case 422:
        // 处理验证错误
        if (data?.detail && Array.isArray(data.detail)) {
          const errorMessages = data.detail.map((err: any) => {
            if (err.loc && err.msg) {
              return `${err.loc.join('.')}: ${err.msg}`;
            }
            return err.msg || '验证错误';
          });
          message.error(errorMessages.join('; '));
        } else {
          message.error(data?.detail || '数据验证失败');
        }
        break;
      case 429:
        message.error('请求过于频繁，请稍后再试');
        break;
      case 500:
        message.error('服务器内部错误，请稍后再试');
        break;
      case 502:
      case 503:
      case 504:
        message.error('服务暂时不可用，请稍后再试');
        break;
      default:
        message.error(data?.detail || `请求失败 (${status})`);
    }
    
    return Promise.reject(error);
  }
);

// 导出请求实例
export { request };

// 导出常用的请求方法
export const get = (url: string, config?: AxiosRequestConfig) => {
  return request.get(url, config);
};

export const post = (url: string, data?: any, config?: AxiosRequestConfig) => {
  return request.post(url, data, config);
};

export const put = (url: string, data?: any, config?: AxiosRequestConfig) => {
  return request.put(url, data, config);
};

export const patch = (url: string, data?: any, config?: AxiosRequestConfig) => {
  return request.patch(url, data, config);
};

export const del = (url: string, config?: AxiosRequestConfig) => {
  return request.delete(url, config);
};

// 文件上传专用方法
export const uploadFile = (url: string, file: File, onProgress?: (progress: number) => void) => {
  const formData = new FormData();
  formData.append('file', file);
  
  return request.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
  });
};

// 文件下载专用方法
export const downloadFile = async (url: string, filename?: string) => {
  try {
    const response = await request.get(url, {
      responseType: 'blob',
    });
    
    // 创建下载链接
    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    
    // 从响应头获取文件名
    const contentDisposition = response.headers['content-disposition'];
    let downloadFilename = filename;
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="(.+)"/i);
      if (filenameMatch) {
        downloadFilename = filenameMatch[1];
      }
    }
    
    link.download = downloadFilename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
    
    message.success('文件下载成功');
  } catch (error) {
    console.error('文件下载失败:', error);
    message.error('文件下载失败');
    throw error;
  }
};

export default request;