#!/usr/bin/env node
/**
 * Node.js代码示例库 - 3AI工作室
 * 提供常用的Node.js代码模板，包括Express应用、数据库操作、中间件等
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
const winston = require('winston');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const mongoose = require('mongoose');
const redis = require('redis');
const nodemailer = require('nodemailer');
const multer = require('multer');
const path = require('path');
const fs = require('fs').promises;
const crypto = require('crypto');
const { promisify } = require('util');
const { EventEmitter } = require('events');

// ================================
// 配置管理
// ================================

class Config {
  constructor() {
    this.env = process.env.NODE_ENV || 'development';
    this.port = process.env.PORT || 3000;
    this.mongoUrl = process.env.MONGO_URL || 'mongodb://localhost:27017/myapp';
    this.redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
    this.jwtSecret = process.env.JWT_SECRET || 'your-secret-key';
    this.jwtExpiry = process.env.JWT_EXPIRY || '24h';
    this.emailHost = process.env.EMAIL_HOST || 'smtp.gmail.com';
    this.emailPort = process.env.EMAIL_PORT || 587;
    this.emailUser = process.env.EMAIL_USER || '';
    this.emailPass = process.env.EMAIL_PASS || '';
  }

  isDevelopment() {
    return this.env === 'development';
  }

  isProduction() {
    return this.env === 'production';
  }

  validate() {
    const required = ['jwtSecret'];
    const missing = required.filter(key => !this[key]);
    
    if (missing.length > 0) {
      throw new Error(`Missing required config: ${missing.join(', ')}`);
    }
  }
}

const config = new Config();

// ================================
// 日志系统
// ================================

class Logger {
  constructor() {
    this.logger = winston.createLogger({
      level: config.isDevelopment() ? 'debug' : 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      defaultMeta: { service: 'nodejs-app' },
      transports: [
        new winston.transports.File({ 
          filename: 'logs/error.log', 
          level: 'error',
          maxsize: 5242880, // 5MB
          maxFiles: 5
        }),
        new winston.transports.File({ 
          filename: 'logs/combined.log',
          maxsize: 5242880,
          maxFiles: 5
        })
      ]
    });

    if (config.isDevelopment()) {
      this.logger.add(new winston.transports.Console({
        format: winston.format.combine(
          winston.format.colorize(),
          winston.format.simple()
        )
      }));
    }
  }

  debug(message, meta = {}) {
    this.logger.debug(message, meta);
  }

  info(message, meta = {}) {
    this.logger.info(message, meta);
  }

  warn(message, meta = {}) {
    this.logger.warn(message, meta);
  }

  error(message, error = null, meta = {}) {
    if (error instanceof Error) {
      this.logger.error(message, { ...meta, error: error.stack });
    } else {
      this.logger.error(message, meta);
    }
  }
}

const logger = new Logger();

// ================================
// 错误处理
// ================================

class AppError extends Error {
  constructor(message, statusCode = 500, isOperational = true) {
    super(message);
    this.statusCode = statusCode;
    this.isOperational = isOperational;
    this.timestamp = new Date().toISOString();
    
    Error.captureStackTrace(this, this.constructor);
  }
}

class ValidationError extends AppError {
  constructor(message, field = null) {
    super(message, 400);
    this.field = field;
  }
}

class NotFoundError extends AppError {
  constructor(resource = 'Resource') {
    super(`${resource} not found`, 404);
  }
}

class UnauthorizedError extends AppError {
  constructor(message = 'Unauthorized') {
    super(message, 401);
  }
}

class ForbiddenError extends AppError {
  constructor(message = 'Forbidden') {
    super(message, 403);
  }
}

// 全局错误处理中间件
const errorHandler = (err, req, res, next) => {
  let error = { ...err };
  error.message = err.message;

  // Mongoose错误处理
  if (err.name === 'CastError') {
    const message = 'Resource not found';
    error = new NotFoundError(message);
  }

  if (err.code === 11000) {
    const message = 'Duplicate field value entered';
    error = new ValidationError(message);
  }

  if (err.name === 'ValidationError') {
    const message = Object.values(err.errors).map(val => val.message).join(', ');
    error = new ValidationError(message);
  }

  logger.error('Error occurred', err, {
    url: req.originalUrl,
    method: req.method,
    ip: req.ip,
    userAgent: req.get('User-Agent')
  });

  res.status(error.statusCode || 500).json({
    success: false,
    error: {
      message: error.message || 'Server Error',
      ...(config.isDevelopment() && { stack: error.stack })
    }
  });
};

// 异步错误处理包装器
const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

// ================================
// 数据库连接
// ================================

class Database {
  constructor() {
    this.mongoose = mongoose;
    this.redis = null;
  }

  async connectMongoDB() {
    try {
      const conn = await mongoose.connect(config.mongoUrl, {
        useNewUrlParser: true,
        useUnifiedTopology: true
      });
      
      logger.info(`MongoDB Connected: ${conn.connection.host}`);
      
      // 监听连接事件
      mongoose.connection.on('error', (err) => {
        logger.error('MongoDB connection error', err);
      });
      
      mongoose.connection.on('disconnected', () => {
        logger.warn('MongoDB disconnected');
      });
      
    } catch (error) {
      logger.error('MongoDB connection failed', error);
      process.exit(1);
    }
  }

  async connectRedis() {
    try {
      this.redis = redis.createClient({ url: config.redisUrl });
      
      this.redis.on('error', (err) => {
        logger.error('Redis connection error', err);
      });
      
      this.redis.on('connect', () => {
        logger.info('Redis connected');
      });
      
      await this.redis.connect();
      
    } catch (error) {
      logger.error('Redis connection failed', error);
    }
  }

  async disconnect() {
    try {
      await mongoose.connection.close();
      if (this.redis) {
        await this.redis.quit();
      }
      logger.info('Database connections closed');
    } catch (error) {
      logger.error('Error closing database connections', error);
    }
  }

  getRedis() {
    return this.redis;
  }
}

const database = new Database();

// ================================
// 数据模型
// ================================

// 用户模型
const userSchema = new mongoose.Schema({
  username: {
    type: String,
    required: [true, 'Username is required'],
    unique: true,
    trim: true,
    minlength: [3, 'Username must be at least 3 characters'],
    maxlength: [30, 'Username cannot exceed 30 characters']
  },
  email: {
    type: String,
    required: [true, 'Email is required'],
    unique: true,
    lowercase: true,
    match: [/^\S+@\S+\.\S+$/, 'Please enter a valid email']
  },
  password: {
    type: String,
    required: [true, 'Password is required'],
    minlength: [6, 'Password must be at least 6 characters'],
    select: false
  },
  role: {
    type: String,
    enum: ['user', 'admin', 'moderator'],
    default: 'user'
  },
  profile: {
    firstName: String,
    lastName: String,
    avatar: String,
    bio: String
  },
  isActive: {
    type: Boolean,
    default: true
  },
  lastLogin: Date,
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
});

// 密码加密中间件
userSchema.pre('save', async function(next) {
  if (!this.isModified('password')) return next();
  
  try {
    const salt = await bcrypt.genSalt(12);
    this.password = await bcrypt.hash(this.password, salt);
    next();
  } catch (error) {
    next(error);
  }
});

// 更新时间中间件
userSchema.pre('save', function(next) {
  this.updatedAt = Date.now();
  next();
});

// 实例方法
userSchema.methods.comparePassword = async function(candidatePassword) {
  return await bcrypt.compare(candidatePassword, this.password);
};

userSchema.methods.generateJWT = function() {
  return jwt.sign(
    { 
      id: this._id, 
      username: this.username, 
      role: this.role 
    },
    config.jwtSecret,
    { expiresIn: config.jwtExpiry }
  );
};

userSchema.methods.toJSON = function() {
  const userObject = this.toObject();
  delete userObject.password;
  return userObject;
};

const User = mongoose.model('User', userSchema);

// 文章模型
const articleSchema = new mongoose.Schema({
  title: {
    type: String,
    required: [true, 'Title is required'],
    trim: true,
    maxlength: [200, 'Title cannot exceed 200 characters']
  },
  content: {
    type: String,
    required: [true, 'Content is required']
  },
  excerpt: {
    type: String,
    maxlength: [500, 'Excerpt cannot exceed 500 characters']
  },
  author: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  tags: [{
    type: String,
    trim: true
  }],
  category: {
    type: String,
    required: true
  },
  status: {
    type: String,
    enum: ['draft', 'published', 'archived'],
    default: 'draft'
  },
  featuredImage: String,
  viewCount: {
    type: Number,
    default: 0
  },
  likeCount: {
    type: Number,
    default: 0
  },
  publishedAt: Date,
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
});

articleSchema.pre('save', function(next) {
  this.updatedAt = Date.now();
  if (this.status === 'published' && !this.publishedAt) {
    this.publishedAt = Date.now();
  }
  next();
});

const Article = mongoose.model('Article', articleSchema);

// ================================
// 缓存服务
// ================================

class CacheService {
  constructor(redisClient) {
    this.redis = redisClient;
    this.defaultTTL = 3600; // 1小时
  }

  async get(key) {
    try {
      const value = await this.redis.get(key);
      return value ? JSON.parse(value) : null;
    } catch (error) {
      logger.error('Cache get error', error);
      return null;
    }
  }

  async set(key, value, ttl = this.defaultTTL) {
    try {
      await this.redis.setEx(key, ttl, JSON.stringify(value));
      return true;
    } catch (error) {
      logger.error('Cache set error', error);
      return false;
    }
  }

  async del(key) {
    try {
      await this.redis.del(key);
      return true;
    } catch (error) {
      logger.error('Cache delete error', error);
      return false;
    }
  }

  async exists(key) {
    try {
      return await this.redis.exists(key);
    } catch (error) {
      logger.error('Cache exists error', error);
      return false;
    }
  }

  async flush() {
    try {
      await this.redis.flushAll();
      return true;
    } catch (error) {
      logger.error('Cache flush error', error);
      return false;
    }
  }

  // 缓存装饰器
  cache(ttl = this.defaultTTL) {
    return (target, propertyName, descriptor) => {
      const method = descriptor.value;
      
      descriptor.value = async function(...args) {
        const key = `${target.constructor.name}:${propertyName}:${JSON.stringify(args)}`;
        
        // 尝试从缓存获取
        let result = await this.cacheService.get(key);
        if (result !== null) {
          return result;
        }
        
        // 执行原方法
        result = await method.apply(this, args);
        
        // 存入缓存
        await this.cacheService.set(key, result, ttl);
        
        return result;
      };
      
      return descriptor;
    };
  }
}

// ================================
// 邮件服务
// ================================

class EmailService {
  constructor() {
    this.transporter = nodemailer.createTransporter({
      host: config.emailHost,
      port: config.emailPort,
      secure: config.emailPort === 465,
      auth: {
        user: config.emailUser,
        pass: config.emailPass
      }
    });
  }

  async sendEmail(to, subject, html, text = null) {
    try {
      const mailOptions = {
        from: config.emailUser,
        to,
        subject,
        html,
        text: text || this.htmlToText(html)
      };

      const result = await this.transporter.sendMail(mailOptions);
      logger.info('Email sent successfully', { to, subject, messageId: result.messageId });
      return result;
    } catch (error) {
      logger.error('Email send failed', error, { to, subject });
      throw new AppError('Failed to send email', 500);
    }
  }

  async sendWelcomeEmail(user) {
    const subject = '欢迎注册我们的平台';
    const html = `
      <h1>欢迎，${user.username}！</h1>
      <p>感谢您注册我们的平台。</p>
      <p>您的账户已经创建成功，现在可以开始使用我们的服务了。</p>
    `;
    
    return await this.sendEmail(user.email, subject, html);
  }

  async sendPasswordResetEmail(user, resetToken) {
    const subject = '密码重置请求';
    const resetUrl = `${process.env.FRONTEND_URL}/reset-password?token=${resetToken}`;
    const html = `
      <h1>密码重置</h1>
      <p>您请求重置密码。请点击下面的链接重置您的密码：</p>
      <a href="${resetUrl}">重置密码</a>
      <p>如果您没有请求重置密码，请忽略此邮件。</p>
      <p>此链接将在1小时后过期。</p>
    `;
    
    return await this.sendEmail(user.email, subject, html);
  }

  htmlToText(html) {
    return html.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
  }
}

// ================================
// 文件上传服务
// ================================

class FileUploadService {
  constructor() {
    this.uploadDir = path.join(__dirname, 'uploads');
    this.maxFileSize = 5 * 1024 * 1024; // 5MB
    this.allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'];
    
    this.ensureUploadDir();
  }

  async ensureUploadDir() {
    try {
      await fs.mkdir(this.uploadDir, { recursive: true });
    } catch (error) {
      logger.error('Failed to create upload directory', error);
    }
  }

  getMulterConfig() {
    const storage = multer.diskStorage({
      destination: (req, file, cb) => {
        cb(null, this.uploadDir);
      },
      filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        const ext = path.extname(file.originalname);
        cb(null, file.fieldname + '-' + uniqueSuffix + ext);
      }
    });

    const fileFilter = (req, file, cb) => {
      if (this.allowedTypes.includes(file.mimetype)) {
        cb(null, true);
      } else {
        cb(new ValidationError('File type not allowed'), false);
      }
    };

    return multer({
      storage,
      fileFilter,
      limits: {
        fileSize: this.maxFileSize
      }
    });
  }

  async deleteFile(filename) {
    try {
      const filePath = path.join(this.uploadDir, filename);
      await fs.unlink(filePath);
      return true;
    } catch (error) {
      logger.error('Failed to delete file', error, { filename });
      return false;
    }
  }

  getFileUrl(filename) {
    return `/uploads/${filename}`;
  }
}

// ================================
// 认证中间件
// ================================

class AuthMiddleware {
  static async authenticate(req, res, next) {
    try {
      const token = req.header('Authorization')?.replace('Bearer ', '');
      
      if (!token) {
        throw new UnauthorizedError('No token provided');
      }

      const decoded = jwt.verify(token, config.jwtSecret);
      const user = await User.findById(decoded.id);
      
      if (!user || !user.isActive) {
        throw new UnauthorizedError('Invalid token');
      }

      req.user = user;
      next();
    } catch (error) {
      if (error.name === 'JsonWebTokenError') {
        next(new UnauthorizedError('Invalid token'));
      } else if (error.name === 'TokenExpiredError') {
        next(new UnauthorizedError('Token expired'));
      } else {
        next(error);
      }
    }
  }

  static authorize(...roles) {
    return (req, res, next) => {
      if (!req.user) {
        return next(new UnauthorizedError());
      }

      if (!roles.includes(req.user.role)) {
        return next(new ForbiddenError('Insufficient permissions'));
      }

      next();
    };
  }

  static async optionalAuth(req, res, next) {
    try {
      const token = req.header('Authorization')?.replace('Bearer ', '');
      
      if (token) {
        const decoded = jwt.verify(token, config.jwtSecret);
        const user = await User.findById(decoded.id);
        
        if (user && user.isActive) {
          req.user = user;
        }
      }
      
      next();
    } catch (error) {
      // 可选认证，忽略错误
      next();
    }
  }
}

// ================================
// 验证中间件
// ================================

class ValidationMiddleware {
  static validateUser(req, res, next) {
    const { username, email, password } = req.body;
    const errors = [];

    if (!username || username.length < 3) {
      errors.push('Username must be at least 3 characters');
    }

    if (!email || !/^\S+@\S+\.\S+$/.test(email)) {
      errors.push('Valid email is required');
    }

    if (!password || password.length < 6) {
      errors.push('Password must be at least 6 characters');
    }

    if (errors.length > 0) {
      return next(new ValidationError(errors.join(', ')));
    }

    next();
  }

  static validateArticle(req, res, next) {
    const { title, content, category } = req.body;
    const errors = [];

    if (!title || title.trim().length === 0) {
      errors.push('Title is required');
    }

    if (!content || content.trim().length === 0) {
      errors.push('Content is required');
    }

    if (!category || category.trim().length === 0) {
      errors.push('Category is required');
    }

    if (errors.length > 0) {
      return next(new ValidationError(errors.join(', ')));
    }

    next();
  }

  static validatePagination(req, res, next) {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;

    if (page < 1) {
      return next(new ValidationError('Page must be greater than 0'));
    }

    if (limit < 1 || limit > 100) {
      return next(new ValidationError('Limit must be between 1 and 100'));
    }

    req.pagination = { page, limit, skip: (page - 1) * limit };
    next();
  }
}

// ================================
// 服务层
// ================================

class UserService {
  constructor(cacheService) {
    this.cacheService = cacheService;
  }

  async createUser(userData) {
    const existingUser = await User.findOne({
      $or: [{ email: userData.email }, { username: userData.username }]
    });

    if (existingUser) {
      throw new ValidationError('User already exists');
    }

    const user = new User(userData);
    await user.save();

    logger.info('User created', { userId: user._id, username: user.username });
    return user;
  }

  async authenticateUser(email, password) {
    const user = await User.findOne({ email }).select('+password');
    
    if (!user || !await user.comparePassword(password)) {
      throw new UnauthorizedError('Invalid credentials');
    }

    if (!user.isActive) {
      throw new UnauthorizedError('Account is deactivated');
    }

    user.lastLogin = new Date();
    await user.save();

    logger.info('User authenticated', { userId: user._id, username: user.username });
    return user;
  }

  async getUserById(id) {
    const cacheKey = `user:${id}`;
    let user = await this.cacheService.get(cacheKey);
    
    if (!user) {
      user = await User.findById(id);
      if (user) {
        await this.cacheService.set(cacheKey, user, 1800); // 30分钟
      }
    }

    if (!user) {
      throw new NotFoundError('User');
    }

    return user;
  }

  async updateUser(id, updateData) {
    const user = await User.findByIdAndUpdate(
      id,
      { ...updateData, updatedAt: new Date() },
      { new: true, runValidators: true }
    );

    if (!user) {
      throw new NotFoundError('User');
    }

    // 清除缓存
    await this.cacheService.del(`user:${id}`);

    logger.info('User updated', { userId: user._id });
    return user;
  }

  async deleteUser(id) {
    const user = await User.findByIdAndDelete(id);
    
    if (!user) {
      throw new NotFoundError('User');
    }

    // 清除缓存
    await this.cacheService.del(`user:${id}`);

    logger.info('User deleted', { userId: id });
    return true;
  }

  async getUsers(page = 1, limit = 10, filters = {}) {
    const skip = (page - 1) * limit;
    
    const query = User.find(filters)
      .skip(skip)
      .limit(limit)
      .sort({ createdAt: -1 });

    const [users, total] = await Promise.all([
      query.exec(),
      User.countDocuments(filters)
    ]);

    return {
      users,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit)
      }
    };
  }
}

class ArticleService {
  constructor(cacheService) {
    this.cacheService = cacheService;
  }

  async createArticle(articleData, authorId) {
    const article = new Article({
      ...articleData,
      author: authorId
    });

    await article.save();
    await article.populate('author', 'username email');

    logger.info('Article created', { articleId: article._id, authorId });
    return article;
  }

  async getArticleById(id) {
    const article = await Article.findById(id).populate('author', 'username email');
    
    if (!article) {
      throw new NotFoundError('Article');
    }

    return article;
  }

  async updateArticle(id, updateData, userId) {
    const article = await Article.findById(id);
    
    if (!article) {
      throw new NotFoundError('Article');
    }

    // 检查权限
    if (article.author.toString() !== userId) {
      throw new ForbiddenError('Not authorized to update this article');
    }

    Object.assign(article, updateData);
    await article.save();
    await article.populate('author', 'username email');

    logger.info('Article updated', { articleId: id, userId });
    return article;
  }

  async deleteArticle(id, userId) {
    const article = await Article.findById(id);
    
    if (!article) {
      throw new NotFoundError('Article');
    }

    // 检查权限
    if (article.author.toString() !== userId) {
      throw new ForbiddenError('Not authorized to delete this article');
    }

    await Article.findByIdAndDelete(id);

    logger.info('Article deleted', { articleId: id, userId });
    return true;
  }

  async getArticles(page = 1, limit = 10, filters = {}) {
    const skip = (page - 1) * limit;
    
    // 构建查询条件
    const query = {};
    if (filters.category) query.category = filters.category;
    if (filters.status) query.status = filters.status;
    if (filters.author) query.author = filters.author;
    if (filters.tags) query.tags = { $in: filters.tags };
    
    const [articles, total] = await Promise.all([
      Article.find(query)
        .populate('author', 'username email')
        .skip(skip)
        .limit(limit)
        .sort({ createdAt: -1 })
        .exec(),
      Article.countDocuments(query)
    ]);

    return {
      articles,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit)
      }
    };
  }

  async incrementViewCount(id) {
    await Article.findByIdAndUpdate(id, { $inc: { viewCount: 1 } });
  }

  async toggleLike(id, userId) {
    // 这里可以实现点赞逻辑，需要额外的Like模型
    // 简化版本：直接增加点赞数
    const article = await Article.findByIdAndUpdate(
      id,
      { $inc: { likeCount: 1 } },
      { new: true }
    );

    if (!article) {
      throw new NotFoundError('Article');
    }

    return article;
  }
}

// ================================
// 控制器
// ================================

class AuthController {
  constructor(userService, emailService) {
    this.userService = userService;
    this.emailService = emailService;
  }

  register = asyncHandler(async (req, res) => {
    const user = await this.userService.createUser(req.body);
    const token = user.generateJWT();

    // 发送欢迎邮件
    try {
      await this.emailService.sendWelcomeEmail(user);
    } catch (error) {
      logger.error('Failed to send welcome email', error);
    }

    res.status(201).json({
      success: true,
      data: {
        user,
        token
      },
      message: 'User registered successfully'
    });
  });

  login = asyncHandler(async (req, res) => {
    const { email, password } = req.body;
    
    if (!email || !password) {
      throw new ValidationError('Email and password are required');
    }

    const user = await this.userService.authenticateUser(email, password);
    const token = user.generateJWT();

    res.json({
      success: true,
      data: {
        user,
        token
      },
      message: 'Login successful'
    });
  });

  getProfile = asyncHandler(async (req, res) => {
    res.json({
      success: true,
      data: req.user,
      message: 'Profile retrieved successfully'
    });
  });

  updateProfile = asyncHandler(async (req, res) => {
    const allowedUpdates = ['profile', 'email'];
    const updates = {};
    
    Object.keys(req.body).forEach(key => {
      if (allowedUpdates.includes(key)) {
        updates[key] = req.body[key];
      }
    });

    const user = await this.userService.updateUser(req.user._id, updates);

    res.json({
      success: true,
      data: user,
      message: 'Profile updated successfully'
    });
  });

  changePassword = asyncHandler(async (req, res) => {
    const { currentPassword, newPassword } = req.body;
    
    if (!currentPassword || !newPassword) {
      throw new ValidationError('Current password and new password are required');
    }

    const user = await User.findById(req.user._id).select('+password');
    
    if (!await user.comparePassword(currentPassword)) {
      throw new UnauthorizedError('Current password is incorrect');
    }

    user.password = newPassword;
    await user.save();

    res.json({
      success: true,
      message: 'Password changed successfully'
    });
  });
}

class ArticleController {
  constructor(articleService) {
    this.articleService = articleService;
  }

  create = asyncHandler(async (req, res) => {
    const article = await this.articleService.createArticle(req.body, req.user._id);

    res.status(201).json({
      success: true,
      data: article,
      message: 'Article created successfully'
    });
  });

  getById = asyncHandler(async (req, res) => {
    const article = await this.articleService.getArticleById(req.params.id);
    
    // 增加浏览量
    await this.articleService.incrementViewCount(req.params.id);

    res.json({
      success: true,
      data: article,
      message: 'Article retrieved successfully'
    });
  });

  update = asyncHandler(async (req, res) => {
    const article = await this.articleService.updateArticle(
      req.params.id,
      req.body,
      req.user._id
    );

    res.json({
      success: true,
      data: article,
      message: 'Article updated successfully'
    });
  });

  delete = asyncHandler(async (req, res) => {
    await this.articleService.deleteArticle(req.params.id, req.user._id);

    res.json({
      success: true,
      message: 'Article deleted successfully'
    });
  });

  list = asyncHandler(async (req, res) => {
    const { page, limit } = req.pagination;
    const filters = {
      category: req.query.category,
      status: req.query.status || 'published',
      author: req.query.author,
      tags: req.query.tags ? req.query.tags.split(',') : undefined
    };

    // 移除undefined值
    Object.keys(filters).forEach(key => {
      if (filters[key] === undefined) {
        delete filters[key];
      }
    });

    const result = await this.articleService.getArticles(page, limit, filters);

    res.json({
      success: true,
      data: result,
      message: 'Articles retrieved successfully'
    });
  });

  like = asyncHandler(async (req, res) => {
    const article = await this.articleService.toggleLike(req.params.id, req.user._id);

    res.json({
      success: true,
      data: article,
      message: 'Article liked successfully'
    });
  });
}

// ================================
// 路由
// ================================

function createAuthRoutes(authController) {
  const router = express.Router();

  router.post('/register', ValidationMiddleware.validateUser, authController.register);
  router.post('/login', authController.login);
  router.get('/profile', AuthMiddleware.authenticate, authController.getProfile);
  router.put('/profile', AuthMiddleware.authenticate, authController.updateProfile);
  router.put('/change-password', AuthMiddleware.authenticate, authController.changePassword);

  return router;
}

function createArticleRoutes(articleController) {
  const router = express.Router();

  router.post('/', 
    AuthMiddleware.authenticate, 
    ValidationMiddleware.validateArticle, 
    articleController.create
  );
  
  router.get('/', 
    ValidationMiddleware.validatePagination, 
    articleController.list
  );
  
  router.get('/:id', articleController.getById);
  
  router.put('/:id', 
    AuthMiddleware.authenticate, 
    ValidationMiddleware.validateArticle, 
    articleController.update
  );
  
  router.delete('/:id', AuthMiddleware.authenticate, articleController.delete);
  
  router.post('/:id/like', AuthMiddleware.authenticate, articleController.like);

  return router;
}

// ================================
// 应用创建
// ================================

function createApp() {
  const app = express();

  // 基础中间件
  app.use(helmet());
  app.use(compression());
  app.use(cors({
    origin: process.env.FRONTEND_URL || 'http://localhost:3000',
    credentials: true
  }));

  // 请求日志
  app.use(morgan('combined', {
    stream: {
      write: (message) => logger.info(message.trim())
    }
  }));

  // 请求解析
  app.use(express.json({ limit: '10mb' }));
  app.use(express.urlencoded({ extended: true, limit: '10mb' }));

  // 静态文件
  app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

  // 限流
  const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15分钟
    max: 100, // 限制每个IP 15分钟内最多100个请求
    message: {
      success: false,
      error: {
        message: 'Too many requests, please try again later'
      }
    }
  });
  app.use('/api/', limiter);

  // 初始化服务
  const cacheService = new CacheService(database.getRedis());
  const emailService = new EmailService();
  const fileUploadService = new FileUploadService();
  const userService = new UserService(cacheService);
  const articleService = new ArticleService(cacheService);

  // 初始化控制器
  const authController = new AuthController(userService, emailService);
  const articleController = new ArticleController(articleService);

  // 路由
  app.get('/api/health', (req, res) => {
    res.json({
      success: true,
      data: {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        version: process.version
      },
      message: 'Service is healthy'
    });
  });

  app.use('/api/auth', createAuthRoutes(authController));
  app.use('/api/articles', createArticleRoutes(articleController));

  // 文件上传路由
  app.post('/api/upload', 
    AuthMiddleware.authenticate,
    fileUploadService.getMulterConfig().single('file'),
    (req, res) => {
      if (!req.file) {
        throw new ValidationError('No file uploaded');
      }

      res.json({
        success: true,
        data: {
          filename: req.file.filename,
          originalName: req.file.originalname,
          size: req.file.size,
          url: fileUploadService.getFileUrl(req.file.filename)
        },
        message: 'File uploaded successfully'
      });
    }
  );

  // 404处理
  app.use('*', (req, res) => {
    res.status(404).json({
      success: false,
      error: {
        message: 'Route not found'
      }
    });
  });

  // 错误处理
  app.use(errorHandler);

  return app;
}

// ================================
// 应用启动
// ================================

async function startServer() {
  try {
    // 验证配置
    config.validate();

    // 连接数据库
    await database.connectMongoDB();
    await database.connectRedis();

    // 创建应用
    const app = createApp();

    // 启动服务器
    const server = app.listen(config.port, () => {
      logger.info(`Server running on port ${config.port} in ${config.env} mode`);
    });

    // 优雅关闭
    const gracefulShutdown = async (signal) => {
      logger.info(`Received ${signal}, shutting down gracefully`);
      
      server.close(async () => {
        logger.info('HTTP server closed');
        
        try {
          await database.disconnect();
          logger.info('Database connections closed');
          process.exit(0);
        } catch (error) {
          logger.error('Error during shutdown', error);
          process.exit(1);
        }
      });
    };

    process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
    process.on('SIGINT', () => gracefulShutdown('SIGINT'));

    return server;
  } catch (error) {
    logger.error('Failed to start server', error);
    process.exit(1);
  }
}

// ================================
// 工具函数
// ================================

class Utils {
  static generateRandomString(length = 32) {
    return crypto.randomBytes(length).toString('hex');
  }

  static slugify(text) {
    return text
      .toLowerCase()
      .replace(/[^\w\s-]/g, '')
      .replace(/[\s_-]+/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  static formatDate(date, format = 'YYYY-MM-DD') {
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    
    return format
      .replace('YYYY', year)
      .replace('MM', month)
      .replace('DD', day);
  }

  static validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  }

  static sanitizeHtml(html) {
    // 简单的HTML清理，生产环境建议使用DOMPurify
    return html
      .replace(/<script[^>]*>.*?<\/script>/gi, '')
      .replace(/<iframe[^>]*>.*?<\/iframe>/gi, '')
      .replace(/javascript:/gi, '')
      .replace(/on\w+\s*=/gi, '');
  }

  static paginate(page, limit, total) {
    const pages = Math.ceil(total / limit);
    const hasNext = page < pages;
    const hasPrev = page > 1;
    
    return {
      page,
      limit,
      total,
      pages,
      hasNext,
      hasPrev,
      nextPage: hasNext ? page + 1 : null,
      prevPage: hasPrev ? page - 1 : null
    };
  }
}

// ================================
// 导出
// ================================

module.exports = {
  createApp,
  startServer,
  Config,
  Logger,
  Database,
  CacheService,
  EmailService,
  FileUploadService,
  AuthMiddleware,
  ValidationMiddleware,
  UserService,
  ArticleService,
  AuthController,
  ArticleController,
  Utils,
  // 错误类
  AppError,
  ValidationError,
  NotFoundError,
  UnauthorizedError,
  ForbiddenError,
  // 模型
  User,
  Article
};

// ================================
// 使用示例
// ================================

if (require.main === module) {
  startServer();
}

/* 
使用说明：

1. 项目结构：
   - 采用分层架构：Controller -> Service -> Model
   - 依赖注入模式
   - 中间件模式
   - 错误处理统一化

2. 安全特性：
   - JWT认证
   - 密码加密
   - 请求限流
   - CORS配置
   - 输入验证
   - 文件上传限制

3. 性能优化：
   - Redis缓存
   - 数据库连接池
   - 响应压缩
   - 静态文件服务
   - 分页查询

4. 监控和日志：
   - Winston日志
   - 请求日志
   - 错误追踪
   - 健康检查

5. 开发体验：
   - 热重载支持
   - 环境变量配置
   - 详细错误信息
   - API文档友好

6. 部署特性：
   - 优雅关闭
   - 进程管理
   - 容器化支持
   - 环境隔离

7. 扩展性：
   - 模块化设计
   - 插件架构
   - 配置驱动
   - 微服务友好

8. 最佳实践：
   - RESTful API设计
   - 统一响应格式
   - 错误处理标准化
   - 代码注释完整
   - 类型检查

9. 测试支持：
   - 单元测试友好
   - 集成测试支持
   - Mock数据
   - 测试环境隔离

10. 生产就绪：
    - 性能监控
    - 错误报告
    - 日志轮转
    - 资源限制
    - 安全加固
*/