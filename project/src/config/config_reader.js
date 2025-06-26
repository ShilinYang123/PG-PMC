/**
 * 配置读取工具
 * 从统一配置管理目录读取配置信息
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// 配置文件路径
const CONFIG_DIR = path.join(__dirname, '../../../docs/03-管理');
const PROJECT_CONFIG_PATH = path.join(CONFIG_DIR, 'project_config.yaml');

// 缓存配置
let _projectConfig = null;
let _envConfig = null;

/**
 * 加载项目配置文件
 * @returns {Object} 项目配置对象
 */
function loadProjectConfig() {
  if (_projectConfig) {
    return _projectConfig;
  }

  try {
    if (fs.existsSync(PROJECT_CONFIG_PATH)) {
      const configContent = fs.readFileSync(PROJECT_CONFIG_PATH, 'utf8');
      _projectConfig = yaml.load(configContent);
      return _projectConfig;
    }
  } catch (error) {
    console.warn('无法加载项目配置文件:', error.message);
  }

  return {};
}

/**
 * 加载环境变量配置
 * @param {string} env 环境名称 (development, production, test)
 * @returns {Object} 环境变量配置对象
 */
function loadEnvConfig(env = 'development') {
  if (_envConfig) {
    return _envConfig;
  }

  _envConfig = {};

  try {
    const projectConfig = loadProjectConfig();
    const environmentConfig = projectConfig.environment || {};
    
    // 合并通用配置和环境特定配置
    const commonConfigs = ['app', 'database', 'redis', 'security', 'storage', 'mail', 'logging', 'external_services', 'monitoring', 'cache', 'rate_limit'];
    
    // 加载通用配置
    for (const configType of commonConfigs) {
      if (environmentConfig[configType]) {
        Object.assign(_envConfig, flattenConfig(environmentConfig[configType], configType.toUpperCase()));
      }
    }
    
    // 加载环境特定配置
    if (environmentConfig[env]) {
      Object.assign(_envConfig, flattenConfig(environmentConfig[env], ''));
    }
    
  } catch (error) {
    console.warn('无法加载环境配置:', error.message);
  }

  return _envConfig;
}

/**
 * 将嵌套配置对象扁平化为环境变量格式
 * @param {Object} config 配置对象
 * @param {string} prefix 前缀
 * @returns {Object} 扁平化的配置对象
 */
function flattenConfig(config, prefix = '') {
  const result = {};
  
  for (const [key, value] of Object.entries(config)) {
    const envKey = prefix ? `${prefix}_${key.toUpperCase()}` : key.toUpperCase();
    
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      Object.assign(result, flattenConfig(value, envKey));
    } else {
      result[envKey] = value;
    }
  }
  
  return result;
}

/**
 * 获取配置值，优先级：环境变量 > 统一配置文件 > 默认值
 * @param {string} key 配置键
 * @param {*} defaultValue 默认值
 * @param {string} env 环境名称
 * @returns {*} 配置值
 */
function getConfig(key, defaultValue = null, env = process.env.NODE_ENV || 'development') {
  // 优先使用环境变量
  if (process.env[key] !== undefined) {
    return process.env[key];
  }

  // 其次使用统一配置文件中的环境变量
  const envConfig = loadEnvConfig(env);
  if (envConfig[key] !== undefined) {
    return envConfig[key];
  }

  // 最后返回默认值
  return defaultValue;
}

/**
 * 获取数据库配置
 * @param {string} env 环境名称
 * @returns {Object} 数据库配置
 */
function getDatabaseConfig(env = process.env.NODE_ENV || 'development') {
  const projectConfig = loadProjectConfig();
  const dbConfig = projectConfig.environment?.database || {};
  const networkConfig = projectConfig.environment?.network || {};
  const defaultHost = networkConfig.host || 'localhost';

  let dbUrl;
  switch (env) {
  case 'test':
    dbUrl = dbConfig.test_url || `postgresql://postgres:password@${defaultHost}:5432/3AI_test_db`;
    break;
  default:
    dbUrl = dbConfig.url || `postgresql://postgres:password@${defaultHost}:5432/3AI_db`;
  }

  return {
    host: getConfig('DATABASE_HOST', dbConfig.host || defaultHost, env),
    port: parseInt(getConfig('DATABASE_PORT', dbConfig.port || 5432, env)),
    name: getConfig('DATABASE_NAME', dbConfig.name || '3AI_db', env),
    username: getConfig('DATABASE_USER', dbConfig.user || 'postgres', env),
    password: getConfig('DATABASE_PASSWORD', dbConfig.password || 'password', env),
    url: getConfig('DATABASE_URL', dbUrl, env),
    dialect: 'postgres',
  };
}

