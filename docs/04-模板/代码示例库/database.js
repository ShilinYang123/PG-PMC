// 数据库操作代码示例 - 3AI工作室
// 提供统一的数据库操作接口，支持多种数据库和ORM

const { Pool } = require('pg');
const mysql = require('mysql2/promise');
const mongoose = require('mongoose');
const redis = require('redis');
const { Sequelize, DataTypes, Op } = require('sequelize');

// ================================
// 数据库连接配置
// ================================

/**
 * 数据库配置
 */
const DB_CONFIG = {
  postgres: {
    host: process.env.PG_HOST || 'localhost',
    port: process.env.PG_PORT || 5432,
    database: process.env.PG_DATABASE || 'myapp',
    user: process.env.PG_USER || 'postgres',
    password: process.env.PG_PASSWORD || 'password',
    max: 20,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
  },
  
  mysql: {
    host: process.env.MYSQL_HOST || 'localhost',
    port: process.env.MYSQL_PORT || 3306,
    database: process.env.MYSQL_DATABASE || 'myapp',
    user: process.env.MYSQL_USER || 'root',
    password: process.env.MYSQL_PASSWORD || 'password',
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0,
  },
  
  mongodb: {
    uri: process.env.MONGODB_URI || 'mongodb://localhost:27017/myapp',
    options: {
      useNewUrlParser: true,
      useUnifiedTopology: true,
      maxPoolSize: 10,
      serverSelectionTimeoutMS: 5000,
      socketTimeoutMS: 45000,
    }
  },
  
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: process.env.REDIS_PORT || 6379,
    password: process.env.REDIS_PASSWORD,
    db: process.env.REDIS_DB || 0,
    retryDelayOnFailover: 100,
    maxRetriesPerRequest: 3,
  }
};

// ================================
// PostgreSQL 操作类
// ================================

class PostgreSQLDatabase {
  constructor(config = DB_CONFIG.postgres) {
    this.pool = new Pool(config);
    this.connected = false;
  }

  /**
   * 连接数据库
   */
  async connect() {
    try {
      const client = await this.pool.connect();
      await client.query('SELECT NOW()');
      client.release();
      this.connected = true;
      console.log('PostgreSQL connected successfully');
    } catch (error) {
      console.error('PostgreSQL connection failed:', error);
      throw error;
    }
  }

  /**
   * 执行查询
   */
  async query(text, params = []) {
    const start = Date.now();
    try {
      const result = await this.pool.query(text, params);
      const duration = Date.now() - start;
      console.log('Query executed', { text, duration, rows: result.rowCount });
      return result;
    } catch (error) {
      console.error('Query failed', { text, params, error: error.message });
      throw error;
    }
  }

  /**
   * 事务执行
   */
  async transaction(callback) {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      const result = await callback(client);
      await client.query('COMMIT');
      return result;
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * 批量插入
   */
  async batchInsert(table, columns, values) {
    const placeholders = values.map((_, i) => 
      `(${columns.map((_, j) => `$${i * columns.length + j + 1}`).join(', ')})`
    ).join(', ');
    
    const query = `INSERT INTO ${table} (${columns.join(', ')}) VALUES ${placeholders}`;
    const flatValues = values.flat();
    
    return this.query(query, flatValues);
  }

  /**
   * 分页查询
   */
  async paginate(table, options = {}) {
    const {
      page = 1,
      limit = 10,
      where = '',
      orderBy = 'id',
      orderDirection = 'ASC',
      params = []
    } = options;
    
    const offset = (page - 1) * limit;
    const whereClause = where ? `WHERE ${where}` : '';
    
    // 获取总数
    const countQuery = `SELECT COUNT(*) FROM ${table} ${whereClause}`;
    const countResult = await this.query(countQuery, params);
    const total = parseInt(countResult.rows[0].count);
    
    // 获取数据
    const dataQuery = `
      SELECT * FROM ${table} 
      ${whereClause} 
      ORDER BY ${orderBy} ${orderDirection} 
      LIMIT $${params.length + 1} OFFSET $${params.length + 2}
    `;
    const dataResult = await this.query(dataQuery, [...params, limit, offset]);
    
    return {
      data: dataResult.rows,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit)
      }
    };
  }

  /**
   * 关闭连接
   */
  async close() {
    await this.pool.end();
    this.connected = false;
  }
}

