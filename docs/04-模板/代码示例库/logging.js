// 日志记录代码示例 - 3AI工作室
// 提供统一的日志记录机制，支持多种日志级别、格式化、存储和监控

const winston = require('winston');
const path = require('path');
const fs = require('fs');

// ================================
// 日志配置
// ================================

/**
 * 日志级别定义
 */
const LOG_LEVELS = {
  error: 0,
  warn: 1,
  info: 2,
  http: 3,
  verbose: 4,
  debug: 5,
  silly: 6
};

/**
 * 日志颜色配置
 */
const LOG_COLORS = {
  error: 'red',
  warn: 'yellow',
  info: 'green',
  http: 'magenta',
  verbose: 'cyan',
  debug: 'blue',
  silly: 'grey'
};

// 设置颜色
winston.addColors(LOG_COLORS);

// ================================
// 自定义格式化器
// ================================

/**
 * 开发环境格式化器
 */
const developmentFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.errors({ stack: true }),
  winston.format.colorize({ all: true }),
  winston.format.printf(({ timestamp, level, message, stack, ...meta }) => {
    let log = `${timestamp} [${level}]: ${message}`;
    
    // 添加元数据
    if (Object.keys(meta).length > 0) {
      log += `\n${JSON.stringify(meta, null, 2)}`;
    }
    
    // 添加堆栈跟踪
    if (stack) {
      log += `\n${stack}`;
    }
    
    return log;
  })
);

/**
 * 生产环境格式化器
 */
const productionFormat = winston.format.combine(
  winston.format.timestamp(),
  winston.format.errors({ stack: true }),
  winston.format.json(),
  winston.format.printf((info) => {
    // 添加应用信息
    info.app = process.env.APP_NAME || 'myapp';
    info.version = process.env.APP_VERSION || '1.0.0';
    info.environment = process.env.NODE_ENV || 'development';
    info.hostname = require('os').hostname();
    info.pid = process.pid;
    
    return JSON.stringify(info);
  })
);

/**
 * HTTP 请求格式化器
 */
const httpFormat = winston.format.combine(
  winston.format.timestamp(),
  winston.format.json(),
  winston.format.printf((info) => {
    const { timestamp, level, message, ...meta } = info;
    
    return JSON.stringify({
      timestamp,
      level,
      type: 'http',
      message,
      ...meta
    });
  })
);

// ================================
// 传输器配置
// ================================

/**
 * 创建文件传输器
 */
const createFileTransport = (filename, level = 'info', maxsize = 5242880, maxFiles = 5) => {
  const logDir = process.env.LOG_DIR || 'logs';
  
  // 确保日志目录存在
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }
  
  return new winston.transports.File({
    filename: path.join(logDir, filename),
    level,
    maxsize,
    maxFiles,
    format: productionFormat
  });
};

/**
 * 控制台传输器
 */
const consoleTransport = new winston.transports.Console({
  level: process.env.LOG_LEVEL || 'info',
  format: process.env.NODE_ENV === 'production' ? productionFormat : developmentFormat
});

// ================================
// 日志器创建
// ================================

/**
 * 创建主日志器
 */
const createLogger = () => {
  const transports = [consoleTransport];
  
  // 生产环境添加文件传输器
  if (process.env.NODE_ENV === 'production') {
    transports.push(
      createFileTransport('error.log', 'error'),
      createFileTransport('combined.log', 'info'),
      createFileTransport('debug.log', 'debug')
    );
  }
  
  return winston.createLogger({
    levels: LOG_LEVELS,
    level: process.env.LOG_LEVEL || 'info',
    format: productionFormat,
    transports,
    exitOnError: false,
    
    // 异常处理
    exceptionHandlers: [
      new winston.transports.File({ 
        filename: path.join(process.env.LOG_DIR || 'logs', 'exceptions.log'),
        format: productionFormat
      })
    ],
    
    // 拒绝处理
    rejectionHandlers: [
      new winston.transports.File({ 
        filename: path.join(process.env.LOG_DIR || 'logs', 'rejections.log'),
        format: productionFormat
      })
    ]
  });
};

/**
 * 创建 HTTP 日志器
 */
const createHttpLogger = () => {
  return winston.createLogger({
    level: 'http',
    format: httpFormat,
    transports: [
      new winston.transports.File({
        filename: path.join(process.env.LOG_DIR || 'logs', 'access.log'),
        format: httpFormat
      })
    ]
  });
};

// ================================
// 日志器实例
// ================================
const logger = createLogger();
const httpLogger = createHttpLogger();

// ================================
// 日志工具类
// ================================

class Logger {
  constructor(module = 'app') {
    this.module = module;
    this.logger = logger;
  }

  /**
   * 格式化日志消息
   */
  formatMessage(message, meta = {}) {
    return {
      message,
      module: this.module,
      ...meta
    };
  }

  /**
   * 错误日志
   */
  error(message, error = null, meta = {}) {
    const logData = this.formatMessage(message, {
      ...meta,
      ...(error && {
        error: {
          name: error.name,
          message: error.message,
          stack: error.stack,
          code: error.code
        }
      })
    });
    
    this.logger.error(logData);
  }

