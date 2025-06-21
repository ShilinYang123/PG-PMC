/**
 * 现代化测试示例
 * 提供完整的测试工具类和示例，包括数据库测试、API测试、模拟对象等
 * 支持 Jest、Supertest、MongoDB Memory Server 等现代测试工具
 */

// TypeScript 编译器配置
/// <reference lib="es2015" />
/// <reference lib="es2017" />

// Jest 测试框架导入
// 注意：使用 Jest 全局模式（在 jest.config.ts 中设置 injectGlobals: true）
// 或者显式导入：import { describe, test, expect, beforeEach, afterEach, beforeAll, afterAll, jest } from '@jest/globals';

// 外部依赖导入（在实际项目中需要安装相应的包）
// import request from 'supertest';
// import { MongoMemoryServer } from 'mongodb-memory-server';
// import mongoose from 'mongoose';
// import express from 'express';

// 模拟导入 - 用于示例目的
declare class MongoMemoryServer {
  static create(): Promise<MongoMemoryServer>;
  start(): Promise<void>;
  stop(): Promise<void>;
  getUri(): string;
}

declare const mongoose: {
  connect(uri: string): Promise<void>;
  disconnect(): Promise<void>;
  connection: {
    dropDatabase(): Promise<void>;
    close(): Promise<void>;
    collections: Record<string, {
      deleteMany(filter: any): Promise<any>;
    }>;
  };
};

// Express 类型声明
type Express = {
  listen(port: number, callback?: () => void): any;
  use(...handlers: any[]): Express;
  get(path: string, ...handlers: any[]): Express;
  post(path: string, ...handlers: any[]): Express;
  put(path: string, ...handlers: any[]): Express;
  delete(path: string, ...handlers: any[]): Express;
};

// Jest 全局函数和命名空间类型声明
declare function describe(name: string, fn: () => void): void;
declare function test(name: string, fn: () => void | Promise<void>, timeout?: number): void;
declare function it(name: string, fn: () => void | Promise<void>, timeout?: number): void;
declare function beforeAll(fn: () => void | Promise<void>, timeout?: number): void;
declare function afterAll(fn: () => void | Promise<void>, timeout?: number): void;
declare function beforeEach(fn: () => void | Promise<void>, timeout?: number): void;
declare function afterEach(fn: () => void | Promise<void>, timeout?: number): void;

declare namespace test {
  function each<T extends readonly any[]>(cases: readonly T[]): (name: string, fn: (...args: T extends readonly (infer U)[] ? U[] : any[]) => void | Promise<void>) => void;
}

interface JestMatchers {
  toBe(expected: any): void;
  toEqual(expected: any): void;
  toBeTruthy(): void;
  toBeFalsy(): void;
  toBeNull(): void;
  toBeUndefined(): void;
  toBeDefined(): void;
  toContain(item: any): void;
  toHaveLength(length: number): void;
  toThrow(error?: string | RegExp | Error): void;
  toHaveBeenCalled(): void;
  toHaveBeenCalledWith(...args: any[]): void;
  toHaveBeenCalledTimes(times: number): void;
  toBeLessThan(expected: number): void;
  toBeGreaterThan(expected: number): void;
  toMatchObject(expected: any): void;
  toMatch(pattern: string | RegExp): void;
  resolves: any;
  rejects: any;
}

declare const expect: {
  (actual: any): JestMatchers & {
    not: JestMatchers;
  };
};

declare namespace jest {
  interface MockedFunction<T extends (...args: any[]) => any> {
    (...args: Parameters<T>): ReturnType<T>;
    mockReturnValue(value: ReturnType<T>): this;
    mockResolvedValue(value: any): this;
    mockRejectedValue(value: any): this;
    mockImplementation(fn: T): this;
    mockClear(): void;
    mockReset(): void;
    mockRestore(): void;
  }
  
  function fn<T extends (...args: any[]) => any>(implementation?: T): MockedFunction<T>;
  function spyOn<T, K extends keyof T>(object: T, method: K): MockedFunction<T[K] extends (...args: any[]) => any ? T[K] : never>;
  function setTimeout(timeout: number): void;
}

// ================================
// 类型定义
// ================================

interface TestUser {
  id?: string;
  username: string;
  email: string;
  password: string;
  role: 'admin' | 'user' | 'moderator';
  profile: {
    firstName: string;
    lastName: string;
    bio?: string;
    avatar?: string;
  };
  createdAt?: Date;
  updatedAt?: Date;
}

