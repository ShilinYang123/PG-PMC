/**
 * 测试代码示例库 - 3AI工作室
 * 提供常用的测试代码模板，包括单元测试、集成测试、端到端测试等
 */

// ================================
// Jest 单元测试示例
// ================================

const { describe, test, expect, beforeEach, afterEach, beforeAll, afterAll, jest } = require('@jest/globals');
const request = require('supertest');
const mongoose = require('mongoose');

// 测试工具函数
class TestUtils {
  // 生成测试数据
  static generateUser(overrides = {}) {
    return {
      username: 'testuser',
      email: 'test@example.com',
      password: 'password123',
      role: 'user',
      profile: {
        firstName: 'Test',
        lastName: 'User',
        bio: 'Test user bio'
      },
      ...overrides
    };
  }

  static generateArticle(overrides = {}) {
    return {
      title: 'Test Article',
      content: 'This is a test article content',
      excerpt: 'Test excerpt',
      category: 'technology',
      tags: ['test', 'article'],
      status: 'published',
      ...overrides
    };
  }

  // 数据库清理
  static async clearDatabase() {
    const collections = mongoose.connection.collections;
    for (const key in collections) {
      const collection = collections[key];
      await collection.deleteMany({});
    }
  }

  // 创建测试用户
  static async createTestUser(userData = {}) {
    const User = require('../models/User');
    const user = new User(this.generateUser(userData));
    await user.save();
    return user;
  }

  // 生成JWT令牌
  static generateToken(user) {
    return user.generateJWT();
  }

  // 模拟请求
  static mockRequest(overrides = {}) {
    return {
      body: {},
      params: {},
      query: {},
      headers: {},
      user: null,
      ...overrides
    };
  }

  static mockResponse() {
    const res = {};
    res.status = jest.fn().mockReturnValue(res);
    res.json = jest.fn().mockReturnValue(res);
    res.send = jest.fn().mockReturnValue(res);
    res.cookie = jest.fn().mockReturnValue(res);
    res.clearCookie = jest.fn().mockReturnValue(res);
    return res;
  }

  static mockNext() {
    return jest.fn();
  }
}

// ================================
// 单元测试示例 - 工具函数测试
// ================================

describe('Utils', () => {
  const Utils = require('../utils/Utils');

  describe('validateEmail', () => {
    test('should return true for valid email', () => {
      expect(Utils.validateEmail('test@example.com')).toBe(true);
      expect(Utils.validateEmail('user.name+tag@domain.co.uk')).toBe(true);
    });

    test('should return false for invalid email', () => {
      expect(Utils.validateEmail('invalid-email')).toBe(false);
      expect(Utils.validateEmail('test@')).toBe(false);
      expect(Utils.validateEmail('@example.com')).toBe(false);
      expect(Utils.validateEmail('')).toBe(false);
    });
  });

  describe('slugify', () => {
    test('should convert text to slug', () => {
      expect(Utils.slugify('Hello World')).toBe('hello-world');
      expect(Utils.slugify('Test Article Title!')).toBe('test-article-title');
      expect(Utils.slugify('  Multiple   Spaces  ')).toBe('multiple-spaces');
    });

    test('should handle special characters', () => {
      expect(Utils.slugify('Test@#$%^&*()Title')).toBe('test-title');
      expect(Utils.slugify('中文标题')).toBe('');
    });
  });

  describe('formatDate', () => {
    test('should format date correctly', () => {
      const date = new Date('2023-12-25T10:30:00Z');
      expect(Utils.formatDate(date)).toBe('2023-12-25');
      expect(Utils.formatDate(date, 'DD/MM/YYYY')).toBe('25/12/2023');
    });
  });

  describe('paginate', () => {
    test('should calculate pagination correctly', () => {
      const result = Utils.paginate(2, 10, 25);
      expect(result).toEqual({
        page: 2,
        limit: 10,
        total: 25,
        pages: 3,
        hasNext: true,
        hasPrev: true,
        nextPage: 3,
        prevPage: 1
      });
    });

    test('should handle first page', () => {
      const result = Utils.paginate(1, 10, 25);
      expect(result.hasPrev).toBe(false);
      expect(result.prevPage).toBe(null);
    });

    test('should handle last page', () => {
      const result = Utils.paginate(3, 10, 25);
      expect(result.hasNext).toBe(false);
      expect(result.nextPage).toBe(null);
    });
  });
});

