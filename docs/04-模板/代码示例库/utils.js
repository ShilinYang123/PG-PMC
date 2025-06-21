// 工具函数代码示例 - 3AI工作室
// 提供常用的工具函数，包括数据处理、验证、格式化、加密等

const crypto = require('crypto');
const path = require('path');
const fs = require('fs');

// ================================
// 数据类型检查
// ================================

/**
 * 检查数据类型
 */
const is = {
  // 基本类型检查
  string: (value) => typeof value === 'string',
  number: (value) => typeof value === 'number' && !isNaN(value),
  boolean: (value) => typeof value === 'boolean',
  function: (value) => typeof value === 'function',
  object: (value) => value !== null && typeof value === 'object',
  array: (value) => Array.isArray(value),
  null: (value) => value === null,
  undefined: (value) => value === undefined,
  
  // 复合类型检查
  empty: (value) => {
    if (value === null || value === undefined) return true;
    if (typeof value === 'string') return value.trim() === '';
    if (Array.isArray(value)) return value.length === 0;
    if (typeof value === 'object') return Object.keys(value).length === 0;
    return false;
  },
  
  email: (value) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return typeof value === 'string' && emailRegex.test(value);
  },
  
  url: (value) => {
    try {
      new URL(value);
      return true;
    } catch {
      return false;
    }
  },
  
  phone: (value) => {
    const phoneRegex = /^[+]?[1-9]?[0-9]{7,15}$/;
    return typeof value === 'string' && phoneRegex.test(value.replace(/[\s-()]/g, ''));
  },
  
  date: (value) => {
    return value instanceof Date && !isNaN(value.getTime());
  },
  
  json: (value) => {
    try {
      JSON.parse(value);
      return true;
    } catch {
      return false;
    }
  },
  
  uuid: (value) => {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    return typeof value === 'string' && uuidRegex.test(value);
  },
  
  creditCard: (value) => {
    const ccRegex = /^[0-9]{13,19}$/;
    return typeof value === 'string' && ccRegex.test(value.replace(/[\s-]/g, ''));
  },
  
  ipAddress: (value) => {
    const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    return typeof value === 'string' && ipRegex.test(value);
  }
};

// ================================
// 字符串工具
// ================================