// ================================
// MySQL 操作类
// ================================

class MySQLDatabase {
  constructor(config = DB_CONFIG.mysql) {
    this.pool = mysql.createPool(config);
    this.connected = false;
  }

  /**
   * 连接测试
   */
  async connect() {
    try {
      const connection = await this.pool.getConnection();
      await connection.ping();
      connection.release();
      this.connected = true;
      console.log('MySQL connected successfully');
    } catch (error) {
      console.error('MySQL connection failed:', error);
      throw error;
    }
  }

  /**
   * 执行查询
   */
  async query(sql, params = []) {
    const start = Date.now();
    try {
      const [rows, fields] = await this.pool.execute(sql, params);
      const duration = Date.now() - start;
      console.log('Query executed', { sql, duration, rows: rows.length });
      return { rows, fields };
    } catch (error) {
      console.error('Query failed', { sql, params, error: error.message });
      throw error;
    }
  }

  /**
   * 事务执行
   */
  async transaction(callback) {
    const connection = await this.pool.getConnection();
    try {
      await connection.beginTransaction();
      const result = await callback(connection);
      await connection.commit();
      return result;
    } catch (error) {
      await connection.rollback();
      throw error;
    } finally {
      connection.release();
    }
  }

  /**
   * 批量插入
   */
  async batchInsert(table, data) {
    if (!data.length) return { affectedRows: 0 };
    
    const columns = Object.keys(data[0]);
    const values = data.map(row => columns.map(col => row[col]));
    
    const sql = `INSERT INTO ${table} (${columns.join(', ')}) VALUES ?`;
    return this.query(sql, [values]);
  }

  /**
   * 关闭连接
   */
  async close() {
    await this.pool.end();
    this.connected = false;
  }
}

// ================================
// MongoDB 操作类
// ================================

class MongoDatabase {
  constructor(config = DB_CONFIG.mongodb) {
    this.uri = config.uri;
    this.options = config.options;
    this.connection = null;
    this.connected = false;
  }

  /**
   * 连接数据库
   */
  async connect() {
    try {
      this.connection = await mongoose.connect(this.uri, this.options);
      this.connected = true;
      console.log('MongoDB connected successfully');
    } catch (error) {
      console.error('MongoDB connection failed:', error);
      throw error;
    }
  }

  /**
   * 创建模型
   */
  createModel(name, schema) {
    return mongoose.model(name, new mongoose.Schema(schema, {
      timestamps: true,
      versionKey: false
    }));
  }

  /**
   * 聚合查询
   */
  async aggregate(model, pipeline) {
    const start = Date.now();
    try {
      const result = await model.aggregate(pipeline);
      const duration = Date.now() - start;
      console.log('Aggregation executed', { pipeline, duration, count: result.length });
      return result;
    } catch (error) {
      console.error('Aggregation failed', { pipeline, error: error.message });
      throw error;
    }
  }

  /**
   * 分页查询
   */
  async paginate(model, query = {}, options = {}) {
    const {
      page = 1,
      limit = 10,
      sort = { _id: -1 },
      populate = '',
      select = ''
    } = options;
    
    const skip = (page - 1) * limit;
    
    const [data, total] = await Promise.all([
      model.find(query)
        .sort(sort)
        .skip(skip)
        .limit(limit)
        .populate(populate)
        .select(select)
        .lean(),
      model.countDocuments(query)
    ]);
    
    return {
      data,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit)
      }
    };
  }

  /**
   * 批量操作
   */
  async bulkWrite(model, operations) {
    const start = Date.now();
    try {
      const result = await model.bulkWrite(operations);
      const duration = Date.now() - start;
      console.log('Bulk operation executed', { operations: operations.length, duration });
      return result;
    } catch (error) {
      console.error('Bulk operation failed', { error: error.message });
      throw error;
    }
  }

  /**
   * 关闭连接
   */
  async close() {
    if (this.connection) {
      await mongoose.connection.close();
      this.connected = false;
    }
  }
}

// ================================
// Redis 操作类
// ================================

