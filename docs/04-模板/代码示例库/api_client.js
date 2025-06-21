// API 接口代码示例 - 3AI工作室
// 提供统一的 API 客户端，支持请求拦截、响应处理、错误处理和缓存

const axios = require('axios');
const qs = require('querystring');

// ================================
// API 配置
// ================================

/**
 * API 配置常量
 */
const API_CONFIG = {
  baseURL: process.env.API_BASE_URL || 'https://api.example.com',
  timeout: parseInt(process.env.API_TIMEOUT) || 10000,
  retryAttempts: 3,
  retryDelay: 1000,
  cacheTimeout: 5 * 60 * 1000, // 5分钟
};

/**
 * HTTP 状态码
 */
const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
  GATEWAY_TIMEOUT: 504
};

/**
 * 错误类型
 */
const ERROR_TYPES = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR: 'AUTHORIZATION_ERROR',
  NOT_FOUND_ERROR: 'NOT_FOUND_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  RATE_LIMIT_ERROR: 'RATE_LIMIT_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR'
};

// ================================
// 自定义错误类
// ================================

class APIError extends Error {
  constructor(message, type, status, data = null) {
    super(message);
    this.name = 'APIError';
    this.type = type;
    this.status = status;
    this.data = data;
    this.timestamp = new Date().toISOString();
  }

  toJSON() {
    return {
      name: this.name,
      message: this.message,
      type: this.type,
      status: this.status,
      data: this.data,
      timestamp: this.timestamp
    };
  }
}

// ================================
// 请求缓存
// ================================

class RequestCache {
  constructor(maxSize = 100) {
    this.cache = new Map();
    this.maxSize = maxSize;
  }

  /**
   * 生成缓存键
   */
  generateKey(method, url, params, data) {
    const key = {
      method: method.toUpperCase(),
      url,
      params: params || {},
      data: data || {}
    };
    return JSON.stringify(key);
  }

  /**
   * 获取缓存
   */
  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;
    
    if (Date.now() > item.expiry) {
      this.cache.delete(key);
      return null;
    }
    
    return item.data;
  }

  /**
   * 设置缓存
   */
  set(key, data, ttl = API_CONFIG.cacheTimeout) {
    // 如果缓存已满，删除最旧的项
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    
    this.cache.set(key, {
      data,
      expiry: Date.now() + ttl
    });
  }

  /**
   * 删除缓存
   */
  delete(key) {
    this.cache.delete(key);
  }

  /**
   * 清空缓存
   */
  clear() {
    this.cache.clear();
  }

  /**
   * 获取缓存统计
   */
  getStats() {
    return {
      size: this.cache.size,
      maxSize: this.maxSize,
      keys: Array.from(this.cache.keys())
    };
  }
}

// ================================
// 请求重试机制
// ================================

class RetryManager {
  constructor(maxAttempts = 3, baseDelay = 1000) {
    this.maxAttempts = maxAttempts;
    this.baseDelay = baseDelay;
  }

  /**
   * 是否应该重试
   */
  shouldRetry(error, attempt) {
    if (attempt >= this.maxAttempts) return false;
    
    // 网络错误或服务器错误才重试
    if (error.code === 'ECONNABORTED' || error.code === 'ENOTFOUND') {
      return true;
    }
    
    if (error.response) {
      const status = error.response.status;
      return status >= 500 || status === 429;
    }
    
    return false;
  }

  /**
   * 计算延迟时间（指数退避）
   */
  calculateDelay(attempt) {
    return this.baseDelay * Math.pow(2, attempt - 1) + Math.random() * 1000;
  }

  /**
   * 等待
   */
  async wait(delay) {
    return new Promise(resolve => setTimeout(resolve, delay));
  }
}

// ================================
// API 客户端类
// ================================

