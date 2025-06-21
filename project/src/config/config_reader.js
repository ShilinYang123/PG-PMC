/**
 * 配置读取工具
 * 从统一配置管理目录读取配置信息
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// 配置文件路径
const CONFIG_DIR = path.join(__dirname, '../../docs/03-管理');
const PROJECT_CONFIG_PATH = path.join(CONFIG_DIR, 'project_config.yaml');
const ENV_PATH = path.join(CONFIG_DIR, '.env');

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
 * @returns {Object} 环境变量配置对象
 */
function loadEnvConfig() {
  if (_envConfig) {
    return _envConfig;
  }

  _envConfig = {};

  try {
    if (fs.existsSync(ENV_PATH)) {
      const envContent = fs.readFileSync(ENV_PATH, 'utf8');
      const lines = envContent.split('\n');

      for (const line of lines) {
        const trimmedLine = line.trim();
        if (
          trimmedLine &&
          !trimmedLine.startsWith('#') &&
          trimmedLine.includes('=')
        ) {
          const [key, ...valueParts] = trimmedLine.split('=');
          const value = valueParts.join('=').replace(/^["']|["']$/g, '');
          _envConfig[key.trim()] = value;
        }
      }
    }
  } catch (error) {
    console.warn('无法加载环境配置文件:', error.message);
  }

  return _envConfig;
}

/**
 * 获取配置值，优先级：环境变量 > 统一配置文件 > 默认值
 * @param {string} key 配置键
 * @param {*} defaultValue 默认值
 * @returns {*} 配置值
 */
function getConfig(key, defaultValue = null) {
  // 优先使用环境变量
  if (process.env[key] !== undefined) {
    return process.env[key];
  }

  // 其次使用统一配置文件中的环境变量
  const envConfig = loadEnvConfig();
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
function getDatabaseConfig(env = 'development') {
  const projectConfig = loadProjectConfig();
  const dbConfig = projectConfig.database || {};

  let dbName;
  switch (env) {
  case 'test':
    dbName =
        dbConfig.test_name || `${projectConfig.project_name || '3AI'}_test_db`;
    break;
  case 'development':
    dbName =
        dbConfig.dev_name || `${projectConfig.project_name || '3AI'}_dev_db`;
    break;
  default:
    dbName = dbConfig.name || `${projectConfig.project_name || '3AI'}_db`;
  }

  return {
    host: getConfig('DB_HOST', dbConfig.host || 'localhost'),
    port: parseInt(getConfig('DB_PORT', dbConfig.port || 5432)),
    name: getConfig('DB_NAME', dbName),
    username: getConfig('DB_USER', dbConfig.username || 'postgres'),
    password: getConfig('DB_PASSWORD', dbConfig.password || 'password'),
    dialect: 'postgres',
  };
}

/**
 * 获取应用配置
 * @returns {Object} 应用配置
 */
function getAppConfig() {
  const projectConfig = loadProjectConfig();
  const appConfig = projectConfig.app || {};

  return {
    name: getConfig('APP_NAME', projectConfig.project_name || '3AI'),
    version: getConfig('APP_VERSION', projectConfig.project_version || '1.0.0'),
    port: parseInt(getConfig('PORT', appConfig.port || 3000)),
    host: getConfig('HOST', 'localhost'),
    url: getConfig(
      'APP_URL',
      appConfig.url || `http://localhost:${getConfig('PORT', 3000)}`
    ),
    api_port: parseInt(getConfig('API_PORT', appConfig.api_port || 8000)),
    api_url: getConfig(
      'API_URL',
      appConfig.api_url || `http://localhost:${getConfig('API_PORT', 8000)}`
    ),
  };
}

/**
 * 获取Redis配置
 * @returns {Object} Redis配置
 */
function getRedisConfig() {
  return {
    host: getConfig('REDIS_HOST', 'localhost'),
    port: parseInt(getConfig('REDIS_PORT', 6379)),
    password: getConfig('REDIS_PASSWORD', null),
    db: parseInt(getConfig('REDIS_DB', 0)),
  };
}

/**
 * 获取JWT配置
 * @returns {Object} JWT配置
 */
function getJwtConfig() {
  return {
    secret: getConfig('JWT_SECRET', '3ai-secret-key'),
    expiresIn: getConfig('JWT_EXPIRES_IN', '24h'),
    refreshExpiresIn: getConfig('JWT_REFRESH_EXPIRES_IN', '7d'),
  };
}

/**
 * 获取邮件配置
 * @returns {Object} 邮件配置
 */
function getEmailConfig() {
  return {
    host: getConfig('SMTP_HOST', 'smtp.gmail.com'),
    port: parseInt(getConfig('SMTP_PORT', 587)),
    secure: getConfig('SMTP_SECURE', 'false') === 'true',
    auth: {
      user: getConfig('SMTP_USER'),
      pass: getConfig('SMTP_PASS'),
    },
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