// ================================
// 单元测试示例 - 服务层测试
// ================================

describe('UserService', () => {
  let userService;
  let mockCacheService;

  beforeEach(() => {
    // 模拟缓存服务
    mockCacheService = {
      get: jest.fn(),
      set: jest.fn(),
      del: jest.fn()
    };

    const UserService = require('../services/UserService');
    userService = new UserService(mockCacheService);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('createUser', () => {
    test('should create user successfully', async () => {
      const userData = TestUtils.generateUser();
      
      // 模拟数据库查询
      const User = require('../models/User');
      jest.spyOn(User, 'findOne').mockResolvedValue(null);
      jest.spyOn(User.prototype, 'save').mockResolvedValue(userData);

      const result = await userService.createUser(userData);

      expect(User.findOne).toHaveBeenCalledWith({
        $or: [{ email: userData.email }, { username: userData.username }]
      });
      expect(result).toEqual(userData);
    });

    test('should throw error if user already exists', async () => {
      const userData = TestUtils.generateUser();
      const existingUser = { _id: '123', ...userData };
      
      const User = require('../models/User');
      jest.spyOn(User, 'findOne').mockResolvedValue(existingUser);

      await expect(userService.createUser(userData))
        .rejects
        .toThrow('User already exists');
    });
  });

  describe('getUserById', () => {
    test('should return cached user if available', async () => {
      const userId = '507f1f77bcf86cd799439011';
      const cachedUser = { _id: userId, username: 'testuser' };
      
      mockCacheService.get.mockResolvedValue(cachedUser);

      const result = await userService.getUserById(userId);

      expect(mockCacheService.get).toHaveBeenCalledWith(`user:${userId}`);
      expect(result).toEqual(cachedUser);
    });

    test('should fetch from database if not cached', async () => {
      const userId = '507f1f77bcf86cd799439011';
      const dbUser = { _id: userId, username: 'testuser' };
      
      mockCacheService.get.mockResolvedValue(null);
      
      const User = require('../models/User');
      jest.spyOn(User, 'findById').mockResolvedValue(dbUser);

      const result = await userService.getUserById(userId);

      expect(User.findById).toHaveBeenCalledWith(userId);
      expect(mockCacheService.set).toHaveBeenCalledWith(`user:${userId}`, dbUser, 1800);
      expect(result).toEqual(dbUser);
    });

    test('should throw error if user not found', async () => {
      const userId = '507f1f77bcf86cd799439011';
      
      mockCacheService.get.mockResolvedValue(null);
      
      const User = require('../models/User');
      jest.spyOn(User, 'findById').mockResolvedValue(null);

      await expect(userService.getUserById(userId))
        .rejects
        .toThrow('User not found');
    });
  });
});

// ================================
// 单元测试示例 - 控制器测试
// ================================

describe('AuthController', () => {
  let authController;
  let mockUserService;
  let mockEmailService;

  beforeEach(() => {
    mockUserService = {
      createUser: jest.fn(),
      authenticateUser: jest.fn()
    };

    mockEmailService = {
      sendWelcomeEmail: jest.fn()
    };

    const AuthController = require('../controllers/AuthController');
    authController = new AuthController(mockUserService, mockEmailService);
  });

  describe('register', () => {
    test('should register user successfully', async () => {
      const userData = TestUtils.generateUser();
      const createdUser = { _id: '123', ...userData };
      const token = 'jwt-token';
      
      createdUser.generateJWT = jest.fn().mockReturnValue(token);
      mockUserService.createUser.mockResolvedValue(createdUser);
      mockEmailService.sendWelcomeEmail.mockResolvedValue(true);

      const req = TestUtils.mockRequest({ body: userData });
      const res = TestUtils.mockResponse();
      const next = TestUtils.mockNext();

      await authController.register(req, res, next);

      expect(mockUserService.createUser).toHaveBeenCalledWith(userData);
      expect(mockEmailService.sendWelcomeEmail).toHaveBeenCalledWith(createdUser);
      expect(res.status).toHaveBeenCalledWith(201);
      expect(res.json).toHaveBeenCalledWith({
        success: true,
        data: {
          user: createdUser,
          token
        },
        message: 'User registered successfully'
      });
    });

    test('should handle registration error', async () => {
      const userData = TestUtils.generateUser();
      const error = new Error('User already exists');
      
      mockUserService.createUser.mockRejectedValue(error);

      const req = TestUtils.mockRequest({ body: userData });
      const res = TestUtils.mockResponse();
      const next = TestUtils.mockNext();

      await authController.register(req, res, next);

      expect(next).toHaveBeenCalledWith(error);
    });
  });

  describe('login', () => {
    test('should login user successfully', async () => {
      const loginData = { email: 'test@example.com', password: 'password123' };
      const user = { _id: '123', email: loginData.email };
      const token = 'jwt-token';
      
      user.generateJWT = jest.fn().mockReturnValue(token);
      mockUserService.authenticateUser.mockResolvedValue(user);

      const req = TestUtils.mockRequest({ body: loginData });
      const res = TestUtils.mockResponse();
      const next = TestUtils.mockNext();

      await authController.login(req, res, next);

      expect(mockUserService.authenticateUser).toHaveBeenCalledWith(
        loginData.email,
        loginData.password
      );
      expect(res.json).toHaveBeenCalledWith({
        success: true,
        data: {
          user,
          token
        },
        message: 'Login successful'
      });
    });

    test('should handle missing credentials', async () => {
      const req = TestUtils.mockRequest({ body: {} });
      const res = TestUtils.mockResponse();
      const next = TestUtils.mockNext();

      await authController.login(req, res, next);

      expect(next).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'Email and password are required'
        })
      );
    });
  });
});

