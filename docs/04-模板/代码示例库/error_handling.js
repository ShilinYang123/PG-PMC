// 错误处理代码示例 - 3AI工作室
// 提供统一的错误处理机制，包括自定义错误类、错误中间件、错误日志等

// ================================
// 自定义错误类
// ================================

/**
 * 基础应用错误类
 */
class AppError extends Error {
  constructor(message, statusCode = 500, code = 'INTERNAL_ERROR', isOperational = true) {
    super(message);
    
    this.name = this.constructor.name;
    this.statusCode = statusCode;
    this.code = code;
    this.isOperational = isOperational;
    this.timestamp = new Date().toISOString();
    
    // 捕获堆栈跟踪
    Error.captureStackTrace(this, this.constructor);
  }

  /**
   * 转换为 JSON 格式
   */
  toJSON() {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      statusCode: this.statusCode,
      timestamp: this.timestamp,
      stack: process.env.NODE_ENV === 'development' ? this.stack : undefined
    };
  }
}

/**
 * 验证错误
 */
class ValidationError extends AppError {
  constructor(message, field = null, value = null) {
    super(message, 400, 'VALIDATION_ERROR');
    this.field = field;
    this.value = value;
  }
}

/**
 * 认证错误
 */
class AuthenticationError extends AppError {
  constructor(message = '认证失败') {
    super(message, 401, 'AUTHENTICATION_ERROR');
  }
}

/**
 * 授权错误
 */
class AuthorizationError extends AppError {
  constructor(message = '权限不足') {
    super(message, 403, 'AUTHORIZATION_ERROR');
  }
}

/**
 * 资源未找到错误
 */
class NotFoundError extends AppError {
  constructor(resource = '资源') {
    super(`${resource}未找到`, 404, 'NOT_FOUND_ERROR');
    this.resource = resource;
  }
}

/**
 * 冲突错误
 */
class ConflictError extends AppError {
  constructor(message = '资源冲突') {
    super(message, 409, 'CONFLICT_ERROR');
  }
}

/**
 * 业务逻辑错误
 */
class BusinessError extends AppError {
  constructor(message, code = 'BUSINESS_ERROR') {
    super(message, 422, code);
  }
}

/**
 * 外部服务错误
 */
class ExternalServiceError extends AppError {
  constructor(service, message = '外部服务调用失败') {
    super(`${service}: ${message}`, 502, 'EXTERNAL_SERVICE_ERROR');
    this.service = service;
  }
}

/**
 * 限流错误
 */
class RateLimitError extends AppError {
  constructor(message = '请求过于频繁') {
    super(message, 429, 'RATE_LIMIT_ERROR');
  }
}

// ================================
// 错误处理中间件 (Express)
// ================================

/**
 * 全局错误处理中间件
 */
const errorHandler = (err, req, res, next) => {
  // 确保错误对象有必要的属性
  let error = { ...err };
  error.message = err.message;

  // 记录错误日志
  console.error('Error:', {
    message: error.message,
    stack: error.stack,
    url: req.originalUrl,
    method: req.method,
    ip: req.ip,
    userAgent: req.get('User-Agent'),
    timestamp: new Date().toISOString()
  });

  // 处理特定类型的错误
  if (err.name === 'CastError') {
    const message = '资源未找到';
    error = new NotFoundError(message);
  }

  if (err.code === 11000) {
    const message = '重复的字段值';
    error = new ConflictError(message);
  }

  if (err.name === 'ValidationError') {
    const message = Object.values(err.errors).map(val => val.message).join(', ');
    error = new ValidationError(message);
  }

  if (err.name === 'JsonWebTokenError') {
    const message = '无效的令牌';
    error = new AuthenticationError(message);
  }

  if (err.name === 'TokenExpiredError') {
    const message = '令牌已过期';
    error = new AuthenticationError(message);
  }

  // 发送错误响应
  res.status(error.statusCode || 500).json({
    success: false,
    error: {
      message: error.message || '服务器内部错误',
      code: error.code || 'INTERNAL_ERROR',
      ...(process.env.NODE_ENV === 'development' && { stack: error.stack })
    }
  });
};

