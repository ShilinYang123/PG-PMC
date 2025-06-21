/**
 * Jest 配置文件 - TypeScript 项目测试配置
 * 3AI工作室 - 现代化测试环境配置
 */

// 使用自定义Jest类型声明
interface Config {
  preset?: string;
  testEnvironment?: string;
  setupFilesAfterEnv?: string[];
  moduleFileExtensions?: string[];
  transform?: Record<string, string>;
  testMatch?: string[];
  collectCoverageFrom?: string[];
  coverageDirectory?: string;
  coverageReporters?: string[];
  verbose?: boolean;
  silent?: boolean;
  bail?: boolean;
  maxWorkers?: number | string;
  testTimeout?: number;
  [key: string]: any;
}

const config: Config = {
  // ================================
  // 基础配置
  // ================================
  
  // 指定测试环境
  testEnvironment: 'node',
  
  // 启用全局 Jest 函数（describe, test, expect 等）
  injectGlobals: true,
  
  // 项目根目录
  rootDir: '.',
  
  // 测试文件匹配模式
  testMatch: [
    '**/__tests__/**/*.(ts|tsx|js)',
    '**/*.(test|spec).(ts|tsx|js)',
  ],
  
  // 忽略的测试文件
  testPathIgnorePatterns: [
    '/node_modules/',
    '/dist/',
    '/build/',
    '/coverage/',
  ],
  
  // ================================
  // TypeScript 支持
  // ================================
  
  // 预设配置
  preset: 'ts-jest',
  
  // 文件扩展名
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  
  // 转换配置
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest',
  },
  
  // TypeScript 配置
  globals: {
    'ts-jest': {
      tsconfig: 'tsconfig.json',
      isolatedModules: true,
    },
  },
  
  // ================================
  // 模块解析
  // ================================
  
  // 模块名映射（路径别名）
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@tests/(.*)$': '<rootDir>/tests/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    '^@models/(.*)$': '<rootDir>/src/models/$1',
    '^@controllers/(.*)$': '<rootDir>/src/controllers/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@middleware/(.*)$': '<rootDir>/src/middleware/$1',
    '^@config/(.*)$': '<rootDir>/src/config/$1',
  },
  
  // 模块目录
  moduleDirectories: ['node_modules', '<rootDir>/src'],
  
  // ================================
  // 覆盖率配置
  // ================================
  
  // 启用覆盖率收集
  collectCoverage: true,
  
  // 覆盖率输出目录
  coverageDirectory: 'coverage',
  
  // 覆盖率收集的文件
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.test.{ts,tsx}',
    '!src/**/*.spec.{ts,tsx}',
    '!src/index.ts',
    '!src/app.ts',
    '!src/server.ts',
    '!src/config/**',
    '!src/types/**',
  ],
  
  // 覆盖率报告格式
  coverageReporters: [
    'text',
    'text-summary',
    'html',
    'lcov',
    'json',
  ],
  
  // 覆盖率阈值
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
    // 特定文件或目录的阈值
    './src/utils/': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
  },
  
  // ================================
  // 测试设置
  // ================================
  
  // 测试超时时间（毫秒）
  testTimeout: 10000,
  
  // 设置文件
  setupFilesAfterEnv: [
    '<rootDir>/tests/setup.ts',
  ],
  
  // 全局设置文件
  globalSetup: '<rootDir>/tests/globalSetup.ts',
  
  // 全局清理文件
  globalTeardown: '<rootDir>/tests/globalTeardown.ts',
  
  // ================================
  // 输出配置
  // ================================
  
  // 详细输出
  verbose: true,
  
  // 静默模式
  silent: false,
  
  // 显示覆盖率 (已在上方配置)
  
  // 错误输出
  errorOnDeprecated: true,
  
  // ================================
  // 监视模式配置
  // ================================
  
  // 监视插件
  watchPlugins: [
    'jest-watch-typeahead/filename',
    'jest-watch-typeahead/testname',
  ],
  
  // 监视忽略模式
  watchPathIgnorePatterns: [
    '/node_modules/',
    '/dist/',
    '/coverage/',
  ],
  
  // ================================
  // 性能配置
  // ================================
  
  // 最大工作进程数
  maxWorkers: '50%',
  
  // 缓存目录
  cacheDirectory: '<rootDir>/.jest-cache',
  
  // 清除模拟
  clearMocks: true,
  
  // 重置模拟
  resetMocks: true,
  
  // 恢复模拟
  restoreMocks: true,
  
  // ================================
  // 高级配置
  // ================================
  
  // 快照序列化器
  snapshotSerializers: [
    'jest-serializer-html',
  ],
  
  // 测试结果处理器
  testResultsProcessor: 'jest-sonar-reporter',
  
  // 报告器
  reporters: [
    'default',
    [
      'jest-html-reporters',
      {
        publicPath: './coverage/html-report',
        filename: 'report.html',
        expand: true,
      },
    ],
    [
      'jest-junit',
      {
        outputDirectory: './coverage',
        outputName: 'junit.xml',
      },
    ],
  ],
  
  // ================================
  // 环境变量
  // ================================
  
  // 测试环境选项
  testEnvironmentOptions: {
    // Node.js 环境选项
    url: 'http://localhost',
  },
  
  // 设置环境变量
  setupFiles: [
    '<rootDir>/tests/env.ts',
  ],
};

export default config;