// ================================
// 集成测试示例 - API测试
// ================================

describe('API Integration Tests', () => {
  let app;
  let server;
  let testUser;
  let authToken;

  beforeAll(async () => {
    // 连接测试数据库
    const { MongoMemoryServer } = require('mongodb-memory-server');
    const mongod = await MongoMemoryServer.create();
    const uri = mongod.getUri();
    
    await mongoose.connect(uri, {
      useNewUrlParser: true,
      useUnifiedTopology: true
    });

    // 创建应用
    const { createApp } = require('../app');
    app = createApp();
    
    // 启动服务器
    server = app.listen(0);
  });

  afterAll(async () => {
    await server.close();
    await mongoose.connection.close();
  });

  beforeEach(async () => {
    await TestUtils.clearDatabase();
    
    // 创建测试用户
    testUser = await TestUtils.createTestUser();
    authToken = TestUtils.generateToken(testUser);
  });

  describe('Auth Endpoints', () => {
    describe('POST /api/auth/register', () => {
      test('should register new user', async () => {
        const userData = TestUtils.generateUser({
          username: 'newuser',
          email: 'newuser@example.com'
        });

        const response = await request(app)
          .post('/api/auth/register')
          .send(userData)
          .expect(201);

        expect(response.body.success).toBe(true);
        expect(response.body.data.user.username).toBe(userData.username);
        expect(response.body.data.user.email).toBe(userData.email);
        expect(response.body.data.token).toBeDefined();
      });

      test('should return error for duplicate user', async () => {
        const userData = TestUtils.generateUser();

        await request(app)
          .post('/api/auth/register')
          .send(userData)
          .expect(400);
      });

      test('should validate required fields', async () => {
        const response = await request(app)
          .post('/api/auth/register')
          .send({})
          .expect(400);

        expect(response.body.success).toBe(false);
        expect(response.body.error.message).toContain('required');
      });
    });

    describe('POST /api/auth/login', () => {
      test('should login with valid credentials', async () => {
        const response = await request(app)
          .post('/api/auth/login')
          .send({
            email: testUser.email,
            password: 'password123'
          })
          .expect(200);

        expect(response.body.success).toBe(true);
        expect(response.body.data.user.email).toBe(testUser.email);
        expect(response.body.data.token).toBeDefined();
      });

      test('should return error for invalid credentials', async () => {
        const response = await request(app)
          .post('/api/auth/login')
          .send({
            email: testUser.email,
            password: 'wrongpassword'
          })
          .expect(401);

        expect(response.body.success).toBe(false);
        expect(response.body.error.message).toContain('Invalid credentials');
      });
    });

    describe('GET /api/auth/profile', () => {
      test('should get user profile with valid token', async () => {
        const response = await request(app)
          .get('/api/auth/profile')
          .set('Authorization', `Bearer ${authToken}`)
          .expect(200);

        expect(response.body.success).toBe(true);
        expect(response.body.data.username).toBe(testUser.username);
      });

      test('should return error without token', async () => {
        const response = await request(app)
          .get('/api/auth/profile')
          .expect(401);

        expect(response.body.success).toBe(false);
        expect(response.body.error.message).toContain('No token provided');
      });
    });
  });

  describe('Article Endpoints', () => {
    let testArticle;

    beforeEach(async () => {
      const Article = require('../models/Article');
      testArticle = new Article(TestUtils.generateArticle({
        author: testUser._id
      }));
      await testArticle.save();
    });

    describe('GET /api/articles', () => {
      test('should get articles list', async () => {
        const response = await request(app)
          .get('/api/articles')
          .expect(200);

        expect(response.body.success).toBe(true);
        expect(response.body.data.articles).toHaveLength(1);
        expect(response.body.data.pagination).toBeDefined();
      });

      test('should support pagination', async () => {
        const response = await request(app)
          .get('/api/articles?page=1&limit=5')
          .expect(200);

        expect(response.body.data.pagination.page).toBe(1);
        expect(response.body.data.pagination.limit).toBe(5);
      });

      test('should support filtering', async () => {
        const response = await request(app)
          .get('/api/articles?category=technology')
          .expect(200);

        expect(response.body.success).toBe(true);
        expect(response.body.data.articles[0].category).toBe('technology');
      });
    });

    describe('POST /api/articles', () => {
      test('should create article with valid data', async () => {
        const articleData = TestUtils.generateArticle({
          title: 'New Test Article'
        });

        const response = await request(app)
          .post('/api/articles')
          .set('Authorization', `Bearer ${authToken}`)
          .send(articleData)
          .expect(201);

        expect(response.body.success).toBe(true);
        expect(response.body.data.title).toBe(articleData.title);
        expect(response.body.data.author._id).toBe(testUser._id.toString());
      });

      test('should require authentication', async () => {
        const articleData = TestUtils.generateArticle();

        const response = await request(app)
          .post('/api/articles')
          .send(articleData)
          .expect(401);

        expect(response.body.success).toBe(false);
      });
    });

    describe('GET /api/articles/:id', () => {
      test('should get article by id', async () => {
        const response = await request(app)
          .get(`/api/articles/${testArticle._id}`)
          .expect(200);

        expect(response.body.success).toBe(true);
        expect(response.body.data.title).toBe(testArticle.title);
      });

      test('should return 404 for non-existent article', async () => {
        const fakeId = new mongoose.Types.ObjectId();
        
        const response = await request(app)
          .get(`/api/articles/${fakeId}`)
          .expect(404);

        expect(response.body.success).toBe(false);
      });
    });
  });
});