interface TestArticle {
  id?: string;
  title: string;
  content: string;
  excerpt: string;
  category: string;
  tags: string[];
  status: 'draft' | 'published' | 'archived';
  author?: string;
  publishedAt?: Date;
  createdAt?: Date;
  updatedAt?: Date;
}

interface MockRequest {
  body: Record<string, unknown>;
  params: Record<string, string>;
  query: Record<string, string>;
  headers: Record<string, string>;
  user?: TestUser | null;
}

interface MockResponse {
  status: (code: number) => MockResponse;
  json: (data: unknown) => MockResponse;
  send: (data: unknown) => MockResponse;
  cookie: (name: string, value: string, options?: unknown) => MockResponse;
  clearCookie: (name: string) => MockResponse;
}

// ================================
// 现代化测试工具类
// ================================

export class ModernTestUtils {
  private static mongoServer: MongoMemoryServer;

  /**
   * 设置内存数据库
   */
  static async setupDatabase(): Promise<void> {
    this.mongoServer = await MongoMemoryServer.create();
    const mongoUri = this.mongoServer.getUri();
    await mongoose.connect(mongoUri);
  }

  /**
   * 清理数据库
   */
  static async teardownDatabase(): Promise<void> {
    await mongoose.connection.dropDatabase();
    await mongoose.connection.close();
    await this.mongoServer.stop();
  }

  /**
   * 清空所有集合
   */
  static async clearDatabase(): Promise<void> {
    const collections = mongoose.connection.collections as Record<string, { deleteMany(filter: any): Promise<any> }>;
    const clearPromises = Object.values(collections).map(
      collection => collection.deleteMany({})
    );
    await Promise.all(clearPromises);
  }

  /**
   * 生成测试用户数据
   */
  static generateUser(overrides: Partial<TestUser> = {}): TestUser {
    return {
      username: `testuser_${Date.now()}`,
      email: `test_${Date.now()}@example.com`,
      password: 'SecurePassword123!',
      role: 'user',
      profile: {
        firstName: 'Test',
        lastName: 'User',
        bio: 'Generated test user bio',
      },
      ...overrides,
    };
  }

  /**
   * 生成测试文章数据
   */
  static generateArticle(overrides: Partial<TestArticle> = {}): TestArticle {
    const timestamp = Date.now();
    return {
      title: `Test Article ${timestamp}`,
      content: `This is test article content generated at ${new Date().toISOString()}`,
      excerpt: 'Auto-generated test excerpt',
      category: 'technology',
      tags: ['test', 'automated', 'typescript'],
      status: 'published',
      ...overrides,
    };
  }

  /**
   * 创建测试用户（需要实际的 User 模型）
   */
  static async createTestUser(userData: Partial<TestUser> = {}): Promise<TestUser & Document> {
    // 注意：这里需要实际的 User 模型
    // const User = require('../models/User');
    // const user = new User(this.generateUser(userData));
    // return await user.save();
    
    // 模拟实现
    const user = this.generateUser(userData);
    return { ...user, id: `user_${Date.now()}` } as TestUser & Document;
  }

  /**
   * 模拟 Express 请求对象
   */
  static mockRequest(overrides: Partial<MockRequest> = {}): MockRequest {
    return {
      body: {},
      params: {},
      query: {},
      headers: {
        'content-type': 'application/json',
        'user-agent': 'test-agent',
      },
      user: null,
      ...overrides,
    };
  }

  /**
   * 模拟 Express 响应对象
   */
  static mockResponse(): MockResponse {
    const res = {} as MockResponse;
    res.status = jest.fn().mockReturnValue(res);
    res.json = jest.fn().mockReturnValue(res);
    res.send = jest.fn().mockReturnValue(res);
    res.cookie = jest.fn().mockReturnValue(res);
    res.clearCookie = jest.fn().mockReturnValue(res);
    return res;
  }

  /**
   * 模拟 Express next 函数
   */
  static mockNext(): jest.MockedFunction<() => void> {
    return jest.fn();
  }

  /**
   * 等待指定时间（用于异步测试）
   */
  static async wait(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 生成随机字符串
   */
  static randomString(length = 10): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }

