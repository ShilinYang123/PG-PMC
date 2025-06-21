/**
 * @jest-environment jsdom
 */

describe('Client Application', () => {
  let mockConsoleLog;
  
  beforeEach(() => {
    // 设置DOM环境
    document.body.innerHTML = '<div id="app"></div>';
    
    // Mock console.log
    mockConsoleLog = jest.spyOn(console, 'log').mockImplementation(() => {});
    
    // 清除模块缓存
    jest.resetModules();
  });
  
  afterEach(() => {
    mockConsoleLog.mockRestore();
    document.body.innerHTML = '';
  });
  
  test('should initialize client application', () => {
    // 导入客户端代码
    require('../client.ts');
    
    // 验证初始化日志
    expect(mockConsoleLog).toHaveBeenCalledWith('3AI项目客户端已启动');
  });
  
  test('should render welcome message', () => {
    // 导入客户端代码
    require('../client.ts');
    
    const appElement = document.getElementById('app');
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
  
  test('should setup DOM content loaded event listener', () => {
    // 导入客户端代码
    require('../client.ts');
    
    // 触发 DOMContentLoaded 事件
    const event = new Event('DOMContentLoaded');
    document.dispatchEvent(event);
    
    expect(mockConsoleLog).toHaveBeenCalledWith('DOM已加载完成');
  });
  
  test('should handle missing app element gracefully', () => {
    // 移除 app 元素
    document.body.innerHTML = '';
    
    // 导入并执行客户端代码，不应该抛出错误
    expect(() => {
      require('../client.ts');
    }).not.toThrow();
    
    expect(mockConsoleLog).toHaveBeenCalledWith('3AI项目客户端已启动');
  });
  
  test('should create App class and initialize properly', () => {
    // 导入客户端代码
    require('../client.ts');
    
    // 验证应用已初始化
    expect(mockConsoleLog).toHaveBeenCalledWith('3AI项目客户端已启动');
    
    // 验证DOM内容已渲染
    const appElement = document.getElementById('app');
    expect(appElement.innerHTML).toBeTruthy();
    expect(appElement.innerHTML.length).toBeGreaterThan(0);
  });
  
  test('should have proper HTML structure in rendered content', () => {
    // 导入客户端代码
    require('../client.ts');
    
    const appElement = document.getElementById('app');
    
    // 检查HTML结构
    expect(appElement.querySelector('h1')).toBeTruthy();
    expect(appElement.querySelector('.container')).toBeTruthy();
    expect(appElement.querySelector('.grid')).toBeTruthy();
    expect(appElement.querySelector('.bg-blue-50')).toBeTruthy();
    expect(appElement.querySelector('.bg-green-50')).toBeTruthy();
  });
});