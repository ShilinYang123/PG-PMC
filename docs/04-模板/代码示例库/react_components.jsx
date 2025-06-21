// React组件代码示例 - 3AI工作室
// 提供常用的React组件模板，包括函数组件、类组件、Hooks使用等

import React, { useState, useEffect, useCallback, useMemo, useRef, useContext, createContext } from 'react';
import PropTypes from 'prop-types';

// ================================
// 基础函数组件
// ================================

/**
 * 基础按钮组件
 */
const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'medium', 
  disabled = false, 
  loading = false,
  onClick,
  className = '',
  ...props 
}) => {
  const baseClasses = 'btn';
  const variantClasses = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    danger: 'btn-danger',
    success: 'btn-success'
  };
  const sizeClasses = {
    small: 'btn-sm',
    medium: 'btn-md',
    large: 'btn-lg'
  };
  
  const classes = [
    baseClasses,
    variantClasses[variant],
    sizeClasses[size],
    disabled && 'btn-disabled',
    loading && 'btn-loading',
    className
  ].filter(Boolean).join(' ');
  
  const handleClick = useCallback((e) => {
    if (disabled || loading) return;
    onClick?.(e);
  }, [disabled, loading, onClick]);
  
  return (
    <button 
      className={classes}
      disabled={disabled || loading}
      onClick={handleClick}
      {...props}
    >
      {loading && <span className="spinner" />}
      {children}
    </button>
  );
};

Button.propTypes = {
  children: PropTypes.node.isRequired,
  variant: PropTypes.oneOf(['primary', 'secondary', 'danger', 'success']),
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  disabled: PropTypes.bool,
  loading: PropTypes.bool,
  onClick: PropTypes.func,
  className: PropTypes.string
};

// ================================
// 输入组件
// ================================

/**
 * 输入框组件
 */
const Input = React.forwardRef(({ 
  label,
  error,
  helperText,
  required = false,
  className = '',
  ...props 
}, ref) => {
  const [focused, setFocused] = useState(false);
  
  const inputClasses = [
    'input',
    error && 'input-error',
    focused && 'input-focused',
    className
  ].filter(Boolean).join(' ');
  
  return (
    <div className="input-group">
      {label && (
        <label className="input-label">
          {label}
          {required && <span className="required">*</span>}
        </label>
      )}
      <input
        ref={ref}
        className={inputClasses}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        {...props}
      />
      {error && <span className="input-error-text">{error}</span>}
      {helperText && !error && <span className="input-helper-text">{helperText}</span>}
    </div>
  );
});

Input.displayName = 'Input';

Input.propTypes = {
  label: PropTypes.string,
  error: PropTypes.string,
  helperText: PropTypes.string,
  required: PropTypes.bool,
  className: PropTypes.string
};

// ================================
// 模态框组件
// ================================

/**
 * 模态框组件
 */
