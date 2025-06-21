/**
 * 应用配置测试
 * 测试 app_config.js 模块的配置加载功能
 */

const fs = require('fs');

// Mock config_reader module
const mockConfigReader = {
  getAppConfig: jest.fn(() => ({
    port: 3000,
    host: 'localhost'
  })),
  getDatabaseConfig: jest.fn(() => ({
    host: 'localhost',
    port: 5432,
    database: 'test_db',
    username: 'test_user',
    password: 'test_pass'
  })),
  getRedisConfig: jest.fn(() => ({
    host: 'localhost',
    port: 6379,
    password: null
  })),
  getJwtConfig: jest.fn(() => ({
    secret: 'test_secret',
    expiresIn: '24h'
  })),
  getEmailConfig: jest.fn(() => ({
    host: 'smtp.test.com',
    port: 587,
    secure: false,
    auth: {
      user: 'test@test.com',
      pass: 'test_pass'
    }
  })),
  getEnvironmentConfig: jest.fn(() => ({
    env: 'development',
    logLevel: 'info'
  })),
  getConfig: jest.fn((key, defaultValue) => {
    const configs = {
      'DB_POOL_MAX': '5',
      'DB_POOL_MIN': '0',
      'DB_POOL_ACQUIRE': '30000',
      'DB_POOL_IDLE': '10000',
      'LOG_FILE': './logs/app.log',
      'LOG_MAX_SIZE': '10m',
      'LOG_MAX_FILES': '14d',
      'CORS_ORIGIN': '*',
      'CORS_CREDENTIALS': 'true'
    };
    return configs[key] || defaultValue;
  })
};

jest.mock('../config/config_reader', () => mockConfigReader);

describe('App Configuration', () => {
  let appConfig;

  beforeEach(() => {
    // 清除模块缓存，重新加载配置
    jest.resetModules();
    appConfig = require('../config/app_config');
  });

  describe('Basic Configuration Structure', () => {
    test('should be an object', () => {
      expect(typeof appConfig).toBe('object');
      expect(appConfig).not.toBeNull();
    });

    test('should contain port configuration', () => {
      expect(appConfig.port).toBeDefined();
      expect(typeof appConfig.port).toBe('number');
      expect(appConfig.port).toBe(3000);
    });

    test('should contain host configuration', () => {
      expect(appConfig.host).toBeDefined();
      expect(typeof appConfig.host).toBe('string');
      expect(appConfig.host).toBe('localhost');
    });
  });

  describe('Database Configuration', () => {
    test('should contain database configuration', () => {
      expect(appConfig.database).toBeDefined();
      expect(typeof appConfig.database).toBe('object');
    });

    test('should have valid database connection settings', () => {
      expect(appConfig.database.host).toBe('localhost');
      expect(appConfig.database.port).toBe(5432);
      expect(appConfig.database.database).toBe('test_db');
      expect(appConfig.database.username).toBe('test_user');
      expect(appConfig.database.password).toBe('test_pass');
    });

    test('should have database pool configuration', () => {
      expect(appConfig.database.pool).toBeDefined();
      expect(appConfig.database.pool.max).toBe(5);
      expect(appConfig.database.pool.min).toBe(0);
      expect(appConfig.database.pool.acquire).toBe(30000);
      expect(appConfig.database.pool.idle).toBe(10000);
    });
  });

  describe('Redis Configuration', () => {
    test('should contain Redis configuration', () => {
      expect(appConfig.redis).toBeDefined();
      expect(typeof appConfig.redis).toBe('object');
    });

    test('should have valid Redis connection settings', () => {
      expect(appConfig.redis.host).toBe('localhost');
      expect(appConfig.redis.port).toBe(6379);
      expect(appConfig.redis.password).toBeNull();
    });
  });

  describe('JWT Configuration', () => {
    test('should contain JWT configuration', () => {
      expect(appConfig.jwt).toBeDefined();
      expect(typeof appConfig.jwt).toBe('object');
    });

    test('should have valid JWT settings', () => {
      expect(appConfig.jwt.secret).toBe('test_secret');
      expect(appConfig.jwt.expiresIn).toBe('24h');
    });
  });

  describe('Email Configuration', () => {
    test('should contain email configuration', () => {
      expect(appConfig.email).toBeDefined();
      expect(typeof appConfig.email).toBe('object');
    });

    test('should have valid email settings', () => {
      expect(appConfig.email.host).toBe('smtp.test.com');
      expect(appConfig.email.port).toBe(587);
      expect(appConfig.email.secure).toBe(false);
      expect(appConfig.email.auth).toBeDefined();
      expect(appConfig.email.auth.user).toBe('test@test.com');
      expect(appConfig.email.auth.pass).toBe('test_pass');
    });
  });

  describe('Environment Configuration', () => {
    test('should contain environment configuration', () => {
      expect(appConfig.environment).toBeDefined();
      expect(typeof appConfig.environment).toBe('object');
    });

    test('should have valid environment settings', () => {
      expect(appConfig.environment.env).toBe('development');
      expect(appConfig.environment.logLevel).toBe('info');
    });
  });

  describe('Logging Configuration', () => {
    test('should contain logging configuration', () => {
      expect(appConfig.logging).toBeDefined();
      expect(typeof appConfig.logging).toBe('object');
    });

    test('should have valid logging settings', () => {
      expect(appConfig.logging.level).toBe('info');
      expect(appConfig.logging.file).toBe('./logs/app.log');
      expect(appConfig.logging.maxSize).toBe('10m');
      expect(appConfig.logging.maxFiles).toBe('14d');
    });
  });

  describe('CORS Configuration', () => {
    test('should contain CORS configuration', () => {
      expect(appConfig.cors).toBeDefined();
      expect(typeof appConfig.cors).toBe('object');
    });

    test('should have valid CORS settings', () => {
      expect(appConfig.cors.origin).toBe('*');
      expect(appConfig.cors.credentials).toBe(true);
    });
  });
});