/**
 * 404 错误处理中间件
 */
const notFoundHandler = (req, res, next) => {
  const error = new NotFoundError(`路由 ${req.originalUrl}`);
  next(error);
};

/**
 * 异步错误捕获装饰器
 */
const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

// ================================
// 错误处理工具函数
// ================================

/**
 * 安全的 JSON 解析
 */
const safeJsonParse = (str, defaultValue = null) => {
  try {
    return JSON.parse(str);
  } catch (error) {
    console.warn('JSON 解析失败:', error.message);
    return defaultValue;
  }
};

/**
 * 安全的异步操作
 */
const safeAsync = async (asyncFn, defaultValue = null) => {
  try {
    return await asyncFn();
  } catch (error) {
    console.error('异步操作失败:', error.message);
    return defaultValue;
  }
};

/**
 * 重试机制
 */
const retry = async (fn, maxRetries = 3, delay = 1000) => {
  let lastError;
  
  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      if (i === maxRetries) {
        throw new ExternalServiceError('重试', `操作失败，已重试 ${maxRetries} 次`);
      }
      
      // 指数退避
      const waitTime = delay * Math.pow(2, i);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
  }
};

/**
 * 断路器模式
 */
class CircuitBreaker {
  constructor(threshold = 5, timeout = 60000, monitor = false) {
    this.threshold = threshold;
    this.timeout = timeout;
    this.monitor = monitor;
    this.failureCount = 0;
    this.lastFailureTime = null;
    this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
  }

  async call(fn) {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailureTime > this.timeout) {
        this.state = 'HALF_OPEN';
      } else {
        throw new ExternalServiceError('断路器', '服务暂时不可用');
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  onSuccess() {
    this.failureCount = 0;
    this.state = 'CLOSED';
  }

  onFailure() {
    this.failureCount++;
    this.lastFailureTime = Date.now();
    
    if (this.failureCount >= this.threshold) {
      this.state = 'OPEN';
    }
  }

  getState() {
    return {
      state: this.state,
      failureCount: this.failureCount,
      lastFailureTime: this.lastFailureTime
    };
  }
}

// ================================
// 错误监控和报告
// ================================

/**
 * 错误监控类
 */
class ErrorMonitor {
  constructor() {
    this.errors = [];
    this.maxErrors = 1000;
  }

  /**
   * 记录错误
   */
  logError(error, context = {}) {
    const errorLog = {
      id: this.generateId(),
      timestamp: new Date().toISOString(),
      message: error.message,
      stack: error.stack,
      code: error.code,
      statusCode: error.statusCode,
      context,
      severity: this.getSeverity(error)
    };

    this.errors.unshift(errorLog);
    
    // 保持错误日志数量在限制内
    if (this.errors.length > this.maxErrors) {
      this.errors = this.errors.slice(0, this.maxErrors);
    }

    // 发送到外部监控服务
    this.sendToMonitoring(errorLog);
  }

  /**
   * 获取错误严重程度
   */
  getSeverity(error) {
    if (error.statusCode >= 500) return 'critical';
    if (error.statusCode >= 400) return 'warning';
    return 'info';
  }

  /**
   * 发送到监控服务
   */
  async sendToMonitoring(errorLog) {
    // 这里可以集成 Sentry, LogRocket 等监控服务
    if (process.env.NODE_ENV === 'production') {
      // await sentry.captureException(errorLog);
    }
  }

  /**
   * 生成唯一ID
   */
  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  /**
   * 获取错误统计
   */
  getStats() {
    const now = Date.now();
    const oneHour = 60 * 60 * 1000;
    const oneDay = 24 * oneHour;

    const recentErrors = this.errors.filter(
      error => now - new Date(error.timestamp).getTime() < oneHour
    );

    const dailyErrors = this.errors.filter(
      error => now - new Date(error.timestamp).getTime() < oneDay
    );

    return {
      total: this.errors.length,
      lastHour: recentErrors.length,
      lastDay: dailyErrors.length,
      bySeverity: this.groupBySeverity(this.errors),
      byCode: this.groupByCode(this.errors)
    };
  }