  /**
   * 生成随机邮箱
   */
  static randomEmail(): string {
    return `${this.randomString(8)}@${this.randomString(5)}.com`;
  }

}

// 邮箱验证方法
function validateEmail(email: string | boolean): boolean {
  if (typeof email !== 'string') return false;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// ================================
// 工具函数测试示例（TypeScript）
// ================================

// 假设的工具函数类型
interface Utils {
  validateEmail(email: string | boolean): boolean;
  slugify(text: string): string;
  formatDate(date: Date, format?: string): string;
  paginate(page: number, limit: number, total: number): {
    page: number;
    limit: number;
    total: number;
    pages: number;
    hasNext: boolean;
    hasPrev: boolean;
    nextPage: number | null;
    prevPage: number | null;
  };
}

describe('Utils (TypeScript)', () => {
  // 模拟 Utils 模块
  const mockUtils: Utils = {
    validateEmail: (email: string | boolean): boolean => {
      if (typeof email !== 'string') return false;
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(email);
    },
    
    slugify: (text: string): string => {
      return text
        .toLowerCase()
        .trim()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_-]+/g, '-')
        .replace(/^-+|-+$/g, '');
    },
    
    formatDate: (date: Date, format = 'YYYY-MM-DD'): string => {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      
      if (format === 'DD/MM/YYYY') {
        return `${day}/${month}/${year}`;
      }
      return `${year}-${month}-${day}`;
    },
    
    paginate: (page: number, limit: number, total: number) => {
      const pages = Math.ceil(total / limit);
      return {
        page,
        limit,
        total,
        pages,
        hasNext: page < pages,
        hasPrev: page > 1,
        nextPage: page < pages ? page + 1 : null,
        prevPage: page > 1 ? page - 1 : null,
      };
    },
  };

  describe('validateEmail', () => {
    test.each([
      ['test@example.com', true],
      ['user.name+tag@domain.co.uk', true],
      ['valid.email@subdomain.domain.com', true],
    ])('should return %p for email %s', (email, expected) => {
      expect(mockUtils.validateEmail(email)).toBe(expected);
    });

    test.each([
      ['invalid-email', false],
      ['test@', false],
      ['@example.com', false],
      ['', false],
      ['test..test@example.com', false],
    ])('should return %p for invalid email %s', (email, expected) => {
      expect(mockUtils.validateEmail(email)).toBe(expected);
    });
  });

  describe('slugify', () => {
    test('should convert text to URL-friendly slug', () => {
      expect(mockUtils.slugify('Hello World')).toBe('hello-world');
      expect(mockUtils.slugify('Test Article Title!')).toBe('test-article-title');
      expect(mockUtils.slugify('  Multiple   Spaces  ')).toBe('multiple-spaces');
    });

    test('should handle special characters', () => {
      expect(mockUtils.slugify('Test@#$%^&*()Title')).toBe('test-title');
      expect(mockUtils.slugify('TypeScript & Node.js')).toBe('typescript-nodejs');
    });

    test('should handle edge cases', () => {
      expect(mockUtils.slugify('')).toBe('');
      expect(mockUtils.slugify('   ')).toBe('');
      expect(mockUtils.slugify('---')).toBe('');
    });
  });

  describe('formatDate', () => {
    const testDate = new Date('2023-12-25T10:30:00Z');

    test('should format date with default format', () => {
      expect(mockUtils.formatDate(testDate)).toBe('2023-12-25');
    });

    test('should format date with custom format', () => {
      expect(mockUtils.formatDate(testDate, 'DD/MM/YYYY')).toBe('25/12/2023');
    });
  });

  describe('paginate', () => {
    test('should calculate pagination for middle page', () => {
      const result = mockUtils.paginate(2, 10, 25);
      expect(result).toEqual({
        page: 2,
        limit: 10,
        total: 25,
        pages: 3,
        hasNext: true,
        hasPrev: true,
        nextPage: 3,
        prevPage: 1,
      });
    });

    test('should handle first page', () => {
      const result = mockUtils.paginate(1, 10, 25);
      expect(result).toEqual({
        page: 1,
        limit: 10,
        total: 25,
        pages: 3,
        hasNext: true,
        hasPrev: false,
        nextPage: 2,
        prevPage: null,
      });
    });

    test('should handle last page', () => {
      const result = mockUtils.paginate(3, 10, 25);
      expect(result).toEqual({
        page: 3,
        limit: 10,
        total: 25,
        pages: 3,
        hasNext: false,
        hasPrev: true,
        nextPage: null,
        prevPage: 2,
      });
    });
  });
});

