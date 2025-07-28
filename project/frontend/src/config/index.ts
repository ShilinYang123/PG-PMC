#!/usr/bin/env node
/**
 * 前端应用配置
 * 集成统一配置管理中心，提供React应用的配置支持
 */

import axios from 'axios';

// 环境类型定义
export type Environment = 'development' | 'production' | 'testing' | 'local';

// 配置接口定义
export interface AppConfig {
  // 应用基本信息
  appName: string;
  version: string;
  description: string;
  
  // API配置
  apiBaseUrl: string;
  apiVersion: string;
  apiTimeout: number;
  
  // 环境配置
  environment: Environment;
  isDevelopment: boolean;
  isProduction: boolean;
  isTesting: boolean;
  
  // 功能开关
  enableMockData: boolean;
  enableDevTools: boolean;
  enableAnalytics: boolean;
  
  // UI配置
  theme: {
    primaryColor: string;
    layout: 'side' | 'top';
    fixedHeader: boolean;
    fixedSider: boolean;
    colorWeak: boolean;
  };
  
  // 分页配置
  pagination: {
    defaultPageSize: number;
    pageSizeOptions: string[];
    showSizeChanger: boolean;
    showQuickJumper: boolean;
  };
  
  // 文件上传配置
  upload: {
    maxFileSize: number;
    allowedTypes: string[];
    chunkSize: number;
  };
  
  // 缓存配置
  cache: {
    tokenKey: string;
    userInfoKey: string;
    settingsKey: string;
    timeout: number;
  };
  
  // 路由配置
  routing: {
    basename: string;
    hashRouter: boolean;
  };
}

// 默认配置
const defaultConfig: AppConfig = {
  appName: 'PMC全流程管理系统',
  version: '1.0.0',
  description: 'PMC全流程管理系统前端应用',
  
  apiBaseUrl: process.env.REACT_APP_API_BASE_URL || (process.env.NODE_ENV === 'development' ? '' : 'http://localhost:8000'),
  apiVersion: process.env.REACT_APP_API_VERSION || '/api/v1',
  apiTimeout: parseInt(process.env.REACT_APP_API_TIMEOUT || '30000'),
  
  environment: (process.env.NODE_ENV as Environment) || 'development',
  isDevelopment: process.env.NODE_ENV === 'development',
  isProduction: process.env.NODE_ENV === 'production',
  isTesting: process.env.NODE_ENV === 'test',
  
  enableMockData: process.env.REACT_APP_ENABLE_MOCK === 'true',
  enableDevTools: process.env.NODE_ENV === 'development',
  enableAnalytics: process.env.REACT_APP_ENABLE_ANALYTICS === 'true',
  
  theme: {
    primaryColor: process.env.REACT_APP_PRIMARY_COLOR || '#1890ff',
    layout: (process.env.REACT_APP_LAYOUT as 'side' | 'top') || 'side',
    fixedHeader: process.env.REACT_APP_FIXED_HEADER !== 'false',
    fixedSider: process.env.REACT_APP_FIXED_SIDER !== 'false',
    colorWeak: process.env.REACT_APP_COLOR_WEAK === 'true',
  },
  
  pagination: {
    defaultPageSize: parseInt(process.env.REACT_APP_PAGE_SIZE || '20'),
    pageSizeOptions: ['10', '20', '50', '100'],
    showSizeChanger: true,
    showQuickJumper: true,
  },
  
  upload: {
    maxFileSize: parseInt(process.env.REACT_APP_MAX_FILE_SIZE || '10485760'), // 10MB
    allowedTypes: [
      'image/jpeg',
      'image/png',
      'image/gif',
      'application/pdf',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/csv'
    ],
    chunkSize: 1024 * 1024, // 1MB
  },
  
  cache: {
    tokenKey: 'pmc_token',
    userInfoKey: 'pmc_user_info',
    settingsKey: 'pmc_settings',
    timeout: 7 * 24 * 60 * 60 * 1000, // 7天
  },
  
  routing: {
    basename: process.env.PUBLIC_URL || '/',
    hashRouter: process.env.REACT_APP_HASH_ROUTER === 'true',
  },
};

