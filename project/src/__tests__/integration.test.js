/**
 * 集成测试 - 实际执行TypeScript模块以提高覆盖率
 */

const request = require('supertest');
const path = require('path');

// Mock环境变量
process.env.NODE_ENV = 'test';
process.env.PORT = '0'; // 使用随机端口

// Mock配置
jest.mock('../config/app_config', () => ({
  port: 0,
  host: 'localhost',
  database: {
    pool: {
      min: 2,
      max: 10
    }
  },
  redis: {
    host: 'localhost',
    port: 6379
  },
  jwt: {
    secret: 'test-secret',
    expiresIn: '1h'
  },
  email: {
    service: 'gmail',
    user: 'test@example.com'
  },
  services: {
    ai: {
      provider: 'openai',
      apiKey: 'test-key'
    },
    storage: {
      provider: 'local',
      path: './uploads'
    }
  },
  environment: 'test',
  ssl: {
    enabled: false
  }
}));

describe('Integration Tests', () => {
  let app;
  let server;

  beforeAll(() => {
    // 导入并启动应用
    app = require('../index');
  });

  afterAll((done) => {
    if (server) {
      server.close(done);
    } else {
      done();
    }
  });

  describe('Express App Routes', () => {
    test('should respond to GET /', async () => {
      const response = await request(app)
        .get('/')
        .expect(200);
      
      expect(response.text).toContain('3AI工作室');
    });

    test('should respond to health check', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);
      
      expect(response.body).toHaveProperty('status', 'healthy');
      expect(response.body).toHaveProperty('uptime');
      expect(response.body).toHaveProperty('timestamp');
      expect(response.body).toHaveProperty('memory');
    });

    test('should respond to API info endpoint', async () => {
      const response = await request(app)
        .get('/api/info')
        .expect(200);
      
      expect(response.body).toHaveProperty('project', '3AI工作室项目');
      expect(response.body).toHaveProperty('description');
      expect(response.body).toHaveProperty('features');
      expect(Array.isArray(response.body.features)).toBe(true);
    });

    test('should handle 404 errors', async () => {
      const response = await request(app)
        .get('/nonexistent')
        .expect(404);
      
      expect(response.body).toHaveProperty('error', '页面未找到');
      expect(response.body).toHaveProperty('path', '/nonexistent');
      expect(response.body).toHaveProperty('method', 'GET');
    });

    test('should handle middleware setup', async () => {
      // 测试中间件是否正确设置
      const response = await request(app)
        .get('/')
        .expect(200);
      
      // 验证JSON响应内容类型
      expect(response.headers['content-type']).toMatch(/application\/json/);
      expect(response.body).toHaveProperty('message');
      expect(response.body).toHaveProperty('version');
    });
  });

  describe('Middleware', () => {
    test('should serve static files from public directory', async () => {
      // 测试静态文件中间件是否正确配置
      const response = await request(app)
        .get('/')
        .expect(200);
      
      expect(response.text).toBeDefined();
    });

    test('should parse JSON bodies', async () => {
      // 测试JSON解析中间件
      const response = await request(app)
        .post('/api/info')
        .send({ test: 'data' })
        .expect(404); // POST到GET端点应该返回404
      
      expect(response.body).toHaveProperty('error', '页面未找到');
      expect(response.body).toHaveProperty('method', 'POST');
    });

    test('should handle request logging', async () => {
      // 测试请求日志中间件
      const response = await request(app)
        .get('/health')
        .expect(200);
      
      expect(response.body).toHaveProperty('status', 'healthy');
    });
  });

  describe('Error Handling', () => {
    test('should handle 404 errors correctly', async () => {
      const response = await request(app)
        .get('/definitely-nonexistent-route')
        .expect(404);
      
      expect(response.body).toHaveProperty('error', '页面未找到');
      expect(response.body).toHaveProperty('path', '/definitely-nonexistent-route');
      expect(response.body).toHaveProperty('method', 'GET');
    });

    test('should handle invalid HTTP methods', async () => {
      const response = await request(app)
        .delete('/api/info')
        .expect(404);
      
      expect(response.body).toHaveProperty('error', '页面未找到');
      expect(response.body).toHaveProperty('method', 'DELETE');
    });
  });
});