const string = {
  /**
   * 首字母大写
   */
  capitalize: (str) => {
    if (!is.string(str)) return '';
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
  },
  
  /**
   * 驼峰命名
   */
  camelCase: (str) => {
    if (!is.string(str)) return '';
    return str.replace(/[-_\s]+(.)?/g, (_, char) => char ? char.toUpperCase() : '');
  },
  
  /**
   * 蛇形命名
   */
  snakeCase: (str) => {
    if (!is.string(str)) return '';
    return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`)
              .replace(/[-\s]+/g, '_')
              .replace(/^_/, '');
  },
  
  /**
   * 短横线命名
   */
  kebabCase: (str) => {
    if (!is.string(str)) return '';
    return str.replace(/[A-Z]/g, letter => `-${letter.toLowerCase()}`)
              .replace(/[_\s]+/g, '-')
              .replace(/^-/, '');
  },
  
  /**
   * 截断字符串
   */
  truncate: (str, length = 100, suffix = '...') => {
    if (!is.string(str)) return '';
    if (str.length <= length) return str;
    return str.slice(0, length - suffix.length) + suffix;
  },
  
  /**
   * 移除HTML标签
   */
  stripHtml: (str) => {
    if (!is.string(str)) return '';
    return str.replace(/<[^>]*>/g, '');
  },
  
  /**
   * 转义HTML
   */
  escapeHtml: (str) => {
    if (!is.string(str)) return '';
    const htmlEscapes = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    };
    return str.replace(/[&<>"']/g, char => htmlEscapes[char]);
  },
  
  /**
   * 反转义HTML
   */
  unescapeHtml: (str) => {
    if (!is.string(str)) return '';
    const htmlUnescapes = {
      '&amp;': '&',
      '&lt;': '<',
      '&gt;': '>',
      '&quot;': '"',
      '&#39;': "'"
    };
    return str.replace(/&(?:amp|lt|gt|quot|#39);/g, entity => htmlUnescapes[entity]);
  },
  
  /**
   * 生成随机字符串
   */
  random: (length = 8, charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789') => {
    let result = '';
    for (let i = 0; i < length; i++) {
      result += charset.charAt(Math.floor(Math.random() * charset.length));
    }
    return result;
  },
  
  /**
   * 计算字符串相似度
   */
  similarity: (str1, str2) => {
    if (!is.string(str1) || !is.string(str2)) return 0;
    if (str1 === str2) return 1;
    
    const longer = str1.length > str2.length ? str1 : str2;
    const shorter = str1.length > str2.length ? str2 : str1;
    
    if (longer.length === 0) return 1;
    
    const editDistance = levenshteinDistance(longer, shorter);
    return (longer.length - editDistance) / longer.length;
  },
  
  /**
   * 格式化模板字符串
   */
  template: (template, data) => {
    if (!is.string(template) || !is.object(data)) return template;
    return template.replace(/\{\{([^}]+)\}\}/g, (match, key) => {
      const value = data[key.trim()];
      return value !== undefined ? value : match;
    });
  }
};

/**
 * 计算编辑距离
 */
function levenshteinDistance(str1, str2) {
  const matrix = [];
  
  for (let i = 0; i <= str2.length; i++) {
    matrix[i] = [i];
  }
  
  for (let j = 0; j <= str1.length; j++) {
    matrix[0][j] = j;
  }
  
  for (let i = 1; i <= str2.length; i++) {
    for (let j = 1; j <= str1.length; j++) {
      if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }
  
  return matrix[str2.length][str1.length];
}

// ================================
// 数组工具
// ================================

const array = {
  /**
   * 数组去重
   */
  unique: (arr, key = null) => {
    if (!is.array(arr)) return [];
    
    if (key) {
      const seen = new Set();
      return arr.filter(item => {
        const value = is.function(key) ? key(item) : item[key];
        if (seen.has(value)) return false;
        seen.add(value);
        return true;
      });
    }
    
    return [...new Set(arr)];
  },
  
  /**
   * 数组分块
   */
  chunk: (arr, size = 1) => {
    if (!is.array(arr) || size < 1) return [];
    
    const chunks = [];
    for (let i = 0; i < arr.length; i += size) {
      chunks.push(arr.slice(i, i + size));
    }
    return chunks;
  },
  
  /**
   * 数组扁平化
   */
  flatten: (arr, depth = Infinity) => {
    if (!is.array(arr)) return [];
    
    const flatten = (arr, currentDepth) => {
      const result = [];
      for (const item of arr) {
        if (is.array(item) && currentDepth > 0) {
          result.push(...flatten(item, currentDepth - 1));
        } else {
          result.push(item);
        }
      }
      return result;
    };
    
    return flatten(arr, depth);
  },
  
  /**
   * 数组洗牌
   */
  shuffle: (arr) => {
    if (!is.array(arr)) return [];
    
    const shuffled = [...arr];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  },
  
  /**
   * 数组分组
   */
  groupBy: (arr, key) => {
    if (!is.array(arr)) return {};
    
    return arr.reduce((groups, item) => {
      const groupKey = is.function(key) ? key(item) : item[key];
      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(item);
      return groups;
    }, {});
  },
  
  /**
   * 数组排序
   */
  sortBy: (arr, key, order = 'asc') => {
    if (!is.array(arr)) return [];
    
    return [...arr].sort((a, b) => {
      const valueA = is.function(key) ? key(a) : a[key];
      const valueB = is.function(key) ? key(b) : b[key];
      
      if (valueA < valueB) return order === 'asc' ? -1 : 1;
      if (valueA > valueB) return order === 'asc' ? 1 : -1;
      return 0;
    });
  },
  
  /**
   * 数组交集
   */
  intersection: (...arrays) => {
    if (arrays.length === 0) return [];
    if (arrays.length === 1) return arrays[0];
    
    return arrays.reduce((acc, arr) => {
      if (!is.array(arr)) return acc;
      return acc.filter(item => arr.includes(item));
    });
  },
  
  /**
   * 数组差集
   */
  difference: (arr1, arr2) => {
    if (!is.array(arr1)) return [];
    if (!is.array(arr2)) return arr1;
    
    return arr1.filter(item => !arr2.includes(item));
  },
  
  /**
   * 数组并集
   */
  union: (...arrays) => {
    const combined = arrays.reduce((acc, arr) => {
      if (is.array(arr)) {
        acc.push(...arr);
      }
      return acc;
    }, []);
    
    return array.unique(combined);
  },
  
  /**
   * 数组分页
   */
  paginate: (arr, page = 1, limit = 10) => {
    if (!is.array(arr)) return { data: [], pagination: {} };
    
    const offset = (page - 1) * limit;
    const data = arr.slice(offset, offset + limit);
    
    return {
      data,
      pagination: {
        page,
        limit,
        total: arr.length,
        pages: Math.ceil(arr.length / limit)
      }
    };
  }
};

// ================================
// 对象工具
// ================================

const object = {
  /**
   * 深拷贝
   */
  deepClone: (obj) => {
    if (obj === null || typeof obj !== 'object') return obj;
    if (obj instanceof Date) return new Date(obj.getTime());
    if (obj instanceof Array) return obj.map(item => object.deepClone(item));
    if (typeof obj === 'object') {
      const cloned = {};
      Object.keys(obj).forEach(key => {
        cloned[key] = object.deepClone(obj[key]);
      });
      return cloned;
    }
  },
  
  /**
   * 深度合并
   */
  deepMerge: (target, ...sources) => {
    if (!sources.length) return target;
    const source = sources.shift();
    
    if (is.object(target) && is.object(source)) {
      for (const key in source) {
        if (is.object(source[key])) {
          if (!target[key]) Object.assign(target, { [key]: {} });
          object.deepMerge(target[key], source[key]);
        } else {
          Object.assign(target, { [key]: source[key] });
        }
      }
    }
    
    return object.deepMerge(target, ...sources);
  },
  
  /**
   * 获取嵌套属性
   */
  get: (obj, path, defaultValue = undefined) => {
    if (!is.object(obj) || !is.string(path)) return defaultValue;
    
    const keys = path.split('.');
    let result = obj;
    
    for (const key of keys) {
      if (result === null || result === undefined || !(key in result)) {
        return defaultValue;
      }
      result = result[key];
    }
    
    return result;
  },
  
  /**
   * 设置嵌套属性
   */
  set: (obj, path, value) => {
    if (!is.object(obj) || !is.string(path)) return obj;
    
    const keys = path.split('.');
    let current = obj;
    
    for (let i = 0; i < keys.length - 1; i++) {
      const key = keys[i];
      if (!(key in current) || !is.object(current[key])) {
        current[key] = {};
      }
      current = current[key];
    }
    
    current[keys[keys.length - 1]] = value;
    return obj;
  },
  
  /**
   * 删除嵌套属性
   */
  unset: (obj, path) => {
    if (!is.object(obj) || !is.string(path)) return obj;
    
    const keys = path.split('.');
    let current = obj;
    
    for (let i = 0; i < keys.length - 1; i++) {
      const key = keys[i];
      if (!(key in current) || !is.object(current[key])) {
        return obj;
      }
      current = current[key];
    }
    
    delete current[keys[keys.length - 1]];
    return obj;
  },
  
  /**
   * 对象键转换
   */
  transformKeys: (obj, transformer) => {
    if (!is.object(obj) || !is.function(transformer)) return obj;
    
    const transformed = {};
    Object.keys(obj).forEach(key => {
      const newKey = transformer(key);
      transformed[newKey] = is.object(obj[key]) && !is.array(obj[key]) ?
        object.transformKeys(obj[key], transformer) : obj[key];
    });
    
    return transformed;
  },
  
  /**
   * 过滤对象
   */
  filter: (obj, predicate) => {
    if (!is.object(obj) || !is.function(predicate)) return {};
    
    const filtered = {};
    Object.keys(obj).forEach(key => {
      if (predicate(obj[key], key, obj)) {
        filtered[key] = obj[key];
      }
    });
    
    return filtered;
  },
  
  /**
   * 对象映射
   */
  map: (obj, mapper) => {
    if (!is.object(obj) || !is.function(mapper)) return {};
    
    const mapped = {};
    Object.keys(obj).forEach(key => {
      mapped[key] = mapper(obj[key], key, obj);
    });
    
    return mapped;
  },
  
  /**
   * 选择属性
   */
  pick: (obj, keys) => {
    if (!is.object(obj) || !is.array(keys)) return {};
    
    const picked = {};
    keys.forEach(key => {
      if (key in obj) {
        picked[key] = obj[key];
      }
    });
    
    return picked;
  },
  
  /**
   * 排除属性
   */
  omit: (obj, keys) => {
    if (!is.object(obj) || !is.array(keys)) return obj;
    
    const omitted = { ...obj };
    keys.forEach(key => {
      delete omitted[key];
    });
    
    return omitted;
  }
};

// ================================
// 日期工具
// ================================

const date = {
  /**
   * 格式化日期
   */
  format: (date, format = 'YYYY-MM-DD HH:mm:ss') => {
    if (!is.date(date)) date = new Date(date);
    if (!is.date(date)) return '';
    
    const tokens = {
      YYYY: date.getFullYear(),
      MM: String(date.getMonth() + 1).padStart(2, '0'),
      DD: String(date.getDate()).padStart(2, '0'),
      HH: String(date.getHours()).padStart(2, '0'),
      mm: String(date.getMinutes()).padStart(2, '0'),
      ss: String(date.getSeconds()).padStart(2, '0'),
      SSS: String(date.getMilliseconds()).padStart(3, '0')
    };
    
    return format.replace(/YYYY|MM|DD|HH|mm|ss|SSS/g, match => tokens[match]);
  },
  
  /**
   * 解析日期
   */
  parse: (dateString, format = 'YYYY-MM-DD') => {
    if (!is.string(dateString)) return null;
    
    // 简单的日期解析，实际项目中建议使用 moment.js 或 date-fns
    const date = new Date(dateString);
    return is.date(date) ? date : null;
  },
  
  /**
   * 相对时间
   */
  relative: (date) => {
    if (!is.date(date)) date = new Date(date);
    if (!is.date(date)) return '';
    
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (seconds < 60) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;
    if (days < 30) return `${Math.floor(days / 7)}周前`;
    if (days < 365) return `${Math.floor(days / 30)}个月前`;
    return `${Math.floor(days / 365)}年前`;
  },
  
  /**
   * 添加时间
   */
  add: (date, amount, unit = 'days') => {
    if (!is.date(date)) date = new Date(date);
    if (!is.date(date)) return null;
    
    const newDate = new Date(date);
    
    switch (unit) {
      case 'seconds':
        newDate.setSeconds(newDate.getSeconds() + amount);
        break;
      case 'minutes':
        newDate.setMinutes(newDate.getMinutes() + amount);
        break;
      case 'hours':
        newDate.setHours(newDate.getHours() + amount);
        break;
      case 'days':
        newDate.setDate(newDate.getDate() + amount);
        break;
      case 'weeks':
        newDate.setDate(newDate.getDate() + amount * 7);
        break;
      case 'months':
        newDate.setMonth(newDate.getMonth() + amount);
        break;
      case 'years':
        newDate.setFullYear(newDate.getFullYear() + amount);
        break;
    }
    
    return newDate;
  },
  
  /**
   * 计算时间差
   */
  diff: (date1, date2, unit = 'days') => {
    if (!is.date(date1)) date1 = new Date(date1);
    if (!is.date(date2)) date2 = new Date(date2);
    if (!is.date(date1) || !is.date(date2)) return 0;
    
    const diff = Math.abs(date1.getTime() - date2.getTime());
    
    switch (unit) {
      case 'seconds':
        return Math.floor(diff / 1000);
      case 'minutes':
        return Math.floor(diff / (1000 * 60));
      case 'hours':
        return Math.floor(diff / (1000 * 60 * 60));
      case 'days':
        return Math.floor(diff / (1000 * 60 * 60 * 24));
      case 'weeks':
        return Math.floor(diff / (1000 * 60 * 60 * 24 * 7));
      case 'months':
        return Math.floor(diff / (1000 * 60 * 60 * 24 * 30));
      case 'years':
        return Math.floor(diff / (1000 * 60 * 60 * 24 * 365));
      default:
        return diff;
    }
  },
  
  /**
   * 获取时间范围
   */
  range: (start, end, unit = 'days', step = 1) => {
    if (!is.date(start)) start = new Date(start);
    if (!is.date(end)) end = new Date(end);
    if (!is.date(start) || !is.date(end)) return [];
    
    const dates = [];
    const current = new Date(start);
    
    while (current <= end) {
      dates.push(new Date(current));
      current.setTime(current.getTime() + step * getUnitMilliseconds(unit));
    }
    
    return dates;
  }
};

/**
 * 获取时间单位的毫秒数
 */
function getUnitMilliseconds(unit) {
  const units = {
    seconds: 1000,
    minutes: 1000 * 60,
    hours: 1000 * 60 * 60,
    days: 1000 * 60 * 60 * 24,
    weeks: 1000 * 60 * 60 * 24 * 7
  };
  return units[unit] || units.days;
}

// ================================
// 数字工具
// ================================

const number = {
  /**
   * 格式化数字
   */
  format: (num, options = {}) => {
    if (!is.number(num)) return '0';
    
    const {
      decimals = 2,
      thousandsSeparator = ',',
      decimalSeparator = '.'
    } = options;
    
    const fixed = num.toFixed(decimals);
    const parts = fixed.split('.');
    
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, thousandsSeparator);
    
    return parts.join(decimalSeparator);
  },
  
  /**
   * 随机数
   */
  random: (min = 0, max = 1, decimals = 0) => {
    const random = Math.random() * (max - min) + min;
    return decimals > 0 ? parseFloat(random.toFixed(decimals)) : Math.floor(random);
  },
  
  /**
   * 限制范围
   */
  clamp: (num, min, max) => {
    if (!is.number(num)) return min;
    return Math.min(Math.max(num, min), max);
  },
  
  /**
   * 百分比
   */
  percentage: (value, total, decimals = 2) => {
    if (!is.number(value) || !is.number(total) || total === 0) return 0;
    return parseFloat(((value / total) * 100).toFixed(decimals));
  },
  
  /**
   * 文件大小格式化
   */
  fileSize: (bytes, decimals = 2) => {
    if (!is.number(bytes) || bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
  },
  
  /**
   * 货币格式化
   */
  currency: (amount, currency = 'CNY', locale = 'zh-CN') => {
    if (!is.number(amount)) return '¥0.00';
    
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currency
    }).format(amount);
  }
};

// ================================
// 加密工具
// ================================

const crypto_utils = {
  /**
   * MD5 哈希
   */
  md5: (text) => {
    if (!is.string(text)) return '';
    return crypto.createHash('md5').update(text).digest('hex');
  },
  
  /**
   * SHA256 哈希
   */
  sha256: (text) => {
    if (!is.string(text)) return '';
    return crypto.createHash('sha256').update(text).digest('hex');
  },
  
  /**
   * Base64 编码
   */
  base64Encode: (text) => {
    if (!is.string(text)) return '';
    return Buffer.from(text, 'utf8').toString('base64');
  },
  
  /**
   * Base64 解码
   */
  base64Decode: (encoded) => {
    if (!is.string(encoded)) return '';
    try {
      return Buffer.from(encoded, 'base64').toString('utf8');
    } catch {
      return '';
    }
  },
  
  /**
   * 生成UUID
   */
  uuid: () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  },
  
  /**
   * 生成随机盐
   */
  generateSalt: (length = 16) => {
    return crypto.randomBytes(length).toString('hex');
  },
  
  /**
   * 密码哈希（带盐）
   */
  hashPassword: (password, salt = null) => {
    if (!is.string(password)) return null;
    
    if (!salt) {
      salt = crypto_utils.generateSalt();
    }
    
    const hash = crypto.pbkdf2Sync(password, salt, 10000, 64, 'sha512').toString('hex');
    return { hash, salt };
  },
  
  /**
   * 验证密码
   */
  verifyPassword: (password, hash, salt) => {
    if (!is.string(password) || !is.string(hash) || !is.string(salt)) return false;
    
    const verifyHash = crypto.pbkdf2Sync(password, salt, 10000, 64, 'sha512').toString('hex');
    return hash === verifyHash;
  }
};

// ================================
// 文件工具
// ================================

const file = {
  /**
   * 确保目录存在
   */
  ensureDir: async (dirPath) => {
    try {
      await fs.promises.access(dirPath);
    } catch {
      await fs.promises.mkdir(dirPath, { recursive: true });
    }
  },
  
  /**
   * 读取JSON文件
   */
  readJson: async (filePath) => {
    try {
      const content = await fs.promises.readFile(filePath, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      throw new Error(`Failed to read JSON file: ${error.message}`);
    }
  },
  
  /**
   * 写入JSON文件
   */
  writeJson: async (filePath, data, options = {}) => {
    const { spaces = 2 } = options;
    
    try {
      await file.ensureDir(path.dirname(filePath));
      const content = JSON.stringify(data, null, spaces);
      await fs.promises.writeFile(filePath, content, 'utf8');
    } catch (error) {
      throw new Error(`Failed to write JSON file: ${error.message}`);
    }
  },
  
  /**
   * 获取文件扩展名
   */
  getExtension: (filePath) => {
    return path.extname(filePath).toLowerCase();
  },
  
  /**
   * 获取文件名（不含扩展名）
   */
  getBasename: (filePath) => {
    return path.basename(filePath, path.extname(filePath));
  },
  
  /**
   * 获取文件大小
   */
  getSize: async (filePath) => {
    try {
      const stats = await fs.promises.stat(filePath);
      return stats.size;
    } catch {
      return 0;
    }
  },
  
  /**
   * 检查文件是否存在
   */
  exists: async (filePath) => {
    try {
      await fs.promises.access(filePath);
      return true;
    } catch {
      return false;
    }
  },
  
  /**
   * 复制文件
   */
  copy: async (src, dest) => {
    try {
      await file.ensureDir(path.dirname(dest));
      await fs.promises.copyFile(src, dest);
    } catch (error) {
      throw new Error(`Failed to copy file: ${error.message}`);
    }
  },
  
  /**
   * 删除文件
   */
  remove: async (filePath) => {
    try {
      await fs.promises.unlink(filePath);
    } catch (error) {
      if (error.code !== 'ENOENT') {
        throw new Error(`Failed to remove file: ${error.message}`);
      }
    }
  }
};

// ================================
// 性能工具
// ================================

const performance = {
  /**
   * 防抖
   */
  debounce: (func, delay = 300) => {
    let timeoutId;
    return function(...args) {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
  },
  
  /**
   * 节流
   */
  throttle: (func, limit = 300) => {
    let inThrottle;
    return function(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },
  
  /**
   * 记忆化
   */
  memoize: (func, keyGenerator = (...args) => JSON.stringify(args)) => {
    const cache = new Map();
    
    return function(...args) {
      const key = keyGenerator(...args);
      
      if (cache.has(key)) {
        return cache.get(key);
      }
      
      const result = func.apply(this, args);
      cache.set(key, result);
      return result;
    };
  },
  
  /**
   * 延迟执行
   */
  delay: (ms) => new Promise(resolve => setTimeout(resolve, ms)),
  
  /**
   * 重试机制
   */
  retry: async (func, maxAttempts = 3, delay = 1000) => {
    let lastError;
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await func();
      } catch (error) {
        lastError = error;
        
        if (attempt < maxAttempts) {
          await performance.delay(delay * attempt);
        }
      }
    }
    
    throw lastError;
  },
  
  /**
   * 超时控制
   */
  timeout: (promise, ms) => {
    return Promise.race([
      promise,
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Operation timed out')), ms)
      )
    ]);
  }
};

// ================================
// 导出模块
// ================================
module.exports = {
  is,
  string,
  array,
  object,
  date,
  number,
  crypto: crypto_utils,
  file,
  performance
};

// ================================
// 使用说明
// ================================

/*
1. 数据类型检查：
   - 使用 is 对象进行类型检查
   - 支持基本类型和复合类型
   - 包含常用格式验证

2. 字符串处理：
   - 命名转换（驼峰、蛇形、短横线）
   - HTML 转义和反转义
   - 字符串截断和模板
   - 相似度计算

3. 数组操作：
   - 去重、分块、扁平化
   - 排序、分组、洗牌
   - 集合运算（交集、并集、差集）
   - 分页处理

4. 对象处理：
   - 深拷贝和深度合并
   - 嵌套属性操作
   - 键转换和过滤
   - 属性选择和排除

5. 日期处理：
   - 格式化和解析
   - 相对时间显示
   - 时间计算和范围

6. 数字格式化：
   - 千分位分隔符
   - 文件大小格式化
   - 货币格式化
   - 百分比计算

7. 加密工具：
   - 哈希算法（MD5、SHA256）
   - Base64 编解码
   - UUID 生成
   - 密码哈希和验证

8. 文件操作：
   - 目录创建和检查
   - JSON 文件读写
   - 文件信息获取
   - 文件复制和删除

9. 性能优化：
   - 防抖和节流
   - 记忆化缓存
   - 重试机制
   - 超时控制

10. 最佳实践：
    - 参数验证和错误处理
    - 类型安全检查
    - 性能优化考虑
    - 内存泄漏防护
*/