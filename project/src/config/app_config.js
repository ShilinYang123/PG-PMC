/**
 * 3AI项目应用配置文件
 *
 * 这个文件使用统一配置管理系统，从 docs/03-管理 目录读取配置。
 */

const configReader = require('./config_reader');

// 获取各模块配置
const appConfig = configReader.getAppConfig();
const databaseConfig = configReader.getDatabaseConfig();
const redisConfig = configReader.getRedisConfig();
const jwtConfig = configReader.getJwtConfig();
const emailConfig = configReader.getEmailConfig();
const envConfig = configReader.getEnvironmentConfig();

module.exports = {
  // 服务器配置
  port: appConfig.port,
  host: appConfig.host,

  // 数据库配置
  database: {
    ...databaseConfig,
    pool: {
      max: parseInt(configReader.getConfig('DB_POOL_MAX', 5)),
      min: parseInt(configReader.getConfig('DB_POOL_MIN', 0)),
      acquire: parseInt(configReader.getConfig('DB_POOL_ACQUIRE', 30000)),
      idle: parseInt(configReader.getConfig('DB_POOL_IDLE', 10000)),
    },
  },

  // Redis配置
  redis: redisConfig,

  // 日志配置
  logging: {
    level: envConfig.logLevel.toLowerCase(),
    file: configReader.getConfig('LOG_FILE', './logs/app.log'),
    maxSize: configReader.getConfig('LOG_MAX_SIZE', '10m'),
    maxFiles: configReader.getConfig('LOG_MAX_FILES', '14d'),
  },

  // JWT配置
  jwt: jwtConfig,

  // CORS配置
  cors: {
    origin: configReader.getConfig('CORS_ORIGIN', '*'),
    credentials: configReader.getConfig('CORS_CREDENTIALS', 'true') === 'true',
    optionsSuccessStatus: 200,
  },

  // 文件上传配置
  upload: {
    maxSize: configReader.getConfig('MAX_FILE_SIZE', '10485760'),
    allowedTypes: configReader
      .getConfig('ALLOWED_FILE_TYPES', 'jpg,jpeg,png,gif,pdf')
      .split(','),
    destination: configReader.getConfig('UPLOAD_DIR', './uploads'),
  },

  // API配置
  api: {
    prefix: '/api',
    version: 'v1',
    port: appConfig.api_port,
    url: appConfig.api_url,
    rateLimit: {
      windowMs: parseInt(configReader.getConfig('RATE_LIMIT_WINDOW', 900000)), // 15分钟
      max: parseInt(configReader.getConfig('RATE_LIMIT_MAX', 100)),
    },
  },

  // 安全配置
  security: {
    bcryptRounds: parseInt(configReader.getConfig('BCRYPT_ROUNDS', 12)),
    sessionSecret: configReader.getConfig('SESSION_SECRET', jwtConfig.secret),
    cookieMaxAge: parseInt(configReader.getConfig('SESSION_MAX_AGE', 86400000)),
  },

  // 邮件配置
  email: emailConfig,

  // 第三方服务配置
  services: {
    // AI服务配置
    ai: {
      apiKey: configReader.getConfig('AI_API_KEY'),
      baseUrl: configReader.getConfig(
        'AI_BASE_URL',
        'https://api.openai.com/v1'
      ),
      model: configReader.getConfig('AI_MODEL', 'gpt-3.5-turbo'),
      maxTokens: parseInt(configReader.getConfig('AI_MAX_TOKENS', 2000)),
    },

    // 云存储配置
    storage: {
      provider: configReader.getConfig('STORAGE_PROVIDER', 'local'),
      bucket: configReader.getConfig('STORAGE_BUCKET'),
      region: configReader.getConfig('STORAGE_REGION'),
      accessKey: configReader.getConfig('STORAGE_ACCESS_KEY'),
      secretKey: configReader.getConfig('STORAGE_SECRET_KEY'),
    },
  },

  // 环境配置
  environment: envConfig,

  // SSL配置
  ssl: {
    enabled: configReader.getConfig('SSL_ENABLED', 'false') === 'true',
    cert: configReader.getConfig('SSL_CERT'),
    key: configReader.getConfig('SSL_KEY'),
  },
};