class APIClient {
  constructor(config = {}) {
    this.config = { ...API_CONFIG, ...config };
    this.cache = new RequestCache();
    this.retryManager = new RetryManager(
      this.config.retryAttempts,
      this.config.retryDelay
    );
    
    // 创建 axios 实例
    this.instance = axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });
    
    this.setupInterceptors();
  }

  /**
   * 设置拦截器
   */
  setupInterceptors() {
    // 请求拦截器
    this.instance.interceptors.request.use(
      (config) => {
        // 添加认证头
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        // 添加请求ID
        config.headers['X-Request-ID'] = this.generateRequestId();
        
        // 记录请求日志
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        
        return config;
      },
      (error) => {
        console.error('Request interceptor error:', error);
        return Promise.reject(error);
      }
    );
    
    // 响应拦截器
    this.instance.interceptors.response.use(
      (response) => {
        // 记录响应日志
        console.log(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        return this.handleResponseError(error);
      }
    );
  }

  /**
   * 处理响应错误
   */
  handleResponseError(error) {
    let apiError;
    
    if (error.response) {
      // 服务器响应错误
      const { status, data } = error.response;
      
      switch (status) {
        case HTTP_STATUS.BAD_REQUEST:
          apiError = new APIError(
            data.message || 'Bad Request',
            ERROR_TYPES.VALIDATION_ERROR,
            status,
            data
          );
          break;
        case HTTP_STATUS.UNAUTHORIZED:
          apiError = new APIError(
            'Authentication required',
            ERROR_TYPES.AUTHENTICATION_ERROR,
            status,
            data
          );
          this.handleAuthError();
          break;
        case HTTP_STATUS.FORBIDDEN:
          apiError = new APIError(
            'Access forbidden',
            ERROR_TYPES.AUTHORIZATION_ERROR,
            status,
            data
          );
          break;
        case HTTP_STATUS.NOT_FOUND:
          apiError = new APIError(
            'Resource not found',
            ERROR_TYPES.NOT_FOUND_ERROR,
            status,
            data
          );
          break;
        case HTTP_STATUS.TOO_MANY_REQUESTS:
          apiError = new APIError(
            'Rate limit exceeded',
            ERROR_TYPES.RATE_LIMIT_ERROR,
            status,
            data
          );
          break;
        default:
          if (status >= 500) {
            apiError = new APIError(
              'Server error',
              ERROR_TYPES.SERVER_ERROR,
              status,
              data
            );
          } else {
            apiError = new APIError(
              data.message || 'Unknown error',
              ERROR_TYPES.UNKNOWN_ERROR,
              status,
              data
            );
          }
      }
    } else if (error.request) {
      // 网络错误
      if (error.code === 'ECONNABORTED') {
        apiError = new APIError(
          'Request timeout',
          ERROR_TYPES.TIMEOUT_ERROR,
          0
        );
      } else {
        apiError = new APIError(
          'Network error',
          ERROR_TYPES.NETWORK_ERROR,
          0
        );
      }
    } else {
      // 其他错误
      apiError = new APIError(
        error.message,
        ERROR_TYPES.UNKNOWN_ERROR,
        0
      );
    }
    
    console.error('API Error:', apiError.toJSON());
    return Promise.reject(apiError);
  }

  /**
   * 处理认证错误
   */
  handleAuthError() {
    // 清除认证信息
    this.clearAuthToken();
    
    // 触发重新登录事件
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('auth:required'));
    }
  }

  /**
   * 获取认证令牌
   */
  getAuthToken() {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    }
    return process.env.API_TOKEN;
  }

  /**
   * 设置认证令牌
   */
  setAuthToken(token, persistent = false) {
    if (typeof window !== 'undefined') {
      if (persistent) {
        localStorage.setItem('auth_token', token);
      } else {
        sessionStorage.setItem('auth_token', token);
      }
    }
  }

  /**
   * 清除认证令牌
   */
  clearAuthToken() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      sessionStorage.removeItem('auth_token');
    }
  }

  /**
   * 生成请求ID
   */
  generateRequestId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  /**
   * 执行请求（带重试）
   */
  async executeRequest(requestFn, attempt = 1) {
    try {
      return await requestFn();
    } catch (error) {
      if (this.retryManager.shouldRetry(error, attempt)) {
        const delay = this.retryManager.calculateDelay(attempt);
        console.log(`Retrying request (attempt ${attempt + 1}) after ${delay}ms`);
        
        await this.retryManager.wait(delay);
        return this.executeRequest(requestFn, attempt + 1);
      }
      
      throw error;
    }
  }

  /**
   * GET 请求
   */
  async get(url, params = {}, options = {}) {
    const { useCache = true, cacheTimeout } = options;
    
    // 检查缓存
    if (useCache) {
      const cacheKey = this.cache.generateKey('GET', url, params);
      const cached = this.cache.get(cacheKey);
      if (cached) {
        console.log('Cache hit:', url);
        return cached;
      }
    }
    
    const requestFn = () => this.instance.get(url, { params, ...options });
    const response = await this.executeRequest(requestFn);
    
    // 设置缓存
    if (useCache && response.status === HTTP_STATUS.OK) {
      const cacheKey = this.cache.generateKey('GET', url, params);
      this.cache.set(cacheKey, response.data, cacheTimeout);
    }
    
    return response.data;
  }

  /**
   * POST 请求
   */
  async post(url, data = {}, options = {}) {
    const requestFn = () => this.instance.post(url, data, options);
    const response = await this.executeRequest(requestFn);
    
    // 清除相关缓存
    this.invalidateCache(url);
    
    return response.data;
  }

  /**
   * PUT 请求
   */
  async put(url, data = {}, options = {}) {
    const requestFn = () => this.instance.put(url, data, options);
    const response = await this.executeRequest(requestFn);
    
    // 清除相关缓存
    this.invalidateCache(url);
    
    return response.data;
  }

  /**
   * PATCH 请求
   */
  async patch(url, data = {}, options = {}) {
    const requestFn = () => this.instance.patch(url, data, options);
    const response = await this.executeRequest(requestFn);
    
    // 清除相关缓存
    this.invalidateCache(url);
    
    return response.data;
  }

  /**
   * DELETE 请求
   */
  async delete(url, options = {}) {
    const requestFn = () => this.instance.delete(url, options);
    const response = await this.executeRequest(requestFn);
    
    // 清除相关缓存
    this.invalidateCache(url);
    
    return response.data;
  }

  /**
   * 文件上传
   */
  async upload(url, file, options = {}) {
    const formData = new FormData();
    formData.append('file', file);
    
    // 添加额外字段
    if (options.fields) {
      Object.entries(options.fields).forEach(([key, value]) => {
        formData.append(key, value);
      });
    }
    
    const config = {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: options.onProgress,
      ...options
    };
    
    const requestFn = () => this.instance.post(url, formData, config);
    const response = await this.executeRequest(requestFn);
    
    return response.data;
  }

  /**
   * 文件下载
   */
  async download(url, options = {}) {
    const config = {
      responseType: 'blob',
      onDownloadProgress: options.onProgress,
      ...options
    };
    
    const requestFn = () => this.instance.get(url, config);
    const response = await this.executeRequest(requestFn);
    
    return response.data;
  }

  /**
   * 批量请求
   */
  async batch(requests) {
    const promises = requests.map(request => {
      const { method, url, data, params, options } = request;
      
      switch (method.toLowerCase()) {
        case 'get':
          return this.get(url, params, options);
        case 'post':
          return this.post(url, data, options);
        case 'put':
          return this.put(url, data, options);
        case 'patch':
          return this.patch(url, data, options);
        case 'delete':
          return this.delete(url, options);
        default:
          throw new Error(`Unsupported method: ${method}`);
      }
    });
    
    return Promise.allSettled(promises);
  }

  /**
   * 清除缓存
   */
  invalidateCache(pattern) {
    if (typeof pattern === 'string') {
      // 清除包含特定URL的缓存
      const keys = Array.from(this.cache.cache.keys());
      keys.forEach(key => {
        if (key.includes(pattern)) {
          this.cache.delete(key);
        }
      });
    } else {
      // 清除所有缓存
      this.cache.clear();
    }
  }

  /**
   * 获取客户端统计
   */
  getStats() {
    return {
      cache: this.cache.getStats(),
      config: this.config
    };
  }
}

