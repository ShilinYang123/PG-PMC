/**
 * Jest 导入问题解决方案示例
 * 3AI工作室 - TypeScript 测试最佳实践
 */

// TypeScript 类型声明 - 确保 Jest 全局函数可用
/**
 * Jest 导入问题解决方案示例
 * 3AI工作室 - 提供多种 Jest 函数使用方式的最佳实践
 */

// ================================
// 解决方案 1：使用全局模式（推荐）
// ================================

// 在 jest.config.ts 中设置 injectGlobals: true
// 这样就可以直接使用 describe, test, expect 等全局函数
// 无需任何导入语句

// 示例测试（全局模式）
describe('全局模式测试示例', () => {
  test('应该能够使用全局 Jest 函数', () => {
    expect(1 + 1).toBe(2);
  });

  test('应该能够使用 jest 对象', () => {
    const mockFn = jest.fn();
    mockFn('test');
    expect(mockFn).toHaveBeenCalledWith('test');
  });
});

// ================================
// 解决方案 2：显式导入（现代方式）
// ================================

/*
// 需要安装：npm install --save-dev @jest/globals
import {
  describe as jestDescribe,
  test as jestTest,
  expect as jestExpect,
  beforeEach,
  afterEach,
  beforeAll,
  afterAll,
  jest as jestObject
} from '@jest/globals';

// 使用导入的函数
jestDescribe('显式导入测试示例', () => {
  jestTest('应该能够使用导入的 Jest 函数', () => {
    jestExpected(1 + 1).toBe(2);
  });
});
*/

// ================================
// 解决方案 3：类型声明（兼容模式）
// ================================

/*
// 如果不想修改 Jest 配置，可以添加类型声明
// 在项目根目录创建 types/jest.d.ts 文件：

declare global {
  const describe: jest.Describe;
  const test: jest.It;
  const it: jest.It;
  const expect: jest.Expect;
  const beforeEach: jest.Lifecycle;
  const afterEach: jest.Lifecycle;
  const beforeAll: jest.Lifecycle;
  const afterAll: jest.Lifecycle;
  const jest: jest.Jest;
}

export {};
*/

// ================================
// 解决方案 4：条件导入（灵活模式）
// ================================

/*
// 根据环境动态选择导入方式
let testDescribe: jest.Describe;
let testIt: jest.It;
let testExpect: jest.Expect;
let testJest: jest.Jest;

if (typeof describe !== 'undefined') {
  // 全局模式
  testDescribe = describe;
  testIt = test;
  testExpected = expect;
  testJest = jest;
} else {
  // 导入模式
  const jestGlobals = require('@jest/globals');
  testDescribe = jestGlobals.describe;
  testIt = jestGlobals.test;
  testExpected = jestGlobals.expect;
  testJest = jestGlobals.jest;
}
*/

// ================================
// 最佳实践建议
// ================================

/**
 * 1. 推荐使用全局模式（injectGlobals: true）
 *    - 简洁明了，无需导入
 *    - 与传统 Jest 使用方式一致
 *    - 减少样板代码
 * 
 * 2. 如果团队偏好显式导入
 *    - 安装 @jest/globals
 *    - 使用 ESM 导入语法
 *    - 更明确的依赖关系
 * 
 * 3. 配置文件设置
 *    - jest.config.ts 中设置 injectGlobals: true
 *    - 或者在 package.json 中配置
 * 
 * 4. TypeScript 配置
 *    - 确保 tsconfig.json 包含 Jest 类型
 *    - 在 types 数组中添加 "jest"
 * 
 * 5. 依赖管理
 *    - 安装 @types/jest
 *    - 如使用 @jest/globals，确保版本兼容
 */

// ================================
// 实际项目配置示例
// ================================

/**
 * package.json 依赖：
 * {
 *   "devDependencies": {
 *     "jest": "^29.0.0",
 *     "@types/jest": "^29.0.0",
 *     "ts-jest": "^29.0.0",
 *     "@jest/globals": "^29.0.0" // 可选
 *   }
 * }
 * 
 * jest.config.ts 配置：
 * {
 *   preset: 'ts-jest',
 *   testEnvironment: 'node',
 *   injectGlobals: true, // 启用全局函数
 *   globals: {
 *     'ts-jest': {
 *       isolatedModules: true
 *     }
 *   }
 * }
 * 
 * tsconfig.json 配置：
 * {
 *   "compilerOptions": {
 *     "types": ["jest", "node"]
 *   }
 * }
 */

export {}; // 确保文件被视为模块