  groupBySeverity(errors) {
    return errors.reduce((acc, error) => {
      acc[error.severity] = (acc[error.severity] || 0) + 1;
      return acc;
    }, {});
  }

  groupByCode(errors) {
    return errors.reduce((acc, error) => {
      acc[error.code] = (acc[error.code] || 0) + 1;
      return acc;
    }, {});
  }
}

// ================================
// 使用示例
// ================================

// Express 应用示例
const express = require('express');
const app = express();

// 创建错误监控实例
const errorMonitor = new ErrorMonitor();

// 创建断路器实例
const externalApiBreaker = new CircuitBreaker(3, 30000);

// 示例路由
app.get('/api/users/:id', asyncHandler(async (req, res) => {
  const { id } = req.params;
  
  // 验证参数
  if (!id || isNaN(id)) {
    throw new ValidationError('用户ID必须是有效的数字', 'id', id);
  }
  
  // 模拟数据库查询
  const user = await findUserById(id);
  
  if (!user) {
    throw new NotFoundError('用户');
  }
  
  res.json({ success: true, data: user });
}));

// 外部API调用示例
app.get('/api/external-data', asyncHandler(async (req, res) => {
  try {
    const data = await externalApiBreaker.call(async () => {
      return await retry(async () => {
        const response = await fetch('https://api.example.com/data');
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
      }, 3, 1000);
    });
    
    res.json({ success: true, data });
  } catch (error) {
    throw new ExternalServiceError('外部API', error.message);
  }
}));

// 错误处理中间件
app.use(notFoundHandler);
app.use((err, req, res, next) => {
  // 记录到监控系统
  errorMonitor.logError(err, {
    url: req.originalUrl,
    method: req.method,
    ip: req.ip,
    userAgent: req.get('User-Agent')
  });
  
  // 调用错误处理中间件
  errorHandler(err, req, res, next);
});

// 未捕获异常处理
process.on('uncaughtException', (error) => {
  console.error('未捕获的异常:', error);
  errorMonitor.logError(error, { type: 'uncaughtException' });
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('未处理的 Promise 拒绝:', reason);
  errorMonitor.logError(new Error(reason), { type: 'unhandledRejection' });
});

// ================================
// 导出模块
// ================================
module.exports = {
  // 错误类
  AppError,
  ValidationError,
  AuthenticationError,
  AuthorizationError,
  NotFoundError,
  ConflictError,
  BusinessError,
  ExternalServiceError,
  RateLimitError,
  
  // 中间件
  errorHandler,
  notFoundHandler,
  asyncHandler,
  
  // 工具函数
  safeJsonParse,
  safeAsync,
  retry,
  
  // 高级功能
  CircuitBreaker,
  ErrorMonitor
};

// ================================
// 使用说明
// ================================

/*
1. 基本用法：
   - 继承 AppError 创建自定义错误类
   - 使用 asyncHandler 包装异步路由
   - 在 Express 应用中使用错误处理中间件

2. 错误分类：
   - ValidationError: 输入验证错误
   - AuthenticationError: 认证失败
   - AuthorizationError: 权限不足
   - NotFoundError: 资源未找到
   - BusinessError: 业务逻辑错误
   - ExternalServiceError: 外部服务错误

3. 高级功能：
   - CircuitBreaker: 防止级联故障
   - retry: 自动重试机制
   - ErrorMonitor: 错误监控和统计

4. 最佳实践：
   - 使用操作性错误和编程错误分类
   - 记录详细的错误上下文
   - 在生产环境中隐藏敏感信息
   - 集成外部监控服务
   - 设置合适的错误告警

5. 集成建议：
   - Sentry: 错误追踪和性能监控
   - Winston: 结构化日志记录
   - Prometheus: 指标收集
   - Grafana: 可视化监控
*/