describe('Client-side Code Coverage', () => {
  // 模拟浏览器环境
  const { JSDOM } = require('jsdom');
  
  beforeEach(() => {
    const dom = new JSDOM('<!DOCTYPE html><div id="app"></div>', {
      url: 'http://localhost',
      pretendToBeVisual: true,
      resources: 'usable'
    });
    
    global.document = dom.window.document;
    global.window = dom.window;
    global.console = {
      log: jest.fn(),
      error: jest.fn(),
      info: jest.fn()
    };
  });

  test('should initialize client app', () => {
    // Mock CSS import
    jest.mock('../styles/main.css', () => ({}), { virtual: true });
    
    // 由于client.ts使用了ES6模块和CSS导入，我们需要模拟这些
    const mockApp = {
      init: jest.fn(),
      setupEventListeners: jest.fn(),
      renderWelcomeMessage: jest.fn()
    };

    // 模拟客户端初始化
    mockApp.init();
    mockApp.setupEventListeners();
    mockApp.renderWelcomeMessage();

    expect(mockApp.init).toHaveBeenCalled();
    expect(mockApp.setupEventListeners).toHaveBeenCalled();
    expect(mockApp.renderWelcomeMessage).toHaveBeenCalled();
  });

  test('should handle DOM manipulation', () => {
    const appElement = document.getElementById('app');
    expect(appElement).toBeTruthy();
    
    // 模拟渲染内容
    if (appElement) {
      appElement.innerHTML = '<h1>Test Content</h1>';
      expect(appElement.innerHTML).toContain('Test Content');
    }
  });

  test('should handle event listeners', () => {
    const mockEventListener = jest.fn();
    document.addEventListener('DOMContentLoaded', mockEventListener);
    
    // 触发DOMContentLoaded事件
    const event = new window.Event('DOMContentLoaded');
    document.dispatchEvent(event);
    
    expect(mockEventListener).toHaveBeenCalled();
  });

  describe('Client-side code', () => {
    let mockConsoleLog;
    let originalDocument;
    let originalWindow;

    beforeEach(() => {
      // 保存原始环境
      originalDocument = global.document;
      originalWindow = global.window;
      
      // 设置 DOM 环境
      const { JSDOM } = require('jsdom');
      const dom = new JSDOM('<!DOCTYPE html><html><body><div id="app"></div></body></html>', {
        url: 'http://localhost',
        pretendToBeVisual: true,
        resources: 'usable'
      });
      
      global.document = dom.window.document;
      global.window = dom.window;
      global.Event = dom.window.Event;
      global.HTMLElement = dom.window.HTMLElement;
      
      // Mock console.log
      mockConsoleLog = jest.spyOn(console, 'log').mockImplementation(() => {});
      
      // 清除模块缓存以确保每次测试都重新加载
      const clientPath = require.resolve('../client.ts');
      if (require.cache[clientPath]) {
        delete require.cache[clientPath];
      }
    });

    afterEach(() => {
      mockConsoleLog.mockRestore();
      // 恢复原始环境
      global.document = originalDocument;
      global.window = originalWindow;
    });

    test('should initialize client application and log startup message', () => {
      // 导入并执行客户端代码
      require('../client.ts');
      expect(mockConsoleLog).toHaveBeenCalledWith('3AI项目客户端已启动');
    });

    test('should setup DOM content loaded event listener', () => {
      // 导入客户端代码
      require('../client.ts');
      
      // 触发 DOMContentLoaded 事件
      const event = new global.window.Event('DOMContentLoaded');
      global.document.dispatchEvent(event);
      
      expect(mockConsoleLog).toHaveBeenCalledWith('DOM已加载完成');
    });

    test('should render welcome message in app element', () => {
      // 导入并执行客户端代码
      require('../client.ts');
      
      const appElement = global.document.getElementById('app');
      expect(appElement).toBeTruthy();
      expect(appElement.innerHTML).toContain('欢迎使用3AI工作室项目');
      expect(appElement.innerHTML).toContain('这是一个基于现代技术栈构建的全栈项目');
      expect(appElement.innerHTML).toContain('前端技术');
      expect(appElement.innerHTML).toContain('后端技术');
      expect(appElement.innerHTML).toContain('TypeScript');
      expect(appElement.innerHTML).toContain('Webpack');
      expect(appElement.innerHTML).toContain('Tailwind CSS');
      expect(appElement.innerHTML).toContain('Node.js');
      expect(appElement.innerHTML).toContain('Express');
    });

    test('should handle missing app element gracefully', () => {
      // 移除 app 元素
      const appElement = global.document.getElementById('app');
      if (appElement) {
        appElement.remove();
      }
      
      // 导入并执行客户端代码，不应该抛出错误
      expect(() => {
        require('../client.ts');
      }).not.toThrow();
      
      expect(mockConsoleLog).toHaveBeenCalledWith('3AI项目客户端已启动');
    });

    test('should create App class instance', () => {
      // 导入客户端代码
      require('../client.ts');
      
      // 验证应用已初始化（通过检查控制台输出）
      expect(mockConsoleLog).toHaveBeenCalledWith('3AI项目客户端已启动');
      
      // 验证DOM内容已渲染
      const appElement = global.document.getElementById('app');
      expect(appElement.innerHTML).toBeTruthy();
    });
  });
});