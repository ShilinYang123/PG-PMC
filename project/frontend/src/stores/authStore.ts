import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import axios from 'axios';
import { message } from 'antd';

// 用户信息接口
export interface UserInfo {
  id: number;
  username: string;
  email?: string;
  full_name: string;
  employee_id?: string;
  department?: string;
  position?: string;
  role: string;
  workshop?: string;
  avatar?: string;
  permissions: string[];
  last_login_at?: string;
}

// 登录请求接口
export interface LoginRequest {
  username: string;
  password: string;
  remember_me?: boolean;
  captcha?: string;
}

// 令牌信息接口
export interface TokenInfo {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// 认证状态接口
interface AuthState {
  // 状态
  isAuthenticated: boolean;
  isLoading: boolean;
  user: UserInfo | null;
  token: string | null;
  refreshToken: string | null;
  permissions: string[];
  
  // 方法
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<void>;
  getCurrentUser: () => Promise<void>;
  updateUserInfo: (userInfo: Partial<UserInfo>) => void;
  checkPermission: (permission: string) => boolean;
  checkRole: (role: string) => boolean;
  clearAuth: () => void;
}

// API基础URL
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

// 创建axios实例
const authApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
authApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
authApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await authApi.post('/auth/refresh', {
            refresh_token: refreshToken
          });
          
          const { access_token, refresh_token: newRefreshToken } = response.data.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', newRefreshToken);
          
          // 重试原请求
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return authApi(originalRequest);
        }
      } catch (refreshError) {
        // 刷新失败，清除认证信息
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // 初始状态
      isAuthenticated: false,
      isLoading: false,
      user: null,
      token: null,
      refreshToken: null,
      permissions: [],

      // 登录方法
      login: async (credentials: LoginRequest) => {
        try {
          set({ isLoading: true });
          
          const response = await authApi.post('/auth/login', credentials);
          const { data } = response.data;
          
          const { access_token, refresh_token, token_type, expires_in } = data;
          
          // 存储令牌
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
          
          // 更新状态
          set({
            isAuthenticated: true,
            token: access_token,
            refreshToken: refresh_token,
            isLoading: false
          });
          
          // 获取用户信息
          await get().getCurrentUser();
          
        } catch (error: any) {
          set({ isLoading: false });
          throw error;
        }
      },

      // 登出方法
      logout: async () => {
        try {
          set({ isLoading: true });
          
          // 调用后端登出接口
          await authApi.post('/auth/logout');
          
        } catch (error) {
          console.error('登出请求失败:', error);
        } finally {
          // 无论请求是否成功，都清除本地状态
          get().clearAuth();
        }
      },

      // 刷新访问令牌
      refreshAccessToken: async () => {
        try {
          const refreshToken = get().refreshToken || localStorage.getItem('refresh_token');
          
          if (!refreshToken) {
            throw new Error('没有刷新令牌');
          }
          
          const response = await authApi.post('/auth/refresh', {
            refresh_token: refreshToken
          });
          
          const { access_token, refresh_token: newRefreshToken } = response.data.data;
          
          // 更新令牌
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', newRefreshToken);
          
          set({
            token: access_token,
            refreshToken: newRefreshToken
          });
          
        } catch (error) {
          console.error('刷新令牌失败:', error);
          get().clearAuth();
          throw error;
        }
      },

      // 获取当前用户信息
      getCurrentUser: async () => {
        try {
          const response = await authApi.get('/auth/me');
          const userData = response.data.data;
          
          set({
            user: userData,
            permissions: userData.permissions || []
          });
          
        } catch (error) {
          console.error('获取用户信息失败:', error);
          throw error;
        }
      },

      // 更新用户信息
      updateUserInfo: (userInfo: Partial<UserInfo>) => {
        const currentUser = get().user;
        if (currentUser) {
          set({
            user: { ...currentUser, ...userInfo }
          });
        }
      },

      // 检查权限
      checkPermission: (permission: string) => {
        const permissions = get().permissions;
        return permissions.includes(permission) || permissions.includes('*');
      },

      // 检查角色
      checkRole: (role: string) => {
        const user = get().user;
        return user?.role === role || user?.role === 'admin';
      },

      // 清除认证信息
      clearAuth: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        set({
          isAuthenticated: false,
          isLoading: false,
          user: null,
          token: null,
          refreshToken: null,
          permissions: []
        });
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        permissions: state.permissions
      })
    }
  )
);

// 初始化认证状态
export const initializeAuth = async () => {
  const token = localStorage.getItem('access_token');
  const refreshToken = localStorage.getItem('refresh_token');
  
  if (token && refreshToken) {
    try {
      useAuthStore.setState({
        isAuthenticated: true,
        token,
        refreshToken
      });
      
      // 尝试获取用户信息
      await useAuthStore.getState().getCurrentUser();
    } catch (error) {
      console.error('初始化认证状态失败:', error);
      useAuthStore.getState().clearAuth();
    }
  }
};

// 权限检查Hook
export const usePermission = (permission: string) => {
  const checkPermission = useAuthStore((state) => state.checkPermission);
  return checkPermission(permission);
};

// 角色检查Hook
export const useRole = (role: string) => {
  const checkRole = useAuthStore((state) => state.checkRole);
  return checkRole(role);
};

// 导出认证相关的工具函数
export const authUtils = {
  isTokenExpired: (token: string): boolean => {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp * 1000 < Date.now();
    } catch {
      return true;
    }
  },
  
  getTokenPayload: (token: string) => {
    try {
      return JSON.parse(atob(token.split('.')[1]));
    } catch {
      return null;
    }
  },
  
  formatPermissions: (permissions: string[]): string[] => {
    return permissions.map(p => p.toLowerCase().replace(/[^a-z0-9]/g, '_'));
  }
};

export default useAuthStore;