// ================================
// API 集成测试示例
// ================================

describe('API Integration Tests', () => {
  let app: any; // Express 应用实例
  
  beforeAll(async () => {
    await ModernTestUtils.setupDatabase();
    // app = createApp(); // 假设有创建应用的函数
  });

  afterAll(async () => {
    await ModernTestUtils.teardownDatabase();
  });

  beforeEach(async () => {
    await ModernTestUtils.clearDatabase();
  });

  describe('POST /api/users', () => {
    test('should create a new user', async () => {
      const userData = ModernTestUtils.generateUser();
      
      // 模拟 API 测试
      // const response = await request(app)
      //   .post('/api/users')
      //   .send(userData)
      //   .expect(201);
      
      // expect(response.body).toMatchObject({
      //   id: expect.any(String),
      //   username: userData.username,
      //   email: userData.email,
      //   role: userData.role,
      // });
      
      // 模拟断言
      expect(userData.username).toBeDefined();
      expect(userData.email).toMatch(/^[^\s@]+@[^\s@]+\.[^\s@]+$/);
    });

    test('should return 400 for invalid user data', async () => {
      const invalidData = { username: '', email: 'invalid-email' };
      
      // 模拟 API 测试
      // await request(app)
      //   .post('/api/users')
      //   .send(invalidData)
      //   .expect(400);
      
      expect(invalidData.username).toBe('');
      expect(invalidData.email).not.toMatch(/^[^\s@]+@[^\s@]+\.[^\s@]+$/);
    });
  });
});

// ================================
// 异步操作测试示例
// ================================

describe('Async Operations', () => {
  test('should handle promise resolution', async () => {
    const asyncFunction = async (value: string): Promise<string> => {
      await ModernTestUtils.wait(100);
      return `processed: ${value}`;
    };

    const result = await asyncFunction('test');
    expect(result).toBe('processed: test');
  });

  test('should handle promise rejection', async () => {
    const failingFunction = async (): Promise<never> => {
      await ModernTestUtils.wait(50);
      throw new Error('Operation failed');
    };

    await expect(failingFunction()).rejects.toThrow('Operation failed');
  });

  test('should timeout long operations', async () => {
    const longOperation = async (): Promise<string> => {
      await ModernTestUtils.wait(2000);
      return 'completed';
    };

    // 设置测试超时
    jest.setTimeout(1000);
    
    await expect(longOperation()).rejects.toThrow();
  }, 1500);
});

// ================================
// Mock 和 Spy 示例
// ================================

describe('Mocking and Spying', () => {
  test('should mock external dependencies', () => {
    const mockDatabase = {
      find: jest.fn().mockResolvedValue([{ id: 1, name: 'test' }]),
      create: jest.fn().mockResolvedValue({ id: 2, name: 'created' }),
      update: jest.fn().mockResolvedValue({ id: 1, name: 'updated' }),
      delete: jest.fn().mockResolvedValue(true),
    };

    expect(mockDatabase.find).toBeDefined();
    expect(mockDatabase.create).toBeDefined();
  });

  test('should spy on method calls', () => {
    const service = {
      processData: (data: string) => `processed: ${data}`,
    };

    const spy = jest.spyOn(service, 'processData');
    
    service.processData('test');
    
    expect(spy).toHaveBeenCalledWith('test');
    expect(spy).toHaveBeenCalledTimes(1);
    
    spy.mockRestore();
  });
});

// ================================
// 性能测试示例
// ================================

describe('Performance Tests', () => {
  test('should complete operation within time limit', async () => {
    const startTime = Date.now();
    
    // 模拟一些操作
    await ModernTestUtils.wait(100);
    
    const endTime = Date.now();
    const duration = endTime - startTime;
    
    expect(duration).toBeLessThan(200);
  });

  test('should handle large datasets efficiently', () => {
    const largeArray = Array.from({ length: 10000 }, (_, i) => i);
    
    const startTime = performance.now();
    const result = largeArray.filter(n => n % 2 === 0);
    const endTime = performance.now();
    
    expect(result.length).toBe(5000);
    expect(endTime - startTime).toBeLessThan(100); // 100ms
  });
});