/**
 * 获取应用配置
 * @param {string} env 环境名称
 * @returns {Object} 应用配置
 */
function getAppConfig(env = process.env.NODE_ENV || 'development') {
  const projectConfig = loadProjectConfig();
  const appConfig = projectConfig.environment?.app || {};
  const networkConfig = projectConfig.environment?.network || {};
  const defaultHost = networkConfig.host || 'localhost';
  const defaultPort = networkConfig.default_ports?.frontend || 3000;
  const defaultApiPort = networkConfig.default_ports?.api || 8000;

  return {
    name: getConfig('APP_NAME', appConfig.name || '3AI', env),
    version: getConfig('APP_VERSION', appConfig.version || '1.0.0', env),
    port: parseInt(getConfig('PORT', appConfig.port || defaultPort, env)),
    host: getConfig('HOST', appConfig.host || defaultHost, env),
    url: getConfig('APP_URL', appConfig.url || `http://${defaultHost}:${getConfig('PORT', defaultPort, env)}`, env),
    api_port: parseInt(getConfig('API_PORT', appConfig.api_port || defaultApiPort, env)),
    api_url: getConfig('API_URL', appConfig.api_url || `http://${defaultHost}:${getConfig('API_PORT', defaultApiPort, env)}`, env),
  };
}

/**
 * 获取Redis配置
 * @param {string} env 环境名称
 * @returns {Object} Redis配置
 */
function getRedisConfig(env = process.env.NODE_ENV || 'development') {
  const projectConfig = loadProjectConfig();
  const redisConfig = projectConfig.environment?.redis || {};
  const networkConfig = projectConfig.environment?.network || {};
  const defaultHost = networkConfig.host || 'localhost';

  return {
    host: getConfig('REDIS_HOST', redisConfig.host || defaultHost, env),
    port: parseInt(getConfig('REDIS_PORT', redisConfig.port || 6379, env)),
    password: getConfig('REDIS_PASSWORD', redisConfig.password || null, env),
    db: parseInt(getConfig('REDIS_DB', redisConfig.db || 0, env)),
    url: getConfig('REDIS_URL', redisConfig.url || null, env),
  };
}

/**
 * 获取JWT配置
 * @param {string} env 环境名称
 * @returns {Object} JWT配置
 */
function getJwtConfig(env = process.env.NODE_ENV || 'development') {
  const projectConfig = loadProjectConfig();
  const jwtConfig = projectConfig.environment?.security?.jwt || {};

  return {
    secret: getConfig('JWT_SECRET', jwtConfig.secret || '3ai-secret-key', env),
    expiresIn: getConfig('JWT_EXPIRES_IN', jwtConfig.expires_in || '24h', env),
    refreshExpiresIn: getConfig('JWT_REFRESH_EXPIRES_IN', jwtConfig.refresh_expires_in || '7d', env),
  };
}

/**
 * 获取邮件配置
 * @param {string} env 环境名称
 * @returns {Object} 邮件配置
 */
function getEmailConfig(env = process.env.NODE_ENV || 'development') {
  const projectConfig = loadProjectConfig();
  const emailConfig = projectConfig.environment?.email || {};

  return {
    host: getConfig('SMTP_HOST', emailConfig.smtp_host || 'smtp.gmail.com', env),
    port: parseInt(getConfig('SMTP_PORT', emailConfig.smtp_port || 587, env)),
    secure: getConfig('SMTP_SECURE', emailConfig.smtp_secure || 'false', env) === 'true',
    auth: {
      user: getConfig('SMTP_USER', emailConfig.smtp_user || null, env),
      pass: getConfig('SMTP_PASS', emailConfig.smtp_pass || null, env),
    },
    from: getConfig('EMAIL_FROM', emailConfig.from || null, env),
  };
}

/**
 * 获取环境配置
 * @returns {Object} 环境配置
 */
function getEnvironmentConfig() {
  const projectConfig = loadProjectConfig();
  const env = getConfig('NODE_ENV', 'development');
  const envConfig = projectConfig.environment?.[env] || {};

  return {
    env,
    debug: getConfig('DEBUG', envConfig.debug || false),
    logLevel: getConfig('LOG_LEVEL', envConfig.log_level || 'INFO'),
  };
}

module.exports = {
  getConfig,
  getDatabaseConfig,
  getAppConfig,
  getRedisConfig,
  getJwtConfig,
  getEmailConfig,
  getEnvironmentConfig,
  loadProjectConfig,
  loadEnvConfig,
};