// ================================
// 端到端测试示例 - Puppeteer
// ================================

const puppeteer = require('puppeteer');

describe('E2E Tests', () => {
  let browser;
  let page;
  const baseUrl = 'http://localhost:3000';

  beforeAll(async () => {
    browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
  });

  afterAll(async () => {
    await browser.close();
  });

  beforeEach(async () => {
    page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 720 });
  });

  afterEach(async () => {
    await page.close();
  });

  describe('User Registration Flow', () => {
    test('should register new user successfully', async () => {
      await page.goto(`${baseUrl}/register`);

      // 填写注册表单
      await page.type('#username', 'testuser');
      await page.type('#email', 'test@example.com');
      await page.type('#password', 'password123');
      await page.type('#confirmPassword', 'password123');

      // 提交表单
      await page.click('button[type="submit"]');

      // 等待重定向到仪表板
      await page.waitForNavigation();
      expect(page.url()).toBe(`${baseUrl}/dashboard`);

      // 验证用户信息显示
      const username = await page.$eval('.user-info .username', el => el.textContent);
      expect(username).toBe('testuser');
    });

    test('should show validation errors for invalid input', async () => {
      await page.goto(`${baseUrl}/register`);

      // 提交空表单
      await page.click('button[type="submit"]');

      // 检查错误消息
      const errorMessages = await page.$$eval('.error-message', 
        elements => elements.map(el => el.textContent)
      );
      
      expect(errorMessages).toContain('Username is required');
      expect(errorMessages).toContain('Email is required');
      expect(errorMessages).toContain('Password is required');
    });
  });

  describe('Article Management Flow', () => {
    beforeEach(async () => {
      // 登录用户
      await page.goto(`${baseUrl}/login`);
      await page.type('#email', 'test@example.com');
      await page.type('#password', 'password123');
      await page.click('button[type="submit"]');
      await page.waitForNavigation();
    });

    test('should create new article', async () => {
      await page.goto(`${baseUrl}/articles/new`);

      // 填写文章表单
      await page.type('#title', 'Test Article Title');
      await page.type('#content', 'This is the content of the test article.');
      await page.select('#category', 'technology');
      await page.type('#tags', 'test,article');

      // 提交表单
      await page.click('button[type="submit"]');

      // 等待重定向到文章页面
      await page.waitForNavigation();
      
      // 验证文章创建成功
      const title = await page.$eval('h1', el => el.textContent);
      expect(title).toBe('Test Article Title');
    });

    test('should edit existing article', async () => {
      // 假设已有文章
      await page.goto(`${baseUrl}/articles/1/edit`);

      // 修改标题
      await page.evaluate(() => document.querySelector('#title').value = '');
      await page.type('#title', 'Updated Article Title');

      // 保存更改
      await page.click('button[type="submit"]');
      await page.waitForNavigation();

      // 验证更新成功
      const title = await page.$eval('h1', el => el.textContent);
      expect(title).toBe('Updated Article Title');
    });
  });

  describe('Responsive Design Tests', () => {
    test('should work on mobile devices', async () => {
      await page.setViewport({ width: 375, height: 667 }); // iPhone SE
      await page.goto(`${baseUrl}`);

      // 检查移动菜单
      const mobileMenu = await page.$('.mobile-menu-button');
      expect(mobileMenu).toBeTruthy();

      // 点击菜单按钮
      await page.click('.mobile-menu-button');
      
      // 检查菜单是否展开
      const menuVisible = await page.$eval('.mobile-menu', 
        el => getComputedStyle(el).display !== 'none'
      );
      expect(menuVisible).toBe(true);
    });

    test('should work on tablet devices', async () => {
      await page.setViewport({ width: 768, height: 1024 }); // iPad
      await page.goto(`${baseUrl}`);

      // 检查布局适配
      const sidebar = await page.$('.sidebar');
      const sidebarVisible = await page.evaluate(
        el => getComputedStyle(el).display !== 'none',
        sidebar
      );
      expect(sidebarVisible).toBe(true);
    });
  });

  describe('Performance Tests', () => {
    test('should load page within acceptable time', async () => {
      const startTime = Date.now();
      
      await page.goto(`${baseUrl}`, { waitUntil: 'networkidle0' });
      
      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(3000); // 3秒内加载完成
    });

    test('should have good lighthouse scores', async () => {
      const lighthouse = require('lighthouse');
      const chromeLauncher = require('chrome-launcher');
      
      const chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });
      const options = {
        logLevel: 'info',
        output: 'json',
        onlyCategories: ['performance', 'accessibility'],
        port: chrome.port
      };
      
      const runnerResult = await lighthouse(`${baseUrl}`, options);
      
      expect(runnerResult.lhr.categories.performance.score).toBeGreaterThan(0.8);
      expect(runnerResult.lhr.categories.accessibility.score).toBeGreaterThan(0.9);
      
      await chrome.kill();
    });
  });
});

