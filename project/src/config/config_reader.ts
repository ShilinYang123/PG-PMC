/**
 * 配置读取器
 * 负责读取和管理应用程序配置
 */

interface AppConfig {
  port: number;
  host: string;
  environment: string;
}

/**
 * 获取应用程序配置
 * @returns {AppConfig} 应用程序配置对象
 */
export function getAppConfig(): AppConfig {
  return {
    port: parseInt(process.env.PORT || '3000', 10),
    host: process.env.HOST || 'localhost',
    environment: process.env.NODE_ENV || 'development'
  };
}

/**
 * 验证配置是否有效
 * @param config 配置对象
 * @returns {boolean} 配置是否有效
 */
export function validateConfig(config: AppConfig): boolean {
  return (
    typeof config.port === 'number' &&
    config.port > 0 &&
    config.port < 65536 &&
    typeof config.host === 'string' &&
    config.host.length > 0 &&
    typeof config.environment === 'string'
  );
}

export default {
  getAppConfig,
  validateConfig
};