// ================================
// API 服务基类
// ================================

class BaseAPIService {
  constructor(client, basePath = '') {
    this.client = client;
    this.basePath = basePath;
  }

  /**
   * 构建完整URL
   */
  buildUrl(path) {
    return `${this.basePath}${path}`.replace(/\/+/g, '/');
  }

  /**
   * 分页查询
   */
  async paginate(path, params = {}) {
    const { page = 1, limit = 10, ...filters } = params;
    
    const response = await this.client.get(this.buildUrl(path), {
      page,
      limit,
      ...filters
    });
    
    return {
      data: response.data || [],
      pagination: {
        page: response.page || page,
        limit: response.limit || limit,
        total: response.total || 0,
        pages: response.pages || Math.ceil((response.total || 0) / limit)
      }
    };
  }

  /**
   * 获取单个资源
   */
  async findById(id, options = {}) {
    return this.client.get(this.buildUrl(`/${id}`), {}, options);
  }

  /**
   * 创建资源
   */
  async create(data, options = {}) {
    return this.client.post(this.buildUrl('/'), data, options);
  }

  /**
   * 更新资源
   */
  async update(id, data, options = {}) {
    return this.client.put(this.buildUrl(`/${id}`), data, options);
  }

  /**
   * 部分更新资源
   */
  async patch(id, data, options = {}) {
    return this.client.patch(this.buildUrl(`/${id}`), data, options);
  }

  /**
   * 删除资源
   */
  async delete(id, options = {}) {
    return this.client.delete(this.buildUrl(`/${id}`), options);
  }
}

// ================================
// 具体服务示例
// ================================

/**
 * 用户服务
 */
class UserService extends BaseAPIService {
  constructor(client) {
    super(client, '/api/users');
  }

  /**
   * 用户登录
   */
  async login(credentials) {
    const response = await this.client.post('/api/auth/login', credentials);
    
    // 保存认证令牌
    if (response.token) {
      this.client.setAuthToken(response.token, credentials.remember);
    }
    
    return response;
  }