class RedisDatabase {
  constructor(config = DB_CONFIG.redis) {
    this.client = redis.createClient(config);
    this.connected = false;
    
    this.client.on('error', (err) => {
      console.error('Redis error:', err);
    });
    
    this.client.on('connect', () => {
      console.log('Redis connected');
      this.connected = true;
    });
  }

  /**
   * 连接 Redis
   */
  async connect() {
    try {
      await this.client.connect();
      await this.client.ping();
      console.log('Redis connected successfully');
    } catch (error) {
      console.error('Redis connection failed:', error);
      throw error;
    }
  }

  /**
   * 设置缓存
   */
  async set(key, value, ttl = 3600) {
    try {
      const serialized = typeof value === 'object' ? JSON.stringify(value) : value;
      await this.client.setEx(key, ttl, serialized);
    } catch (error) {
      console.error('Redis set failed:', error);
      throw error;
    }
  }

  /**
   * 获取缓存
   */
  async get(key) {
    try {
      const value = await this.client.get(key);
      if (!value) return null;
      
      try {
        return JSON.parse(value);
      } catch {
        return value;
      }
    } catch (error) {
      console.error('Redis get failed:', error);
      throw error;
    }
  }

  /**
   * 删除缓存
   */
  async del(key) {
    try {
      return await this.client.del(key);
    } catch (error) {
      console.error('Redis del failed:', error);
      throw error;
    }
  }

  /**
   * 批量设置
   */
  async mset(keyValues) {
    try {
      const args = [];
      for (const [key, value] of Object.entries(keyValues)) {
        args.push(key, typeof value === 'object' ? JSON.stringify(value) : value);
      }
      await this.client.mSet(args);
    } catch (error) {
      console.error('Redis mset failed:', error);
      throw error;
    }
  }

  /**
   * 批量获取
   */
  async mget(keys) {
    try {
      const values = await this.client.mGet(keys);
      return values.map(value => {
        if (!value) return null;
        try {
          return JSON.parse(value);
        } catch {
          return value;
        }
      });
    } catch (error) {
      console.error('Redis mget failed:', error);
      throw error;
    }
  }

  /**
   * 列表操作
   */
  async lpush(key, ...values) {
    return this.client.lPush(key, values.map(v => 
      typeof v === 'object' ? JSON.stringify(v) : v
    ));
  }

  async rpop(key) {
    const value = await this.client.rPop(key);
    if (!value) return null;
    try {
      return JSON.parse(value);
    } catch {
      return value;
    }
  }

  /**
   * 集合操作
   */
  async sadd(key, ...members) {
    return this.client.sAdd(key, members.map(m => 
      typeof m === 'object' ? JSON.stringify(m) : m
    ));
  }

  async smembers(key) {
    const members = await this.client.sMembers(key);
    return members.map(member => {
      try {
        return JSON.parse(member);
      } catch {
        return member;
      }
    });
  }

  /**
   * 有序集合操作
   */
  async zadd(key, score, member) {
    const serialized = typeof member === 'object' ? JSON.stringify(member) : member;
    return this.client.zAdd(key, { score, value: serialized });
  }

  async zrange(key, start, stop) {
    const members = await this.client.zRange(key, start, stop);
    return members.map(member => {
      try {
        return JSON.parse(member);
      } catch {
        return member;
      }
    });
  }

  /**
   * 关闭连接
   */
  async close() {
    await this.client.quit();
    this.connected = false;
  }
}

// ================================
// Sequelize ORM 操作类
// ================================

class SequelizeDatabase {
  constructor(config) {
    this.sequelize = new Sequelize(
      config.database,
      config.username,
      config.password,
      {
        host: config.host,
        port: config.port,
        dialect: config.dialect || 'postgres',
        logging: config.logging || console.log,
        pool: {
          max: 5,
          min: 0,
          acquire: 30000,
          idle: 10000
        }
      }
    );
    this.models = {};
  }

  /**
   * 连接数据库
   */
  async connect() {
    try {
      await this.sequelize.authenticate();
      console.log('Sequelize connected successfully');
    } catch (error) {
      console.error('Sequelize connection failed:', error);
      throw error;
    }
  }