// ================================
// 性能测试示例 - Artillery
// ================================

// artillery.yml 配置文件示例
const artilleryConfig = {
  config: {
    target: 'http://localhost:3000',
    phases: [
      {
        duration: 60,
        arrivalRate: 10,
        name: 'Warm up'
      },
      {
        duration: 120,
        arrivalRate: 50,
        name: 'Load test'
      },
      {
        duration: 60,
        arrivalRate: 100,
        name: 'Stress test'
      }
    ],
    payload: {
      path: './users.csv',
      fields: ['email', 'password']
    }
  },
  scenarios: [
    {
      name: 'User login and browse articles',
      weight: 70,
      flow: [
        {
          post: {
            url: '/api/auth/login',
            json: {
              email: '{{ email }}',
              password: '{{ password }}'
            },
            capture: {
              json: '$.data.token',
              as: 'authToken'
            }
          }
        },
        {
          get: {
            url: '/api/articles',
            headers: {
              Authorization: 'Bearer {{ authToken }}'
            }
          }
        },
        {
          think: 5
        },
        {
          get: {
            url: '/api/articles/{{ $randomInt(1, 100) }}',
            headers: {
              Authorization: 'Bearer {{ authToken }}'
            }
          }
        }
      ]
    },
    {
      name: 'Create new article',
      weight: 20,
      flow: [
        {
          post: {
            url: '/api/auth/login',
            json: {
              email: '{{ email }}',
              password: '{{ password }}'
            },
            capture: {
              json: '$.data.token',
              as: 'authToken'
            }
          }
        },
        {
          post: {
            url: '/api/articles',
            headers: {
              Authorization: 'Bearer {{ authToken }}'
            },
            json: {
              title: 'Performance Test Article {{ $randomInt(1, 10000) }}',
              content: 'This is a test article created during performance testing.',
              category: 'technology',
              tags: ['test', 'performance']
            }
          }
        }
      ]
    },
    {
      name: 'Anonymous browsing',
      weight: 10,
      flow: [
        {
          get: {
            url: '/api/articles'
          }
        },
        {
          think: 3
        },
        {
          get: {
            url: '/api/articles/{{ $randomInt(1, 100) }}'
          }
        }
      ]
    }
  ]
};