  /**
   * 用户注册
   */
  async register(userData) {
    return this.client.post('/api/auth/register', userData);
  }

  /**
   * 获取当前用户信息
   */
  async getCurrentUser() {
    return this.client.get('/api/auth/me', {}, { useCache: true });
  }

  /**
   * 更新用户头像
   */
  async updateAvatar(file, onProgress) {
    return this.client.upload('/api/users/avatar', file, {
      onProgress
    });
  }

  /**
   * 搜索用户
   */
  async search(query, filters = {}) {
    return this.paginate('/search', {
      q: query,
      ...filters
    });
  }
}

/**
 * 文章服务
 */
class ArticleService extends BaseAPIService {
  constructor(client) {
    super(client, '/api/articles');
  }

  /**
   * 获取热门文章
   */
  async getPopular(limit = 10) {
    return this.client.get(this.buildUrl('/popular'), { limit });
  }

  /**
   * 获取文章评论
   */
  async getComments(articleId, page = 1) {
    return this.paginate(`/${articleId}/comments`, { page });
  }

  /**
   * 添加评论
   */
  async addComment(articleId, comment) {
    return this.client.post(this.buildUrl(`/${articleId}/comments`), comment);
  }

  /**
   * 点赞文章
   */
  async like(articleId) {
    return this.client.post(this.buildUrl(`/${articleId}/like`));
  }

  /**
   * 收藏文章
   */
  async bookmark(articleId) {
    return this.client.post(this.buildUrl(`/${articleId}/bookmark`));
  }
}

// ================================
// 使用示例
// ================================

// 创建 API 客户端
const apiClient = new APIClient({
  baseURL: 'https://api.myapp.com',
  timeout: 15000,
  retryAttempts: 3
});

// 创建服务实例
const userService = new UserService(apiClient);
const articleService = new ArticleService(apiClient);

// 使用示例
async function example() {
  try {
    // 用户登录
    const loginResult = await userService.login({
      email: 'user@example.com',
      password: 'password123',
      remember: true
    });
    
    console.log('Login successful:', loginResult);
    
    // 获取当前用户信息
    const currentUser = await userService.getCurrentUser();
    console.log('Current user:', currentUser);
    
    // 获取文章列表
    const articles = await articleService.paginate('/', {
      page: 1,
      limit: 20,
      category: 'tech'
    });
    
    console.log('Articles:', articles);
    
    // 批量请求
    const batchResults = await apiClient.batch([
      { method: 'get', url: '/api/users/profile' },
      { method: 'get', url: '/api/articles/popular' },
      { method: 'get', url: '/api/notifications' }
    ]);
    
    console.log('Batch results:', batchResults);
    
  } catch (error) {
    console.error('API Error:', error);
    
    // 根据错误类型处理
    switch (error.type) {
      case ERROR_TYPES.AUTHENTICATION_ERROR:
        // 重定向到登录页
        break;
      case ERROR_TYPES.NETWORK_ERROR:
        // 显示网络错误提示
        break;
      case ERROR_TYPES.VALIDATION_ERROR:
        // 显示表单验证错误
        break;
      default:
        // 显示通用错误提示
        break;
    }
  }
}

// ================================
// 导出模块
// ================================
module.exports = {
  APIClient,
  BaseAPIService,
  UserService,
  ArticleService,
  APIError,
  RequestCache,
  RetryManager,
  
  // 常量
  API_CONFIG,
  HTTP_STATUS,
  ERROR_TYPES,
  
  // 实例
  apiClient
};

// ================================
// 使用说明
// ================================

/*
1. 基本配置：
   - 设置 API_BASE_URL 环境变量
   - 配置超时时间和重试次数
   - 设置认证令牌

2. 错误处理：
   - 网络错误自动重试
   - 认证错误自动清除令牌
   - 结构化错误信息
   - 错误类型分类

3. 缓存机制：
   - GET 请求自动缓存
   - 写操作自动清除缓存
   - 可配置缓存时间
   - 内存缓存实现

4. 请求拦截：
   - 自动添加认证头
   - 请求/响应日志
   - 请求ID追踪
   - 统一错误处理

5. 高级功能：
   - 文件上传/下载
   - 批量请求
   - 分页查询
   - 请求重试
   - 进度监控

6. 最佳实践：
   - 使用服务类封装API
   - 统一错误处理
   - 合理使用缓存
   - 监控API性能
   - 处理网络异常

7. 扩展建议：
   - 集成 GraphQL
   - 添加请求队列
   - 实现离线支持
   - 添加请求去重
   - 集成监控系统
*/