  /**
   * 警告日志
   */
  warn(message, meta = {}) {
    this.logger.warn(this.formatMessage(message, meta));
  }

  /**
   * 信息日志
   */
  info(message, meta = {}) {
    this.logger.info(this.formatMessage(message, meta));
  }

  /**
   * HTTP 日志
   */
  http(message, meta = {}) {
    this.logger.http(this.formatMessage(message, meta));
  }

  /**
   * 调试日志
   */
  debug(message, meta = {}) {
    this.logger.debug(this.formatMessage(message, meta));
  }

  /**
   * 详细日志
   */
  verbose(message, meta = {}) {
    this.logger.verbose(this.formatMessage(message, meta));
  }

  /**
   * 性能日志
   */
  performance(operation, duration, meta = {}) {
    this.info(`Performance: ${operation}`, {
      type: 'performance',
      operation,
      duration,
      ...meta
    });
  }

  /**
   * 业务日志
   */
  business(action, user, meta = {}) {
    this.info(`Business: ${action}`, {
      type: 'business',
      action,
      user,
      ...meta
    });
  }

  /**
   * 安全日志
   */
  security(event, user, meta = {}) {
    this.warn(`Security: ${event}`, {
      type: 'security',
      event,
      user,
      ...meta
    });
  }
}

// ================================
// Express 中间件
// ================================

/**
 * HTTP 请求日志中间件
 */
const httpLoggerMiddleware = (req, res, next) => {
  const start = Date.now();
  const originalSend = res.send;
  
  // 重写 send 方法以捕获响应
  res.send = function(body) {
    const duration = Date.now() - start;
    
    // 记录请求日志
    httpLogger.http('HTTP Request', {
      method: req.method,
      url: req.originalUrl,
      statusCode: res.statusCode,
      duration,
      userAgent: req.get('User-Agent'),
      ip: req.ip,
      userId: req.user?.id,
      requestId: req.id,
      contentLength: res.get('Content-Length'),
      referer: req.get('Referer')
    });
    
    // 调用原始 send 方法
    originalSend.call(this, body);
  };
  
  next();
};

/**
 * 请求ID中间件
 */
const requestIdMiddleware = (req, res, next) => {
  req.id = generateRequestId();
  res.setHeader('X-Request-ID', req.id);
  next();
};

/**
 * 生成请求ID
 */
const generateRequestId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
};

// ================================
// 性能监控
// ================================

/**
 * 性能计时器
 */
class PerformanceTimer {
  constructor(logger, operation) {
    this.logger = logger;
    this.operation = operation;
    this.startTime = process.hrtime.bigint();
  }

  /**
   * 结束计时并记录
   */
  end(meta = {}) {
    const endTime = process.hrtime.bigint();
    const duration = Number(endTime - this.startTime) / 1000000; // 转换为毫秒
    
    this.logger.performance(this.operation, duration, meta);
    return duration;
  }
}

/**
 * 性能监控装饰器
 */
const performanceMonitor = (operation) => {
  return (target, propertyName, descriptor) => {
    const method = descriptor.value;
    
    descriptor.value = async function(...args) {
      const logger = new Logger(target.constructor.name);
      const timer = new PerformanceTimer(logger, `${operation || propertyName}`);
      
      try {
        const result = await method.apply(this, args);
        timer.end({ success: true });
        return result;
      } catch (error) {
        timer.end({ success: false, error: error.message });
        throw error;
      }
    };
    
    return descriptor;
  };
};

// ================================
// 日志聚合和分析
// ================================

/**
 * 日志分析器
 */
class LogAnalyzer {
  constructor() {
    this.metrics = {
      requests: 0,
      errors: 0,
      warnings: 0,
      averageResponseTime: 0,
      statusCodes: {},
      endpoints: {},
      users: new Set()
    };
  }

  /**
   * 分析日志条目
   */
  analyze(logEntry) {
    if (logEntry.type === 'http') {
      this.analyzeHttpLog(logEntry);
    } else if (logEntry.level === 'error') {
      this.metrics.errors++;
    } else if (logEntry.level === 'warn') {
      this.metrics.warnings++;
    }
  }

  /**
   * 分析 HTTP 日志
   */
  analyzeHttpLog(logEntry) {
    this.metrics.requests++;
    
    // 状态码统计
    const statusCode = logEntry.statusCode;
    this.metrics.statusCodes[statusCode] = (this.metrics.statusCodes[statusCode] || 0) + 1;
    
    // 端点统计
    const endpoint = `${logEntry.method} ${logEntry.url}`;
    this.metrics.endpoints[endpoint] = (this.metrics.endpoints[endpoint] || 0) + 1;
    
    // 用户统计
    if (logEntry.userId) {
      this.metrics.users.add(logEntry.userId);
    }
    
    // 响应时间统计
    if (logEntry.duration) {
      this.updateAverageResponseTime(logEntry.duration);
    }
  }

  /**
   * 更新平均响应时间
   */
  updateAverageResponseTime(duration) {
    const currentAvg = this.metrics.averageResponseTime;
    const count = this.metrics.requests;
    this.metrics.averageResponseTime = (currentAvg * (count - 1) + duration) / count;
  }