// 统一配置管理器
class ConfigManager {
  private config: AppConfig;
  private unifiedConfig: any = null;
  
  constructor() {
    this.config = { ...defaultConfig };
    this.loadUnifiedConfig();
  }
  
  /**
   * 加载统一配置
   */
  private async loadUnifiedConfig(): Promise<void> {
    try {
      // 尝试从后端获取统一配置
      const response = await axios.get('/api/v1/config/frontend', {
        timeout: 5000,
        validateStatus: () => true, // 不抛出错误
      });
      
      if (response.status === 200 && response.data) {
        this.unifiedConfig = response.data;
        this.mergeUnifiedConfig();
        console.log('✅ 已加载统一配置');
      } else {
        console.warn('⚠️ 无法获取统一配置，使用默认配置');
      }
    } catch (error) {
      console.warn('⚠️ 统一配置加载失败，使用默认配置:', error);
    }
  }
  
  /**
   * 合并统一配置
   */
  private mergeUnifiedConfig(): void {
    if (!this.unifiedConfig) return;
    
    try {
      // 合并基本信息
      if (this.unifiedConfig.project_name) {
        this.config.appName = this.unifiedConfig.project_name;
      }
      if (this.unifiedConfig.version) {
        this.config.version = this.unifiedConfig.version;
      }
      if (this.unifiedConfig.description) {
        this.config.description = this.unifiedConfig.description;
      }
      
      // 合并API配置
      if (this.unifiedConfig.host && this.unifiedConfig.port) {
        this.config.apiBaseUrl = `http://${this.unifiedConfig.host}:${this.unifiedConfig.port}`;
      }
      if (this.unifiedConfig.api_v1_prefix) {
        this.config.apiVersion = this.unifiedConfig.api_v1_prefix;
      }
      
      // 合并环境配置
      if (this.unifiedConfig.environment) {
        this.config.environment = this.unifiedConfig.environment as Environment;
        this.config.isDevelopment = this.unifiedConfig.environment === 'development';
        this.config.isProduction = this.unifiedConfig.environment === 'production';
        this.config.isTesting = this.unifiedConfig.environment === 'testing';
      }
      
      // 合并分页配置
      if (this.unifiedConfig.default_page_size) {
        this.config.pagination.defaultPageSize = this.unifiedConfig.default_page_size;
      }
      
      // 合并上传配置
      if (this.unifiedConfig.max_file_size) {
        this.config.upload.maxFileSize = this.unifiedConfig.max_file_size;
      }
      if (this.unifiedConfig.allowed_file_types) {
        // 转换文件扩展名为MIME类型
        const mimeTypes = this.unifiedConfig.allowed_file_types.map((ext: string) => {
          const mimeMap: Record<string, string> = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.pdf': 'application/pdf',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.csv': 'text/csv',
          };
          return mimeMap[ext] || ext;
        });
        this.config.upload.allowedTypes = mimeTypes;
      }
      
      console.log('✅ 统一配置合并完成');
    } catch (error) {
      console.error('❌ 统一配置合并失败:', error);
    }
  }
  
  /**
   * 获取配置
   */
  public getConfig(): AppConfig {
    return { ...this.config };
  }
  
  /**
   * 获取API配置
   */
  public getApiConfig() {
    return {
      baseURL: this.config.apiBaseUrl + this.config.apiVersion,
      timeout: this.config.apiTimeout,
      headers: {
        'Content-Type': 'application/json',
      },
    };
  }

  /**
   * 获取API基础URL
   */
  public getApiBaseUrl(): string {
    return this.config.apiBaseUrl + this.config.apiVersion;
  }

  /**
   * 获取API超时时间
   */
  public getApiTimeout(): number {
    return this.config.apiTimeout;
  }
  
  /**
   * 获取主题配置
   */
  public getThemeConfig() {
    return { ...this.config.theme };
  }
  
  /**
   * 获取上传配置
   */
  public getUploadConfig() {
    return { ...this.config.upload };
  }
  
  /**
   * 获取分页配置
   */
  public getPaginationConfig() {
    return { ...this.config.pagination };
  }
  
  /**
   * 获取缓存配置
   */
  public getCacheConfig() {
    return { ...this.config.cache };
  }
  
  /**
   * 获取路由配置
   */
  public getRoutingConfig() {
    return { ...this.config.routing };
  }
  
  /**
   * 更新配置
   */
  public updateConfig(updates: Partial<AppConfig>): void {
    this.config = { ...this.config, ...updates };
  }
  
  /**
   * 重新加载配置
   */
  public async reloadConfig(): Promise<void> {
    await this.loadUnifiedConfig();
  }
  
  /**
   * 验证配置
   */
  public validateConfig(): { valid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    // 验证API配置
    if (!this.config.apiBaseUrl) {
      errors.push('API基础URL未配置');
    }
    
    // 验证上传配置
    if (this.config.upload.maxFileSize <= 0) {
      errors.push('文件上传大小限制无效');
    }
    
    // 验证分页配置
    if (this.config.pagination.defaultPageSize <= 0) {
      errors.push('默认分页大小无效');
    }
    
    return {
      valid: errors.length === 0,
      errors,
    };
  }
  
  /**
   * 导出环境变量
   */
  public exportEnvVars(): Record<string, string> {
    return {
      REACT_APP_API_BASE_URL: this.config.apiBaseUrl,
      REACT_APP_API_VERSION: this.config.apiVersion,
      REACT_APP_API_TIMEOUT: this.config.apiTimeout.toString(),
      REACT_APP_ENABLE_MOCK: this.config.enableMockData.toString(),
      REACT_APP_ENABLE_ANALYTICS: this.config.enableAnalytics.toString(),
      REACT_APP_PRIMARY_COLOR: this.config.theme.primaryColor,
      REACT_APP_LAYOUT: this.config.theme.layout,
      REACT_APP_FIXED_HEADER: this.config.theme.fixedHeader.toString(),
      REACT_APP_FIXED_SIDER: this.config.theme.fixedSider.toString(),
      REACT_APP_COLOR_WEAK: this.config.theme.colorWeak.toString(),
      REACT_APP_PAGE_SIZE: this.config.pagination.defaultPageSize.toString(),
      REACT_APP_MAX_FILE_SIZE: this.config.upload.maxFileSize.toString(),
      REACT_APP_HASH_ROUTER: this.config.routing.hashRouter.toString(),
    };
  }
}