  /**
   * 定义模型
   */
  defineModel(name, attributes, options = {}) {
    this.models[name] = this.sequelize.define(name, attributes, {
      timestamps: true,
      underscored: true,
      ...options
    });
    return this.models[name];
  }

  /**
   * 设置关联关系
   */
  setupAssociations(associations) {
    for (const association of associations) {
      const { source, target, type, options = {} } = association;
      const sourceModel = this.models[source];
      const targetModel = this.models[target];
      
      switch (type) {
        case 'hasOne':
          sourceModel.hasOne(targetModel, options);
          break;
        case 'hasMany':
          sourceModel.hasMany(targetModel, options);
          break;
        case 'belongsTo':
          sourceModel.belongsTo(targetModel, options);
          break;
        case 'belongsToMany':
          sourceModel.belongsToMany(targetModel, options);
          break;
      }
    }
  }

  /**
   * 同步数据库
   */
  async sync(options = {}) {
    try {
      await this.sequelize.sync(options);
      console.log('Database synchronized');
    } catch (error) {
      console.error('Database sync failed:', error);
      throw error;
    }
  }

  /**
   * 执行事务
   */
  async transaction(callback) {
    return this.sequelize.transaction(callback);
  }

  /**
   * 分页查询
   */
  async paginate(model, options = {}) {
    const {
      page = 1,
      limit = 10,
      where = {},
      include = [],
      order = [['id', 'DESC']]
    } = options;
    
    const offset = (page - 1) * limit;
    
    const result = await this.models[model].findAndCountAll({
      where,
      include,
      order,
      limit,
      offset,
      distinct: true
    });
    
    return {
      data: result.rows,
      pagination: {
        page,
        limit,
        total: result.count,
        pages: Math.ceil(result.count / limit)
      }
    };
  }

  /**
   * 关闭连接
   */
  async close() {
    await this.sequelize.close();
  }
}

// ================================
// 数据库管理器
// ================================

class DatabaseManager {
  constructor() {
    this.connections = new Map();
    this.defaultConnection = null;
  }

  /**
   * 添加数据库连接
   */
  addConnection(name, database) {
    this.connections.set(name, database);
    if (!this.defaultConnection) {
      this.defaultConnection = name;
    }
  }

  /**
   * 获取数据库连接
   */
  getConnection(name = null) {
    const connectionName = name || this.defaultConnection;
    const connection = this.connections.get(connectionName);
    
    if (!connection) {
      throw new Error(`Database connection '${connectionName}' not found`);
    }
    
    return connection;
  }

  /**
   * 连接所有数据库
   */
  async connectAll() {
    const promises = Array.from(this.connections.values()).map(db => db.connect());
    await Promise.all(promises);
  }

  /**
   * 关闭所有连接
   */
  async closeAll() {
    const promises = Array.from(this.connections.values()).map(db => db.close());
    await Promise.all(promises);
  }

  /**
   * 健康检查
   */
  async healthCheck() {
    const results = {};
    
    for (const [name, db] of this.connections) {
      try {
        results[name] = {
          status: db.connected ? 'connected' : 'disconnected',
          type: db.constructor.name
        };
      } catch (error) {
        results[name] = {
          status: 'error',
          error: error.message
        };
      }
    }
    
    return results;
  }
}

// ================================
// 缓存装饰器
// ================================

/**
 * 缓存装饰器
 */
function cache(options = {}) {
  const { ttl = 3600, key, redis: redisInstance } = options;
  
  return function(target, propertyName, descriptor) {
    const originalMethod = descriptor.value;
    
    descriptor.value = async function(...args) {
      if (!redisInstance) {
        return originalMethod.apply(this, args);
      }
      
      // 生成缓存键
      const cacheKey = key ? 
        (typeof key === 'function' ? key(...args) : key) :
        `${target.constructor.name}:${propertyName}:${JSON.stringify(args)}`;
      
      // 尝试从缓存获取
      try {
        const cached = await redisInstance.get(cacheKey);
        if (cached !== null) {
          console.log(`Cache hit: ${cacheKey}`);
          return cached;
        }
      } catch (error) {
        console.warn('Cache get failed:', error);
      }
      
      // 执行原方法
      const result = await originalMethod.apply(this, args);
      
      // 设置缓存
      try {
        await redisInstance.set(cacheKey, result, ttl);
        console.log(`Cache set: ${cacheKey}`);
      } catch (error) {
        console.warn('Cache set failed:', error);
      }
      
      return result;
    };
    
    return descriptor;
  };
}