  /**
   * 获取统计报告
   */
  getReport() {
    return {
      ...this.metrics,
      uniqueUsers: this.metrics.users.size,
      errorRate: this.metrics.errors / this.metrics.requests,
      topEndpoints: this.getTopEndpoints(),
      topStatusCodes: this.getTopStatusCodes()
    };
  }

  /**
   * 获取热门端点
   */
  getTopEndpoints(limit = 10) {
    return Object.entries(this.metrics.endpoints)
      .sort(([,a], [,b]) => b - a)
      .slice(0, limit)
      .map(([endpoint, count]) => ({ endpoint, count }));
  }

  /**
   * 获取状态码分布
   */
  getTopStatusCodes() {
    return Object.entries(this.metrics.statusCodes)
      .sort(([,a], [,b]) => b - a)
      .map(([code, count]) => ({ code: parseInt(code), count }));
  }
}

// ================================
// 日志轮转和清理
// ================================

/**
 * 日志清理工具
 */
class LogCleaner {
  constructor(logDir = 'logs', maxAge = 30) {
    this.logDir = logDir;
    this.maxAge = maxAge; // 天数
  }

  /**
   * 清理过期日志
   */
  async cleanOldLogs() {
    try {
      const files = await fs.promises.readdir(this.logDir);
      const now = Date.now();
      const maxAgeMs = this.maxAge * 24 * 60 * 60 * 1000;

      for (const file of files) {
        const filePath = path.join(this.logDir, file);
        const stats = await fs.promises.stat(filePath);
        
        if (now - stats.mtime.getTime() > maxAgeMs) {
          await fs.promises.unlink(filePath);
          logger.info(`Deleted old log file: ${file}`);
        }
      }
    } catch (error) {
      logger.error('Failed to clean old logs', error);
    }
  }

  /**
   * 启动定期清理
   */
  startPeriodicCleanup(intervalHours = 24) {
    const intervalMs = intervalHours * 60 * 60 * 1000;
    
    setInterval(() => {
      this.cleanOldLogs();
    }, intervalMs);
    
    // 立即执行一次
    this.cleanOldLogs();
  }
}

// ================================
// 使用示例
// ================================

// 创建模块日志器
const userLogger = new Logger('user-service');
const authLogger = new Logger('auth-service');
const dbLogger = new Logger('database');

// 基本使用
userLogger.info('User created', { userId: 123, email: 'user@example.com' });
userLogger.error('User creation failed', new Error('Database connection failed'));
userLogger.performance('user-query', 150, { query: 'SELECT * FROM users' });

// 业务日志
userLogger.business('user-login', { id: 123, email: 'user@example.com' });
authLogger.security('failed-login-attempt', { email: 'hacker@evil.com', ip: '192.168.1.100' });

// Express 应用集成
const express = require('express');
const app = express();

// 添加中间件
app.use(requestIdMiddleware);
app.use(httpLoggerMiddleware);

// 示例路由
app.get('/api/users', (req, res) => {
  const timer = new PerformanceTimer(userLogger, 'get-users');
  
  // 模拟业务逻辑
  setTimeout(() => {
    timer.end({ count: 100 });
    res.json({ users: [] });
  }, 100);
});

// 启动日志清理
const logCleaner = new LogCleaner();
logCleaner.startPeriodicCleanup();

// ================================
// 导出模块
// ================================
module.exports = {
  Logger,
  logger,
  httpLogger,
  httpLoggerMiddleware,
  requestIdMiddleware,
  PerformanceTimer,
  performanceMonitor,
  LogAnalyzer,
  LogCleaner,
  
  // 工具函数
  createLogger,
  createHttpLogger,
  generateRequestId
};

// ================================
// 使用说明
// ================================

/*
1. 基本配置：
   - 设置环境变量 LOG_LEVEL, LOG_DIR, NODE_ENV
   - 在生产环境中使用 JSON 格式
   - 在开发环境中使用彩色格式

2. 日志级别：
   - error: 错误信息
   - warn: 警告信息
   - info: 一般信息
   - http: HTTP 请求
   - debug: 调试信息
   - verbose: 详细信息

3. 日志类型：
   - 应用日志: 一般业务逻辑
   - HTTP 日志: 请求响应记录
   - 错误日志: 异常和错误
   - 性能日志: 性能监控
   - 安全日志: 安全事件
   - 业务日志: 业务操作

4. 最佳实践：
   - 使用结构化日志
   - 包含足够的上下文信息
   - 设置合适的日志级别
   - 定期清理旧日志
   - 监控日志异常
   - 集成外部日志服务

5. 集成建议：
   - ELK Stack: Elasticsearch + Logstash + Kibana
   - Fluentd: 日志收集和转发
   - Grafana: 日志可视化
   - Sentry: 错误追踪
   - DataDog: 综合监控

6. 性能考虑：
   - 异步写入日志
   - 使用缓冲区
   - 避免同步 I/O
   - 合理设置日志级别
   - 定期轮转日志文件
*/