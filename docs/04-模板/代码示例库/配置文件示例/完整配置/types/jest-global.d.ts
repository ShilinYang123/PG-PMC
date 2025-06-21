/**
 * Jest 全局类型声明文件
 * 3AI工作室 - TypeScript 测试环境类型支持
 */

// Jest 全局函数类型声明
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

// Jest 命名空间扩展
declare namespace jest {
  interface Describe {
    (name: string, fn: () => void): void;
    each<T extends readonly unknown[]>(table: T): (name: string, fn: (...args: T[number][]) => void) => void;
    only: Describe;
    skip: Describe;
  }

  interface It {
    (name: string, fn?: () => void | Promise<void>, timeout?: number): void;
    each<T extends readonly unknown[]>(table: T): (name: string, fn: (...args: T[number][]) => void | Promise<void>, timeout?: number) => void;
    only: It;
    skip: It;
    todo: (name: string) => void;
  }

  interface Lifecycle {
    (fn: () => void | Promise<void>, timeout?: number): void;
  }

  interface Expect {
    <T = unknown>(actual: T): jest.Matchers<void, T>;
    extend(matchers: Record<string, unknown>): void;
    anything(): unknown;
    any(constructor: unknown): unknown;
    arrayContaining<E = unknown>(sample: readonly E[]): unknown;
    objectContaining(sample: Record<string, unknown>): unknown;
    stringContaining(sample: string): unknown;
    stringMatching(sample: string | RegExp): unknown;
  }

  interface Matchers<R, T = {}> {
    toBe(expected: T): R;
    toEqual(expected: T): R;
    toStrictEqual(expected: T): R;
    toBeCloseTo(expected: number, precision?: number): R;
    toBeDefined(): R;
    toBeFalsy(): R;
    toBeGreaterThan(expected: number): R;
    toBeGreaterThanOrEqual(expected: number): R;
    toBeLessThan(expected: number): R;
    toBeLessThanOrEqual(expected: number): R;
    toBeInstanceOf(expected: unknown): R;
    toBeNull(): R;
    toBeTruthy(): R;
    toBeUndefined(): R;
    toBeNaN(): R;
    toContain(expected: unknown): R;
    toContainEqual(expected: unknown): R;
    toHaveLength(expected: number): R;
    toHaveProperty(keyPath: string | readonly string[], value?: unknown): R;
    toMatch(expected: string | RegExp): R;
    toMatchObject(expected: Record<string, unknown>): R;
    toThrow(expected?: string | RegExp | Error): R;
    toThrowError(expected?: string | RegExp | Error): R;
    toHaveBeenCalled(): R;
    toHaveBeenCalledTimes(expected: number): R;
    toHaveBeenCalledWith(...expected: unknown[]): R;
    toHaveBeenLastCalledWith(...expected: unknown[]): R;
    toHaveBeenNthCalledWith(call: number, ...expected: unknown[]): R;
    toHaveReturnedWith(expected: unknown): R;
    toHaveLastReturnedWith(expected: unknown): R;
    toHaveNthReturnedWith(call: number, expected: unknown): R;
    toHaveReturned(): R;
    toHaveReturnedTimes(expected: number): R;
    resolves: jest.Matchers<Promise<R>, T>;
    rejects: jest.Matchers<Promise<R>, T>;
    not: jest.Matchers<R, T>;
  }

  interface MockedFunction<T extends (...args: any[]) => any> {
    (...args: Parameters<T>): ReturnType<T>;
    mock: MockContext<T>;
    mockClear(): this;
    mockReset(): this;
    mockRestore(): void;
    mockImplementation(fn?: T): this;
    mockImplementationOnce(fn: T): this;
    mockName(name: string): this;
    mockReturnThis(): this;
    mockReturnValue(value: ReturnType<T>): this;
    mockReturnValueOnce(value: ReturnType<T>): this;
    mockResolvedValue(value: Awaited<ReturnType<T>>): this;
    mockResolvedValueOnce(value: Awaited<ReturnType<T>>): this;
    mockRejectedValue(value: unknown): this;
    mockRejectedValueOnce(value: unknown): this;
  }

  interface MockContext<T extends (...args: any[]) => any> {
    calls: Parameters<T>[];
    instances: ReturnType<T>[];
    invocationCallOrder: number[];
    results: Array<{
      type: 'return' | 'throw' | 'incomplete';
      value: ReturnType<T> | unknown;
    }>;
  }

  interface Jest {
    fn<T extends (...args: any[]) => any>(implementation?: T): MockedFunction<T>;
    spyOn<T extends {}, M extends keyof T>(object: T, method: M): MockedFunction<T[M] extends (...args: any[]) => any ? T[M] : never>;
    clearAllMocks(): void;
    resetAllMocks(): void;
    restoreAllMocks(): void;
    clearAllTimers(): void;
    runAllTimers(): void;
    runOnlyPendingTimers(): void;
    advanceTimersByTime(msToRun: number): void;
    useFakeTimers(): void;
    useRealTimers(): void;
    setTimeout(timeout: number): void;
  }
}

export {};