// ================================
// 使用示例
// ================================

// 创建数据库实例
const dbManager = new DatabaseManager();

// 添加 PostgreSQL 连接
const postgres = new PostgreSQLDatabase();
dbManager.addConnection('postgres', postgres);

// 添加 Redis 连接
const redis = new RedisDatabase();
dbManager.addConnection('redis', redis);

// 添加 MongoDB 连接
const mongodb = new MongoDatabase();
dbManager.addConnection('mongodb', mongodb);

// 示例服务类
class UserService {
  constructor(dbManager) {
    this.db = dbManager.getConnection('postgres');
    this.cache = dbManager.getConnection('redis');
  }

  /**
   * 获取用户（带缓存）
   */
  @cache({ ttl: 1800, redis: redis })
  async getUser(id) {
    const result = await this.db.query('SELECT * FROM users WHERE id = $1', [id]);
    return result.rows[0];
  }

  /**
   * 创建用户
   */
  async createUser(userData) {
    return this.db.transaction(async (client) => {
      // 插入用户
      const userResult = await client.query(
        'INSERT INTO users (name, email) VALUES ($1, $2) RETURNING *',
        [userData.name, userData.email]
      );
      
      // 插入用户配置
      await client.query(
        'INSERT INTO user_settings (user_id, theme) VALUES ($1, $2)',
        [userResult.rows[0].id, 'default']
      );
      
      return userResult.rows[0];
    });
  }

  /**
   * 获取用户列表
   */
  async getUsers(page = 1, limit = 10) {
    return this.db.paginate('users', {
      page,
      limit,
      orderBy: 'created_at',
      orderDirection: 'DESC'
    });
  }
}

// 初始化示例
async function initializeDatabase() {
  try {
    // 连接所有数据库
    await dbManager.connectAll();
    
    // 健康检查
    const health = await dbManager.healthCheck();
    console.log('Database health:', health);
    
    // 使用服务
    const userService = new UserService(dbManager);
    
    // 创建用户
    const newUser = await userService.createUser({
      name: 'John Doe',
      email: 'john@example.com'
    });
    
    console.log('User created:', newUser);
    
    // 获取用户（会被缓存）
    const user = await userService.getUser(newUser.id);
    console.log('User retrieved:', user);
    
  } catch (error) {
    console.error('Database initialization failed:', error);
  }
}

// ================================
// 导出模块
// ================================
module.exports = {
  PostgreSQLDatabase,
  MySQLDatabase,
  MongoDatabase,
  RedisDatabase,
  SequelizeDatabase,
  DatabaseManager,
  cache,
  
  // 配置
  DB_CONFIG,
  
  // 实例
  dbManager
};

// ================================
// 使用说明
// ================================

/*
1. 环境变量配置：
   - PostgreSQL: PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD
   - MySQL: MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD
   - MongoDB: MONGODB_URI
   - Redis: REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB

2. 数据库选择：
   - PostgreSQL: 适合复杂查询和事务
   - MySQL: 适合传统 Web 应用
   - MongoDB: 适合文档存储和快速开发
   - Redis: 适合缓存和会话存储

3. 最佳实践：
   - 使用连接池管理连接
   - 实现事务支持
   - 添加查询日志和监控
   - 使用缓存提高性能
   - 实现数据库健康检查
   - 处理连接失败和重连

4. 性能优化：
   - 使用索引优化查询
   - 实现查询缓存
   - 使用批量操作
   - 优化连接池配置
   - 监控慢查询

5. 安全考虑：
   - 使用参数化查询防止 SQL 注入
   - 加密敏感数据
   - 限制数据库权限
   - 定期备份数据
   - 监控异常访问

6. 扩展建议：
   - 实现读写分离
   - 添加数据库分片
   - 集成 ORM 框架
   - 实现数据迁移
   - 添加数据验证
*/