// Jest 测试环境设置文件

// 设置测试超时时间
jest.setTimeout(30000);

// 导入统一配置
const configReader = require('../config/config-reader');
const appConfig = configReader.getAppConfig();

// 模拟环境变量
process.env.NODE_ENV = 'test';
process.env.API_URL = appConfig.api_url;

// 全局测试工具
global.console = {
  ...console,
  // 在测试中静默某些日志
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: console.warn,
  error: console.error
};

// 模拟 fetch API
if (!global.fetch) {
  global.fetch = require('node-fetch');
}

// 清理函数
beforeEach(() => {
  // 清除所有模拟调用记录
  jest.clearAllMocks();
});

aftereEach(() => {
  // 测试后清理
  jest.restoreAllMocks();
});