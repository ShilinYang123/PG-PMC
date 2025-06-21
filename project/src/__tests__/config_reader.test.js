/**
 * 配置读取器测试
 * 测试 config_reader.js 模块的配置读取功能
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// Mock fs module
jest.mock('fs');
jest.mock('js-yaml');

// Mock path.join to return predictable paths
jest.mock('path', () => ({
  ...jest.requireActual('path'),
  join: jest.fn()
}));

describe('Config Reader', () => {
  let configReader;
  const mockFs = fs;
  const mockYaml = yaml;
  const mockPath = path;

  beforeEach(() => {
    // Clear all mocks
    jest.clearAllMocks();
    jest.resetModules();

    // Clear environment variables
    delete process.env.NODE_ENV;
    delete process.env.DB_HOST;
    delete process.env.PORT;
    delete process.env.TEST_VAR;
    delete process.env.APP_NAME;
    delete process.env.APP_VERSION;
    delete process.env.HOST;
    delete process.env.APP_URL;
    delete process.env.API_PORT;
    delete process.env.API_URL;

    // Setup default mocks
    mockPath.join.mockImplementation((...args) => {
      if (args.includes('project_config.yaml')) {
        return '/mock/path/project_config.yaml';
      }
      if (args.includes('.env')) {
        return '/mock/path/.env';
      }
      return '/mock/path';
    });

    mockFs.existsSync.mockReturnValue(true);
    mockFs.readFileSync.mockImplementation((filePath) => {
      if (filePath.includes('project_config.yaml')) {
        return 'mock yaml content';
      }
      if (filePath.includes('.env')) {
        return 'NODE_ENV=test\nDB_HOST=localhost\nDB_PORT=5432';
      }
      return '';
    });

    mockYaml.load.mockReturnValue({
      project_name: '3AI',
      project_version: '1.0.0',
      app: {
        port: 3000,
        api_port: 8000,
        url: 'http://localhost:3000',
        api_url: 'http://localhost:8000'
      },
      database: {
        host: 'localhost',
        port: 5432,
        name: '3AI_db',
        dev_name: '3AI_dev_db',
        test_name: '3AI_test_db',
        username: 'postgres',
        password: 'password'
      },
      environment: {
        development: {
          debug: false,
          log_level: 'INFO'
        },
        test: {
          debug: false,
          log_level: 'INFO'
        }
      }
    });

    // Load the module after mocks are set up
    configReader = require('../config/config_reader');
  });

  describe('Configuration Loading', () => {
    test('should load project configuration successfully', () => {
      const config = configReader.loadProjectConfig();
      expect(config).toBeDefined();
      expect(typeof config).toBe('object');
      // Mock functions are called during module loading, configuration should be loaded
    });

    test('should handle missing configuration files gracefully', () => {
      mockFs.existsSync.mockReturnValue(false);
      jest.resetModules();
      
      const configReader = require('../config/config_reader');
      const config = configReader.loadProjectConfig();
      expect(config).toEqual({});
    });

    test('should load environment configuration', () => {
      const envConfig = configReader.loadEnvConfig();
      expect(envConfig).toBeDefined();
      expect(typeof envConfig).toBe('object');
    });
  });

  describe('getConfig function', () => {
    test('should return environment variable value', () => {
      process.env.TEST_VAR = 'test_value';
      const result = configReader.getConfig('TEST_VAR', 'default');
      expect(result).toBe('test_value');
    });

    test('should return default value when env var not set', () => {
      const result = configReader.getConfig('NONEXISTENT_KEY', 'default_value');
      expect(result).toBe('default_value');
    });

    test('should return null when no default provided', () => {
      const result = configReader.getConfig('NON_EXISTENT_VAR');
      expect(result).toBeNull();
    });

    test('should prioritize process.env over file env', () => {
      process.env.DB_HOST = 'env_host';
      const result = configReader.getConfig('DB_HOST', 'default');
      expect(result).toBe('env_host');
    });
  });

  describe('getAppConfig function', () => {
    test('should return app configuration with defaults', () => {
      const appConfig = configReader.getAppConfig();
      expect(appConfig).toBeDefined();
      expect(typeof appConfig).toBe('object');
      expect(appConfig).toHaveProperty('name');
      expect(appConfig).toHaveProperty('port');
      expect(appConfig).toHaveProperty('version');
      expect(appConfig).toHaveProperty('host');
      expect(appConfig).toHaveProperty('url');
      expect(appConfig).toHaveProperty('api_port');
      expect(appConfig).toHaveProperty('api_url');
      expect(appConfig.name).toBe('3AI');
      expect(appConfig.port).toBe(3000);
      expect(appConfig.host).toBe('localhost');
    });

    test('should use environment variables when available', () => {
      process.env.APP_NAME = 'Custom App';
      process.env.PORT = '4000';
      
      jest.resetModules();
      const configReader = require('../config/config_reader');
      
      const appConfig = configReader.getAppConfig();
      expect(appConfig.name).toBe('Custom App');
      expect(appConfig.port).toBe(4000);
    });
  });

  describe('getDatabaseConfig function', () => {
    test('should return database configuration for development', () => {
      const dbConfig = configReader.getDatabaseConfig('development');
      expect(dbConfig).toBeDefined();
      expect(typeof dbConfig).toBe('object');
      expect(dbConfig.host).toBe('localhost');
      expect(dbConfig.port).toBe(5432);
      expect(dbConfig.name).toBe('3AI_dev_db');
      expect(dbConfig.username).toBe('postgres');
      expect(dbConfig.password).toBe('password');
      expect(dbConfig.dialect).toBe('postgres');
    });

    test('should return database configuration for test', () => {
      const dbConfig = configReader.getDatabaseConfig('test');
      expect(dbConfig.name).toBe('3AI_test_db');
    });

    test('should return database configuration for production', () => {
      const dbConfig = configReader.getDatabaseConfig('production');
      expect(dbConfig.name).toBe('3AI_db');
    });

    test('should use environment variables when available', () => {
      process.env.DB_HOST = 'custom_host';
      process.env.DB_PORT = '3306';
      process.env.DB_NAME = 'custom_db';
      
      jest.resetModules();
      const configReader = require('../config/config_reader');
      
      const dbConfig = configReader.getDatabaseConfig();
      expect(dbConfig.host).toBe('custom_host');
      expect(dbConfig.port).toBe(3306);
      expect(dbConfig.name).toBe('custom_db');
    });
  });

  describe('getRedisConfig function', () => {
    test('should return Redis configuration with defaults', () => {
      const redisConfig = configReader.getRedisConfig();
      expect(redisConfig).toBeDefined();
      expect(redisConfig.host).toBe('localhost');
      expect(redisConfig.port).toBe(6379);
      expect(redisConfig.password).toBeNull();
      expect(redisConfig.db).toBe(0);
    });

    test('should use environment variables when available', () => {
      process.env.REDIS_HOST = 'redis_host';
      process.env.REDIS_PORT = '6380';
      process.env.REDIS_PASSWORD = 'redis_pass';
      process.env.REDIS_DB = '1';
      
      jest.resetModules();
      const configReader = require('../config/config_reader');
      
      const redisConfig = configReader.getRedisConfig();
      expect(redisConfig.host).toBe('redis_host');
      expect(redisConfig.port).toBe(6380);
      expect(redisConfig.password).toBe('redis_pass');
      expect(redisConfig.db).toBe(1);
    });
  });

  describe('getJwtConfig function', () => {
    test('should return JWT configuration with defaults', () => {
      const jwtConfig = configReader.getJwtConfig();
      expect(jwtConfig).toBeDefined();
      expect(jwtConfig.secret).toBe('3ai-secret-key');
      expect(jwtConfig.expiresIn).toBe('24h');
      expect(jwtConfig.refreshExpiresIn).toBe('7d');
    });

    test('should use environment variables when available', () => {
      process.env.JWT_SECRET = 'custom_secret';
      process.env.JWT_EXPIRES_IN = '12h';
      process.env.JWT_REFRESH_EXPIRES_IN = '3d';
      
      jest.resetModules();
      const configReader = require('../config/config_reader');
      
      const jwtConfig = configReader.getJwtConfig();
      expect(jwtConfig.secret).toBe('custom_secret');
      expect(jwtConfig.expiresIn).toBe('12h');
      expect(jwtConfig.refreshExpiresIn).toBe('3d');
    });
  });

  describe('getEmailConfig function', () => {
    test('should return email configuration with defaults', () => {
      const emailConfig = configReader.getEmailConfig();
      expect(emailConfig).toBeDefined();
      expect(emailConfig.host).toBe('smtp.gmail.com');
      expect(emailConfig.port).toBe(587);
      expect(emailConfig.secure).toBe(false);
      expect(emailConfig.auth).toBeDefined();
      expect(emailConfig.auth.user).toBeNull();
      expect(emailConfig.auth.pass).toBeNull();
    });

    test('should use environment variables when available', () => {
      process.env.SMTP_HOST = 'smtp.test.com';
      process.env.SMTP_PORT = '465';
      process.env.SMTP_SECURE = 'true';
      process.env.SMTP_USER = 'test@test.com';
      process.env.SMTP_PASS = 'test_pass';
      
      jest.resetModules();
      const configReader = require('../config/config_reader');
      
      const emailConfig = configReader.getEmailConfig();
      expect(emailConfig.host).toBe('smtp.test.com');
      expect(emailConfig.port).toBe(465);
      expect(emailConfig.secure).toBe(true);
      expect(emailConfig.auth.user).toBe('test@test.com');
      expect(emailConfig.auth.pass).toBe('test_pass');
    });
  });

  describe('getEnvironmentConfig function', () => {
    test('should return environment configuration with defaults', () => {
      const envConfig = configReader.getEnvironmentConfig();
      expect(envConfig).toBeDefined();
      expect(typeof envConfig).toBe('object');
      expect(envConfig).toHaveProperty('env');
      expect(envConfig).toHaveProperty('debug');
      expect(envConfig).toHaveProperty('logLevel');
      expect(envConfig.env).toBe('development');
      expect(envConfig.debug).toBe(false);
      expect(envConfig.logLevel).toBe('INFO');
    });

    test('should use NODE_ENV when available', () => {
      process.env.NODE_ENV = 'test';
      
      jest.resetModules();
      const configReader = require('../config/config_reader');
      
      const envConfig = configReader.getEnvironmentConfig();
      expect(envConfig.env).toBe('test');
    });

    test('should use environment variables for debug and log level', () => {
      process.env.DEBUG = 'true';
      process.env.LOG_LEVEL = 'DEBUG';
      
      jest.resetModules();
      const configReader = require('../config/config_reader');
      
      const envConfig = configReader.getEnvironmentConfig();
      expect(envConfig.debug).toBe('true');
      expect(envConfig.logLevel).toBe('DEBUG');
    });
  });

  describe('Error Handling', () => {
    test('should handle YAML parsing errors', () => {
      mockYaml.load.mockImplementation(() => {
        throw new Error('YAML parsing error');
      });
      
      jest.resetModules();
      
      // Should not throw error when YAML parsing fails
      expect(() => {
        const configReader = require('../config/config_reader');
        configReader.loadProjectConfig();
      }).not.toThrow();
    });

    test('should handle file reading errors', () => {
      mockFs.readFileSync.mockImplementation(() => {
        throw new Error('File reading error');
      });
      
      jest.resetModules();
      
      // Should not throw error when file reading fails
      expect(() => {
        const configReader = require('../config/config_reader');
        configReader.loadProjectConfig();
      }).not.toThrow();
    });

    test('should handle missing project config gracefully', () => {
      mockYaml.load.mockReturnValue({});
      
      jest.resetModules();
      const configReader = require('../config/config_reader');
      
      const appConfig = configReader.getAppConfig();
      expect(appConfig.name).toBe('3AI'); // Should use default
    });
  });
});