const Modal = ({ 
  isOpen, 
  onClose, 
  title, 
  children, 
  size = 'medium',
  closeOnOverlay = true,
  closeOnEscape = true 
}) => {
  const modalRef = useRef(null);
  
  // 处理ESC键关闭
  useEffect(() => {
    if (!closeOnEscape) return;
    
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose, closeOnEscape]);
  
  // 处理点击遮罩关闭
  const handleOverlayClick = useCallback((e) => {
    if (closeOnOverlay && e.target === e.currentTarget) {
      onClose();
    }
  }, [onClose, closeOnOverlay]);
  
  // 防止滚动穿透
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);
  
  if (!isOpen) return null;
  
  const sizeClasses = {
    small: 'modal-sm',
    medium: 'modal-md',
    large: 'modal-lg',
    fullscreen: 'modal-fullscreen'
  };
  
  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div 
        ref={modalRef}
        className={`modal ${sizeClasses[size]}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'modal-title' : undefined}
      >
        <div className="modal-header">
          {title && <h2 id="modal-title" className="modal-title">{title}</h2>}
          <button 
            className="modal-close"
            onClick={onClose}
            aria-label="关闭模态框"
          >
            ×
          </button>
        </div>
        <div className="modal-body">
          {children}
        </div>
      </div>
    </div>
  );
};

Modal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  title: PropTypes.string,
  children: PropTypes.node,
  size: PropTypes.oneOf(['small', 'medium', 'large', 'fullscreen']),
  closeOnOverlay: PropTypes.bool,
  closeOnEscape: PropTypes.bool
};

// ================================
// 列表组件
// ================================

/**
 * 虚拟化列表组件
 */
const VirtualList = ({ 
  items, 
  itemHeight, 
  containerHeight, 
  renderItem,
  overscan = 5 
}) => {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef(null);
  
  const visibleRange = useMemo(() => {
    const start = Math.floor(scrollTop / itemHeight);
    const visibleCount = Math.ceil(containerHeight / itemHeight);
    const end = Math.min(start + visibleCount + overscan, items.length);
    
    return {
      start: Math.max(0, start - overscan),
      end
    };
  }, [scrollTop, itemHeight, containerHeight, items.length, overscan]);
  
  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.start, visibleRange.end).map((item, index) => ({
      ...item,
      index: visibleRange.start + index
    }));
  }, [items, visibleRange]);
  
  const handleScroll = useCallback((e) => {
    setScrollTop(e.target.scrollTop);
  }, []);
  
  const totalHeight = items.length * itemHeight;
  const offsetY = visibleRange.start * itemHeight;
  
  return (
    <div 
      ref={containerRef}
      className="virtual-list"
      style={{ height: containerHeight, overflow: 'auto' }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ transform: `translateY(${offsetY}px)` }}>
          {visibleItems.map((item) => (
            <div 
              key={item.index}
              style={{ height: itemHeight }}
            >
              {renderItem(item, item.index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

VirtualList.propTypes = {
  items: PropTypes.array.isRequired,
  itemHeight: PropTypes.number.isRequired,
  containerHeight: PropTypes.number.isRequired,
  renderItem: PropTypes.func.isRequired,
  overscan: PropTypes.number
};

// ================================
// 表格组件
// ================================

/**
 * 数据表格组件
 */
const DataTable = ({ 
  data, 
  columns, 
  loading = false,
  sortable = true,
  selectable = false,
  onSort,
  onSelect,
  className = '' 
}) => {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [selectedRows, setSelectedRows] = useState(new Set());
  
  const sortedData = useMemo(() => {
    if (!sortConfig.key) return data;
    
    return [...data].sort((a, b) => {
      const aValue = a[sortConfig.key];
      const bValue = b[sortConfig.key];
      
      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [data, sortConfig]);
  
  const handleSort = useCallback((key) => {
    if (!sortable) return;
    
    const direction = sortConfig.key === key && sortConfig.direction === 'asc' ? 'desc' : 'asc';
    setSortConfig({ key, direction });
    onSort?.({ key, direction });
  }, [sortConfig, sortable, onSort]);
  
  const handleSelectAll = useCallback((checked) => {
    if (checked) {
      setSelectedRows(new Set(data.map((_, index) => index)));
    } else {
      setSelectedRows(new Set());
    }
  }, [data]);
  
  const handleSelectRow = useCallback((index, checked) => {
    const newSelected = new Set(selectedRows);
    if (checked) {
      newSelected.add(index);
    } else {
      newSelected.delete(index);
    }
    setSelectedRows(newSelected);
    onSelect?.(Array.from(newSelected));
  }, [selectedRows, onSelect]);
  
  if (loading) {
    return (
      <div className="table-loading">
        <div className="spinner">加载中...</div>
      </div>
    );
  }
  
  return (
    <div className={`data-table ${className}`}>
      <table>
        <thead>
          <tr>
            {selectable && (
              <th>
                <input
                  type="checkbox"
                  checked={selectedRows.size === data.length && data.length > 0}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                />
              </th>
            )}
            {columns.map((column) => (
              <th 
                key={column.key}
                className={sortable ? 'sortable' : ''}
                onClick={() => handleSort(column.key)}
              >
                {column.title}
                {sortable && sortConfig.key === column.key && (
                  <span className={`sort-icon ${sortConfig.direction}`}>
                    {sortConfig.direction === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedData.map((row, index) => (
            <tr key={index} className={selectedRows.has(index) ? 'selected' : ''}>
              {selectable && (
                <td>
                  <input
                    type="checkbox"
                    checked={selectedRows.has(index)}
                    onChange={(e) => handleSelectRow(index, e.target.checked)}
                  />
                </td>
              )}
              {columns.map((column) => (
                <td key={column.key}>
                  {column.render ? column.render(row[column.key], row, index) : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

DataTable.propTypes = {
  data: PropTypes.array.isRequired,
  columns: PropTypes.arrayOf(PropTypes.shape({
    key: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    render: PropTypes.func
  })).isRequired,
  loading: PropTypes.bool,
  sortable: PropTypes.bool,
  selectable: PropTypes.bool,
  onSort: PropTypes.func,
  onSelect: PropTypes.func,
  className: PropTypes.string
};

// ================================
// 自定义Hooks
// ================================

/**
 * 本地存储Hook
 */
const useLocalStorage = (key, initialValue) => {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error('Error reading localStorage:', error);
      return initialValue;
    }
  });
  
  const setValue = useCallback((value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error('Error setting localStorage:', error);
    }
  }, [key, storedValue]);
  
  return [storedValue, setValue];
};

/**
 * 防抖Hook
 */
const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);
  
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);
  
  return debouncedValue;
};

/**
 * 网络请求Hook
 */
const useFetch = (url, options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(url, options);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [url, options]);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  return { data, loading, error, refetch: fetchData };
};

/**
 * 窗口大小Hook
 */
const useWindowSize = () => {
  const [windowSize, setWindowSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight
  });
  
  useEffect(() => {
    const handleResize = () => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  return windowSize;
};

/**
 * 点击外部Hook
 */
const useClickOutside = (ref, handler) => {
  useEffect(() => {
    const listener = (event) => {
      if (!ref.current || ref.current.contains(event.target)) {
        return;
      }
      handler(event);
    };
    
    document.addEventListener('mousedown', listener);
    document.addEventListener('touchstart', listener);
    
    return () => {
      document.removeEventListener('mousedown', listener);
      document.removeEventListener('touchstart', listener);
    };
  }, [ref, handler]);
};

/**
 * 表单Hook
 */
const useForm = (initialValues = {}, validationRules = {}) => {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  
  const setValue = useCallback((name, value) => {
    setValues(prev => ({ ...prev, [name]: value }));
  }, []);
  
  const setError = useCallback((name, error) => {
    setErrors(prev => ({ ...prev, [name]: error }));
  }, []);
  
  const setFieldTouched = useCallback((name, isTouched = true) => {
    setTouched(prev => ({ ...prev, [name]: isTouched }));
  }, []);
  
  const validate = useCallback((fieldName = null) => {
    const fieldsToValidate = fieldName ? [fieldName] : Object.keys(validationRules);
    const newErrors = { ...errors };
    
    fieldsToValidate.forEach(field => {
      const rules = validationRules[field];
      const value = values[field];
      
      if (rules) {
        if (rules.required && (!value || value.toString().trim() === '')) {
          newErrors[field] = rules.required;
        } else if (rules.pattern && value && !rules.pattern.test(value)) {
          newErrors[field] = rules.patternMessage || '格式不正确';
        } else if (rules.minLength && value && value.length < rules.minLength) {
          newErrors[field] = `最少需要${rules.minLength}个字符`;
        } else if (rules.maxLength && value && value.length > rules.maxLength) {
          newErrors[field] = `最多允许${rules.maxLength}个字符`;
        } else if (rules.custom && !rules.custom(value, values)) {
          newErrors[field] = rules.customMessage || '验证失败';
        } else {
          delete newErrors[field];
        }
      }
    });
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [values, errors, validationRules]);
  
  const handleChange = useCallback((e) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === 'checkbox' ? checked : value;
    setValue(name, newValue);
  }, [setValue]);
  
  const handleBlur = useCallback((e) => {
    const { name } = e.target;
    setFieldTouched(name, true);
    validate(name);
  }, [setFieldTouched, validate]);
  
  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
  }, [initialValues]);
  
  return {
    values,
    errors,
    touched,
    setValue,
    setError,
    setFieldTouched,
    validate,
    handleChange,
    handleBlur,
    reset,
    isValid: Object.keys(errors).length === 0
  };
};

// ================================
// Context示例
// ================================

/**
 * 主题Context
 */
const ThemeContext = createContext({
  theme: 'light',
  toggleTheme: () => {}
});

const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useLocalStorage('theme', 'light');
  
  const toggleTheme = useCallback(() => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  }, [setTheme]);
  
  const value = useMemo(() => ({
    theme,
    toggleTheme
  }), [theme, toggleTheme]);
  
  return (
    <ThemeContext.Provider value={value}>
      <div className={`app theme-${theme}`}>
        {children}
      </div>
    </ThemeContext.Provider>
  );
};

const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// ================================
// 高阶组件
// ================================

/**
 * 错误边界HOC
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }
  
  static getDerivedStateFromError(error) {
    return { hasError: true };
  }
  
  componentDidCatch(error, errorInfo) {
    this.setState({
      error,
      errorInfo
    });
    
    // 这里可以记录错误到日志服务
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }
  
  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="error-boundary">
          <h2>出现了错误</h2>
          <details style={{ whiteSpace: 'pre-wrap' }}>
            {this.state.error && this.state.error.toString()}
            <br />
            {this.state.errorInfo.componentStack}
          </details>
        </div>
      );
    }
    
    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
  fallback: PropTypes.node
};

/**
 * 权限控制HOC
 */
const withAuth = (WrappedComponent, requiredPermissions = []) => {
  const AuthComponent = (props) => {
    const [hasPermission, setHasPermission] = useState(false);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
      // 模拟权限检查
      const checkPermissions = async () => {
        try {
          // 这里应该调用实际的权限检查API
          const userPermissions = await getUserPermissions();
          const hasAllPermissions = requiredPermissions.every(permission => 
            userPermissions.includes(permission)
          );
          setHasPermission(hasAllPermissions);
        } catch (error) {
          console.error('Permission check failed:', error);
          setHasPermission(false);
        } finally {
          setLoading(false);
        }
      };
      
      checkPermissions();
    }, []);
    
    if (loading) {
      return <div className="loading">检查权限中...</div>;
    }
    
    if (!hasPermission) {
      return <div className="no-permission">您没有访问权限</div>;
    }
    
    return <WrappedComponent {...props} />;
  };
  
  AuthComponent.displayName = `withAuth(${WrappedComponent.displayName || WrappedComponent.name})`;
  
  return AuthComponent;
};

// 模拟获取用户权限的函数
const getUserPermissions = async () => {
  // 模拟API调用
  return new Promise(resolve => {
    setTimeout(() => {
      resolve(['read', 'write', 'admin']);
    }, 1000);
  });
};

// ================================
// 导出组件
// ================================
export {
  Button,
  Input,
  Modal,
  VirtualList,
  DataTable,
  ErrorBoundary,
  ThemeProvider,
  useLocalStorage,
  useDebounce,
  useFetch,
  useWindowSize,
  useClickOutside,
  useForm,
  useTheme,
  withAuth
};

// ================================
// 使用示例
// ================================

/*
// 基础组件使用
const App = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({ name: '', email: '' });
  const { theme, toggleTheme } = useTheme();
  
  const { values, errors, handleChange, handleBlur, validate } = useForm(
    { username: '', password: '' },
    {
      username: {
        required: '用户名不能为空',
        minLength: 3
      },
      password: {
        required: '密码不能为空',
        minLength: 6,
        pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
        patternMessage: '密码必须包含大小写字母和数字'
      }
    }
  );
  
  const tableColumns = [
    { key: 'name', title: '姓名' },
    { key: 'email', title: '邮箱' },
    { 
      key: 'actions', 
      title: '操作',
      render: (value, row) => (
        <Button size="small" onClick={() => handleEdit(row)}>编辑</Button>
      )
    }
  ];
  
  const tableData = [
    { name: '张三', email: 'zhangsan@example.com' },
    { name: '李四', email: 'lisi@example.com' }
  ];
  
  return (
    <ErrorBoundary>
      <div className="app">
        <Button onClick={toggleTheme}>
          切换到{theme === 'light' ? '暗色' : '亮色'}主题
        </Button>
        
        <Button onClick={() => setIsModalOpen(true)}>
          打开模态框
        </Button>
        
        <form>
          <Input
            name="username"
            label="用户名"
            value={values.username}
            error={errors.username}
            onChange={handleChange}
            onBlur={handleBlur}
            required
          />
          
          <Input
            name="password"
            type="password"
            label="密码"
            value={values.password}
            error={errors.password}
            onChange={handleChange}
            onBlur={handleBlur}
            required
          />
          
          <Button 
            type="submit" 
            disabled={!validate()}
            onClick={(e) => {
              e.preventDefault();
              if (validate()) {
                console.log('表单提交:', values);
              }
            }}
          >
            提交
          </Button>
        </form>
        
        <DataTable
          data={tableData}
          columns={tableColumns}
          sortable
          selectable
          onSelect={(selectedIndexes) => {
            console.log('选中的行:', selectedIndexes);
          }}
        />
        
        <Modal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          title="示例模态框"
        >
          <p>这是模态框的内容</p>
        </Modal>
      </div>
    </ErrorBoundary>
  );
};

// 应用根组件
const Root = () => (
  <ThemeProvider>
    <App />
  </ThemeProvider>
);

export default Root;
*/

// ================================
// 最佳实践说明
// ================================

/*
1. 组件设计原则：
   - 单一职责：每个组件只负责一个功能
   - 可复用性：通过props配置不同的行为
   - 可访问性：支持键盘导航和屏幕阅读器
   - 性能优化：使用React.memo、useCallback、useMemo

2. Props验证：
   - 使用PropTypes进行类型检查
   - 提供默认值和必需属性标记
   - 文档化组件的API

3. 状态管理：
   - 本地状态使用useState
   - 复杂状态使用useReducer
   - 全局状态使用Context或状态管理库

4. 副作用处理：
   - 使用useEffect处理副作用
   - 正确清理事件监听器和定时器
   - 避免内存泄漏

5. 自定义Hooks：
   - 提取可复用的逻辑
   - 遵循Hooks规则
   - 提供清晰的API

6. 错误处理：
   - 使用ErrorBoundary捕获组件错误
   - 提供友好的错误提示
   - 记录错误信息用于调试

7. 性能优化：
   - 避免不必要的重新渲染
   - 使用虚拟化处理大量数据
   - 懒加载和代码分割

8. 测试友好：
   - 使用data-testid属性
   - 避免依赖实现细节
   - 提供清晰的组件接口
*/