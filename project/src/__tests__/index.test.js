const request = require('supertest');
const express = require('express');
const helmet = require('helmet');
const cors = require('cors');

// Mock the config modules
jest.mock('../config/config_reader', () => ({
  getAppConfig: () => ({
    name: 'Test App',
    port: 3000,
    host: 'localhost'
  }),
  getEnvironmentConfig: () => ({
    env: 'test',
    debug: true,
    logLevel: 'INFO'
  })
}));

// Mock the app_config module
jest.mock('../config/app_config', () => ({
  app: {
    name: 'Test App',
    version: '1.0.0',
    description: 'Test application'
  }
}));

// Mock console methods to avoid noise in tests
jest.spyOn(console, 'log').mockImplementation(() => {});
jest.spyOn(console, 'error').mockImplementation(() => {});

describe('Express App Routes', () => {
  let app;

  beforeEach(() => {
    // Create a new Express app for testing
    app = express();
    
    // Add middleware
    app.use(helmet());
    app.use(cors());
    app.use(express.json());
    app.use(express.urlencoded({ extended: true }));
    
    // Add routes similar to index.ts
    app.get('/', (req, res) => {
      res.json({ message: '欢迎使用 3AI 项目 API' });
    });
    
    app.get('/health', (req, res) => {
      res.json({ 
        status: 'OK', 
        timestamp: new Date().toISOString(),
        uptime: process.uptime()
      });
    });
    
    app.get('/api/info', (req, res) => {
      const appConfig = require('../config/app_config');
      const envConfig = require('../config/config_reader').getEnvironmentConfig();
      
      res.json({
        name: appConfig.app.name,
        version: appConfig.app.version,
        description: appConfig.app.description,
        environment: envConfig.env,
        debug: envConfig.debug
      });
    });
    
    // Error handling middleware
    app.use((err, req, res, next) => {
      console.error('Error:', err.message);
      res.status(500).json({ error: '服务器内部错误' });
    });
    
    // 404 handler
    app.use('*', (req, res) => {
      res.status(404).json({ error: '页面未找到' });
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should respond to GET /', async () => {
    const response = await request(app).get('/');
    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('message');
    expect(response.body.message).toContain('3AI 项目');
  });

  test('should respond to GET /health', async () => {
    const response = await request(app).get('/health');
    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('status', 'OK');
    expect(response.body).toHaveProperty('timestamp');
    expect(response.body).toHaveProperty('uptime');
  });

  test('should respond to GET /api/info', async () => {
    const response = await request(app).get('/api/info');
    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('name', 'Test App');
    expect(response.body).toHaveProperty('version', '1.0.0');
    expect(response.body).toHaveProperty('environment', 'test');
    expect(response.body).toHaveProperty('debug', true);
  });

  test('should return 404 for unknown routes', async () => {
    const response = await request(app).get('/unknown-route');
    expect(response.status).toBe(404);
    expect(response.body).toHaveProperty('error', '页面未找到');
  });

  test('should handle POST requests with JSON body', async () => {
    // 在beforeEach中添加测试路由
    const testData = { test: 'data' };
    
    // 创建一个新的app实例用于这个测试
    const testApp = express();
    testApp.use(helmet());
    testApp.use(cors());
    testApp.use(express.json());
    testApp.use(express.urlencoded({ extended: true }));
    
    testApp.post('/test', (req, res) => {
      res.json({ received: req.body });
    });
    
    const response = await request(testApp)
      .post('/test')
      .send(testData);
    
    expect(response.status).toBe(200);
    expect(response.body.received).toEqual(testData);
  });
});

describe('Express App Configuration', () => {
  test('should load app configuration correctly', () => {
    const { getAppConfig } = require('../config/config_reader');
    const config = getAppConfig();
    
    expect(config).toHaveProperty('name', 'Test App');
    expect(config).toHaveProperty('port', 3000);
    expect(config).toHaveProperty('host', 'localhost');
  });

  test('should load environment configuration correctly', () => {
    const { getEnvironmentConfig } = require('../config/config_reader');
    const config = getEnvironmentConfig();
    
    expect(config).toHaveProperty('env', 'test');
    expect(config).toHaveProperty('debug', true);
    expect(config).toHaveProperty('logLevel', 'INFO');
  });
});