// ================================
// 测试配置和工具
// ================================

// Jest 配置
const jestConfig = {
  testEnvironment: 'node',
  setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],
  testMatch: [
    '<rootDir>/tests/**/*.test.js',
    '<rootDir>/src/**/__tests__/**/*.js'
  ],
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/**/*.test.js',
    '!src/config/**',
    '!src/migrations/**'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  testTimeout: 30000,
  verbose: true
};

// 测试设置文件
const testSetup = `
// tests/setup.js
const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');

let mongod;

// 全局设置
beforeAll(async () => {
  mongod = await MongoMemoryServer.create();
  const uri = mongod.getUri();
  await mongoose.connect(uri);
});

// 全局清理
afterAll(async () => {
  await mongoose.connection.close();
  await mongod.stop();
});

// 每个测试后清理数据库
afterEach(async () => {
  const collections = mongoose.connection.collections;
  for (const key in collections) {
    const collection = collections[key];
    await collection.deleteMany({});
  }
});

// 设置测试超时
jest.setTimeout(30000);

// 模拟环境变量
process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test-secret';
process.env.EMAIL_HOST = 'smtp.test.com';
`;

// ================================
// 导出
// ================================

module.exports = {
  TestUtils,
  jestConfig,
  artilleryConfig,
  testSetup
};

/* 
使用说明：

1. 测试类型：
   - 单元测试：测试单个函数或类
   - 集成测试：测试API端点
   - 端到端测试：测试完整用户流程
   - 性能测试：测试系统负载能力

2. 测试工具：
   - Jest：JavaScript测试框架
   - Supertest：HTTP断言库
   - Puppeteer：浏览器自动化
   - Artillery：性能测试工具
   - MongoDB Memory Server：内存数据库

3. 测试策略：
   - 测试金字塔：更多单元测试，适量集成测试，少量E2E测试
   - 测试覆盖率：目标80%以上
   - 测试隔离：每个测试独立运行
   - 数据清理：测试后清理数据

4. 最佳实践：
   - 使用描述性测试名称
   - 遵循AAA模式（Arrange, Act, Assert）
   - 模拟外部依赖
   - 测试边界条件
   - 保持测试简单和专注

5. 持续集成：
   - 在CI/CD管道中运行测试
   - 代码覆盖率报告
   - 性能回归检测
   - 自动化测试报告

6. 测试环境：
   - 独立的测试数据库
   - 模拟外部服务
   - 环境变量配置
   - 测试数据管理

7. 调试技巧：
   - 使用调试器
   - 详细的错误消息
   - 测试日志输出
   - 快照测试

8. 性能测试：
   - 负载测试
   - 压力测试
   - 容量测试
   - 稳定性测试

9. 安全测试：
   - 输入验证测试
   - 认证授权测试
   - SQL注入测试
   - XSS攻击测试

10. 可访问性测试：
    - 键盘导航
    - 屏幕阅读器兼容
    - 颜色对比度
    - ARIA标签
*/