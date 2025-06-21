/**
 * TypeScript文件测试
 * 测试index.ts和client.ts的功能
 */

const path = require('path');
const fs = require('fs');

// Mock console methods
const originalConsole = {
  log: console.log,
  error: console.error,
  info: console.info
};

beforeAll(() => {
  console.log = jest.fn();
  console.error = jest.fn();
  console.info = jest.fn();
});

afterAll(() => {
  console.log = originalConsole.log;
  console.error = originalConsole.error;
  console.info = originalConsole.info;
});

describe('TypeScript Files Tests', () => {
  const indexTsPath = path.join(__dirname, '..', 'index.ts');
  const clientTsPath = path.join(__dirname, '..', 'client.ts');

  test('index.ts file should exist', () => {
    expect(fs.existsSync(indexTsPath)).toBe(true);
  });

  test('client.ts file should exist', () => {
    expect(fs.existsSync(clientTsPath)).toBe(true);
  });

  test('index.ts should contain Express server setup', () => {
    const content = fs.readFileSync(indexTsPath, 'utf8');
    
    // 检查是否包含Express相关导入和设置
    expect(content).toContain('express');
    expect(content).toContain('app');
  });

  test('client.ts should contain frontend code', () => {
    const content = fs.readFileSync(clientTsPath, 'utf8');
    
    // 检查是否包含前端相关代码
    expect(content).toContain('document');
  });

  test('index.ts should have proper TypeScript syntax', () => {
    const content = fs.readFileSync(indexTsPath, 'utf8');
    
    // 检查TypeScript语法
    expect(content).toMatch(/import.*from/); // ES6 imports
    expect(content).not.toContain('var '); // 应该使用let/const
  });

  test('client.ts should have proper TypeScript syntax', () => {
    const content = fs.readFileSync(clientTsPath, 'utf8');
    
    // 检查TypeScript语法
    expect(content).toMatch(/const|let/); // 应该使用现代变量声明
  });

  test('index.ts should contain port configuration', () => {
    const content = fs.readFileSync(indexTsPath, 'utf8');
    
    // 检查端口配置
    expect(content).toMatch(/port|PORT/i);
  });

  test('client.ts should contain DOM manipulation', () => {
    const content = fs.readFileSync(clientTsPath, 'utf8');
    
    // 检查DOM操作
    expect(content).toMatch(/document\.|getElementById|querySelector/);
  });

  test('files should not contain console.log in production code', () => {
    const indexContent = fs.readFileSync(indexTsPath, 'utf8');
    const clientContent = fs.readFileSync(clientTsPath, 'utf8');
    
    // 检查是否有调试用的console.log（应该很少或没有）
    const indexLogs = (indexContent.match(/console\.log/g) || []).length;
    const clientLogs = (clientContent.match(/console\.log/g) || []).length;
    
    // 允许少量的日志，但不应该太多
    expect(indexLogs).toBeLessThan(10);
    expect(clientLogs).toBeLessThan(10);
  });

  test('index.ts should have error handling', () => {
    const content = fs.readFileSync(indexTsPath, 'utf8');
    
    // 检查错误处理
    expect(content).toMatch(/try|catch|error/i);
  });

  test('files should have reasonable length', () => {
    const indexContent = fs.readFileSync(indexTsPath, 'utf8');
    const clientContent = fs.readFileSync(clientTsPath, 'utf8');
    
    const indexLines = indexContent.split('\n').length;
    const clientLines = clientContent.split('\n').length;
    
    // 文件应该有合理的长度（不为空，但也不过长）
    expect(indexLines).toBeGreaterThan(5);
    expect(indexLines).toBeLessThan(500);
    expect(clientLines).toBeGreaterThan(5);
    expect(clientLines).toBeLessThan(500);
  });

  test('index.ts should contain middleware setup', () => {
    const content = fs.readFileSync(indexTsPath, 'utf8');
    
    // 检查中间件设置
    expect(content).toMatch(/app\.use|middleware/i);
  });

  test('client.ts should contain event listeners or DOM ready code', () => {
    const content = fs.readFileSync(clientTsPath, 'utf8');
    
    // 检查事件监听器或DOM就绪代码
    expect(content).toMatch(/addEventListener|DOMContentLoaded|onload/i);
  });

  test('files should not contain TODO or FIXME comments', () => {
    const indexContent = fs.readFileSync(indexTsPath, 'utf8');
    const clientContent = fs.readFileSync(clientTsPath, 'utf8');
    
    // 检查是否有未完成的TODO或FIXME
    expect(indexContent).not.toMatch(/TODO|FIXME/i);
    expect(clientContent).not.toMatch(/TODO|FIXME/i);
  });

  test('index.ts should have proper exports or server start', () => {
    const content = fs.readFileSync(indexTsPath, 'utf8');
    
    // 检查导出或服务器启动
    expect(content).toMatch(/export|app\.listen|server\.listen/i);
  });
});