// 创建配置管理器实例
const configManager = new ConfigManager();

// 导出配置和工具函数
export const config = configManager.getConfig();
export const apiConfig = configManager.getApiConfig();
export const themeConfig = configManager.getThemeConfig();
export const uploadConfig = configManager.getUploadConfig();
export const paginationConfig = configManager.getPaginationConfig();
export const cacheConfig = configManager.getCacheConfig();
export const routingConfig = configManager.getRoutingConfig();

// 导出配置管理器
export { configManager };

// 导出工具函数
export const isDevelopment = () => config.isDevelopment;
export const isProduction = () => config.isProduction;
export const isTesting = () => config.isTesting;
export const getApiUrl = (path: string = '') => `${config.apiBaseUrl}${config.apiVersion}${path}`;
export const getUploadUrl = () => getApiUrl('/upload');
export const getDownloadUrl = (fileId: string) => getApiUrl(`/download/${fileId}`);

// 配置验证
const validation = configManager.validateConfig();
if (!validation.valid) {
  console.error('❌ 配置验证失败:');
  validation.errors.forEach(error => console.error(`  - ${error}`));
}

// 开发环境下输出配置信息
if (config.isDevelopment) {
  console.log('🔧 前端配置信息:', {
    appName: config.appName,
    version: config.version,
    environment: config.environment,
    apiBaseUrl: config.apiBaseUrl,
    apiVersion: config.apiVersion,
  });
}

export default configManager;