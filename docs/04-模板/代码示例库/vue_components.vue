<!-- Vue组件代码示例 - 3AI工作室 -->
<!-- 提供常用的Vue组件模板，包括组合式API、选项式API、自定义指令等 -->

<template>
  <!-- 基础按钮组件 -->
  <div class="vue-components-demo">
    <!-- 按钮组件示例 -->
    <BaseButton
      :variant="buttonVariant"
      :size="buttonSize"
      :loading="buttonLoading"
      @click="handleButtonClick"
    >
      点击我
    </BaseButton>

    <!-- 输入框组件示例 -->
    <BaseInput
      v-model="inputValue"
      label="用户名"
      placeholder="请输入用户名"
      :error="inputError"
      required
    />

    <!-- 模态框组件示例 -->
    <BaseModal
      v-model:visible="modalVisible"
      title="示例模态框"
      @confirm="handleModalConfirm"
    >
      <p>这是模态框的内容</p>
    </BaseModal>

    <!-- 数据表格组件示例 -->
    <DataTable
      :data="tableData"
      :columns="tableColumns"
      :loading="tableLoading"
      sortable
      selectable
      @sort="handleTableSort"
      @select="handleTableSelect"
    />
  </div>
</template>

<script>
// ================================
// 基础按钮组件
// ================================
const BaseButton = {
  name: 'BaseButton',
  props: {
    variant: {
      type: String,
      default: 'primary',
      validator: (value) => ['primary', 'secondary', 'danger', 'success'].includes(value)
    },
    size: {
      type: String,
      default: 'medium',
      validator: (value) => ['small', 'medium', 'large'].includes(value)
    },
    disabled: {
      type: Boolean,
      default: false
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['click'],
  computed: {
    classes() {
      return [
        'btn',
        `btn-${this.variant}`,
        `btn-${this.size}`,
        {
          'btn-disabled': this.disabled,
          'btn-loading': this.loading
        }
      ];
    }
  },
  methods: {
    handleClick(event) {
      if (this.disabled || this.loading) return;
      this.$emit('click', event);
    }
  },
  template: `
    <button 
      :class="classes"
      :disabled="disabled || loading"
      @click="handleClick"
    >
      <span v-if="loading" class="spinner"></span>
      <slot></slot>
    </button>
  `
};

// ================================
// 输入框组件
// ================================
const BaseInput = {
  name: 'BaseInput',
  props: {
    modelValue: {
      type: [String, Number],
      default: ''
    },
    label: {
      type: String,
      default: ''
    },
    placeholder: {
      type: String,
      default: ''
    },
    type: {
      type: String,
      default: 'text'
    },
    error: {
      type: String,
      default: ''
    },
    helperText: {
      type: String,
      default: ''
    },
    required: {
      type: Boolean,
      default: false
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue', 'focus', 'blur', 'change'],
  data() {
    return {
      focused: false
    };
  },
  computed: {
    inputClasses() {
      return [
        'input',
        {
          'input-error': this.error,
          'input-focused': this.focused,
          'input-disabled': this.disabled
        }
      ];
    }
  },
  methods: {
    handleInput(event) {
      this.$emit('update:modelValue', event.target.value);
    },
    handleFocus(event) {
      this.focused = true;
      this.$emit('focus', event);
    },
    handleBlur(event) {
      this.focused = false;
      this.$emit('blur', event);
    },
    handleChange(event) {
      this.$emit('change', event);
    }
  },
  template: `
    <div class="input-group">
      <label v-if="label" class="input-label">
        {{ label }}
        <span v-if="required" class="required">*</span>
      </label>
      <input
        :class="inputClasses"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        @input="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
        @change="handleChange"
      />
      <span v-if="error" class="input-error-text">{{ error }}</span>
      <span v-else-if="helperText" class="input-helper-text">{{ helperText }}</span>
    </div>
  `
};

// ================================
// 模态框组件
// ================================
const BaseModal = {
  name: 'BaseModal',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      default: ''
    },
    size: {
      type: String,
      default: 'medium',
      validator: (value) => ['small', 'medium', 'large', 'fullscreen'].includes(value)
    },
    closeOnOverlay: {
      type: Boolean,
      default: true
    },
    closeOnEscape: {
      type: Boolean,
      default: true
    },
    showFooter: {
      type: Boolean,
      default: true
    }
  },
  emits: ['update:visible', 'confirm', 'cancel'],
  computed: {
    modalClasses() {
      return [
        'modal',
        `modal-${this.size}`
      ];
    }
  },
  watch: {
    visible: {
      handler(newVal) {
        if (newVal) {
          document.body.style.overflow = 'hidden';
          if (this.closeOnEscape) {
            document.addEventListener('keydown', this.handleEscape);
          }
        } else {
          document.body.style.overflow = 'unset';
          document.removeEventListener('keydown', this.handleEscape);
        }
      },
      immediate: true
    }
  },
  beforeUnmount() {
    document.body.style.overflow = 'unset';
    document.removeEventListener('keydown', this.handleEscape);
  },
  methods: {
    close() {
      this.$emit('update:visible', false);
    },
    handleOverlayClick(event) {
      if (this.closeOnOverlay && event.target === event.currentTarget) {
        this.close();
      }
    },
    handleEscape(event) {
      if (event.key === 'Escape') {
        this.close();
      }
    },
    handleConfirm() {
      this.$emit('confirm');
    },
    handleCancel() {
      this.$emit('cancel');
      this.close();
    }
  },
  template: `
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="visible" class="modal-overlay" @click="handleOverlayClick">
          <div :class="modalClasses" role="dialog" aria-modal="true">
            <div class="modal-header">
              <h2 v-if="title" class="modal-title">{{ title }}</h2>
              <button class="modal-close" @click="close" aria-label="关闭模态框">
                ×
              </button>
            </div>
            <div class="modal-body">
              <slot></slot>
            </div>
            <div v-if="showFooter" class="modal-footer">
              <slot name="footer">
                <BaseButton variant="secondary" @click="handleCancel">取消</BaseButton>
                <BaseButton @click="handleConfirm">确认</BaseButton>
              </slot>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  `
};

// ================================
// 数据表格组件
// ================================
const DataTable = {
  name: 'DataTable',
  props: {
    data: {
      type: Array,
      default: () => []
    },
    columns: {
      type: Array,
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    },
    sortable: {
      type: Boolean,
      default: false
    },
    selectable: {
      type: Boolean,
      default: false
    }
  },
  emits: ['sort', 'select'],
  data() {
    return {
      sortConfig: {
        key: null,
        direction: 'asc'
      },
      selectedRows: new Set()
    };
  },
  computed: {
    sortedData() {
      if (!this.sortConfig.key) return this.data;
      
      return [...this.data].sort((a, b) => {
        const aValue = a[this.sortConfig.key];
        const bValue = b[this.sortConfig.key];
        
        if (aValue < bValue) return this.sortConfig.direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return this.sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    },
    allSelected() {
      return this.selectedRows.size === this.data.length && this.data.length > 0;
    }
  },
  methods: {
    handleSort(key) {
      if (!this.sortable) return;
      
      const direction = this.sortConfig.key === key && this.sortConfig.direction === 'asc' ? 'desc' : 'asc';
      this.sortConfig = { key, direction };
      this.$emit('sort', { key, direction });
    },
    handleSelectAll(checked) {
      if (checked) {
        this.selectedRows = new Set(this.data.map((_, index) => index));
      } else {
        this.selectedRows = new Set();
      }
      this.$emit('select', Array.from(this.selectedRows));
    },
    handleSelectRow(index, checked) {
      if (checked) {
        this.selectedRows.add(index);
      } else {
        this.selectedRows.delete(index);
      }
      this.$emit('select', Array.from(this.selectedRows));
    },
    isRowSelected(index) {
      return this.selectedRows.has(index);
    }
  },
  template: `
    <div class="data-table">
      <div v-if="loading" class="table-loading">
        <div class="spinner">加载中...</div>
      </div>
      <table v-else>
        <thead>
          <tr>
            <th v-if="selectable">
              <input
                type="checkbox"
                :checked="allSelected"
                @change="handleSelectAll($event.target.checked)"
              />
            </th>
            <th 
              v-for="column in columns"
              :key="column.key"
              :class="{ sortable: sortable }"
              @click="handleSort(column.key)"
            >
              {{ column.title }}
              <span 
                v-if="sortable && sortConfig.key === column.key"
                :class="['sort-icon', sortConfig.direction]"
              >
                {{ sortConfig.direction === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="(row, index) in sortedData"
            :key="index"
            :class="{ selected: isRowSelected(index) }"
          >
            <td v-if="selectable">
              <input
                type="checkbox"
                :checked="isRowSelected(index)"
                @change="handleSelectRow(index, $event.target.checked)"
              />
            </td>
            <td v-for="column in columns" :key="column.key">
              <slot 
                v-if="column.slot" 
                :name="column.slot" 
                :row="row" 
                :value="row[column.key]" 
                :index="index"
              >
                {{ row[column.key] }}
              </slot>
              <span v-else>{{ row[column.key] }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  `
};

export default {
  name: 'VueComponentsDemo',
  components: {
    BaseButton,
    BaseInput,
    BaseModal,
    DataTable
  },
  data() {
    return {
      buttonVariant: 'primary',
      buttonSize: 'medium',
      buttonLoading: false,
      inputValue: '',
      inputError: '',
      modalVisible: false,
      tableLoading: false,
      tableData: [
        { id: 1, name: '张三', email: 'zhangsan@example.com', age: 25 },
        { id: 2, name: '李四', email: 'lisi@example.com', age: 30 },
        { id: 3, name: '王五', email: 'wangwu@example.com', age: 28 }
      ],
      tableColumns: [
        { key: 'name', title: '姓名' },
        { key: 'email', title: '邮箱' },
        { key: 'age', title: '年龄' },
        { key: 'actions', title: '操作', slot: 'actions' }
      ]
    };
  },
  methods: {
    handleButtonClick() {
      console.log('按钮被点击');
      this.buttonLoading = true;
      setTimeout(() => {
        this.buttonLoading = false;
      }, 2000);
    },
    handleModalConfirm() {
      console.log('模态框确认');
      this.modalVisible = false;
    },
    handleTableSort(sortConfig) {
      console.log('表格排序:', sortConfig);
    },
    handleTableSelect(selectedIndexes) {
      console.log('表格选择:', selectedIndexes);
    }
  }
};
</script>

<script setup>
// ================================
// 组合式API示例
// ================================

// 导入Vue 3组合式API
import { ref, reactive, computed, watch, onMounted, onUnmounted, provide, inject } from 'vue';

// ================================
// 响应式数据
// ================================
const count = ref(0);
const user = reactive({
  name: '',
  email: '',
  age: 0
});

// ================================
// 计算属性
// ================================
const doubleCount = computed(() => count.value * 2);
const userInfo = computed(() => {
  return `${user.name} (${user.email})`;
});

// ================================
// 监听器
// ================================
watch(count, (newValue, oldValue) => {
  console.log(`count changed from ${oldValue} to ${newValue}`);
});

watch(
  () => user.name,
  (newName) => {
    console.log(`用户名改变为: ${newName}`);
  }
);

// ================================
// 生命周期钩子
// ================================
onMounted(() => {
  console.log('组件已挂载');
});

onUnmounted(() => {
  console.log('组件已卸载');
});

// ================================
// 自定义组合函数
// ================================

// 计数器组合函数
function useCounter(initialValue = 0) {
  const count = ref(initialValue);
  
  const increment = () => count.value++;
  const decrement = () => count.value--;
  const reset = () => count.value = initialValue;
  
  return {
    count,
    increment,
    decrement,
    reset
  };
}

// 本地存储组合函数
function useLocalStorage(key, defaultValue) {
  const storedValue = localStorage.getItem(key);
  const value = ref(storedValue ? JSON.parse(storedValue) : defaultValue);
  
  watch(
    value,
    (newValue) => {
      localStorage.setItem(key, JSON.stringify(newValue));
    },
    { deep: true }
  );
  
  return value;
}

// 网络请求组合函数
function useFetch(url) {
  const data = ref(null);
  const error = ref(null);
  const loading = ref(false);
  
  const fetchData = async () => {
    try {
      loading.value = true;
      error.value = null;
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      data.value = await response.json();
    } catch (err) {
      error.value = err.message;
    } finally {
      loading.value = false;
    }
  };
  
  onMounted(fetchData);
  
  return {
    data,
    error,
    loading,
    refetch: fetchData
  };
}

// 表单验证组合函数
function useForm(initialValues, validationRules) {
  const values = reactive({ ...initialValues });
  const errors = reactive({});
  const touched = reactive({});
  
  const validate = (field = null) => {
    const fieldsToValidate = field ? [field] : Object.keys(validationRules);
    
    fieldsToValidate.forEach(fieldName => {
      const rules = validationRules[fieldName];
      const value = values[fieldName];
      
      if (rules) {
        if (rules.required && (!value || value.toString().trim() === '')) {
          errors[fieldName] = rules.required;
        } else if (rules.pattern && value && !rules.pattern.test(value)) {
          errors[fieldName] = rules.patternMessage || '格式不正确';
        } else if (rules.minLength && value && value.length < rules.minLength) {
          errors[fieldName] = `最少需要${rules.minLength}个字符`;
        } else {
          delete errors[fieldName];
        }
      }
    });
    
    return Object.keys(errors).length === 0;
  };
  
  const setFieldValue = (field, value) => {
    values[field] = value;
  };
  
  const setFieldTouched = (field, isTouched = true) => {
    touched[field] = isTouched;
  };
  
  const reset = () => {
    Object.assign(values, initialValues);
    Object.keys(errors).forEach(key => delete errors[key]);
    Object.keys(touched).forEach(key => delete touched[key]);
  };
  
  return {
    values,
    errors,
    touched,
    validate,
    setFieldValue,
    setFieldTouched,
    reset,
    isValid: computed(() => Object.keys(errors).length === 0)
  };
}

// ================================
// 依赖注入
// ================================

// 主题提供者
const themeKey = Symbol('theme');

function useThemeProvider() {
  const theme = useLocalStorage('theme', 'light');
  
  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light';
  };
  
  provide(themeKey, {
    theme,
    toggleTheme
  });
  
  return {
    theme,
    toggleTheme
  };
}

function useTheme() {
  const themeContext = inject(themeKey);
  if (!themeContext) {
    throw new Error('useTheme must be used within a theme provider');
  }
  return themeContext;
}

// ================================
// 使用组合函数
// ================================
const { count: counterValue, increment, decrement, reset } = useCounter(0);
const settings = useLocalStorage('userSettings', { language: 'zh-CN' });
const { data: apiData, loading: apiLoading, error: apiError } = useFetch('/api/users');

const { values: formValues, errors: formErrors, validate: validateForm } = useForm(
  { username: '', password: '' },
  {
    username: {
      required: '用户名不能为空',
      minLength: 3
    },
    password: {
      required: '密码不能为空',
      minLength: 6
    }
  }
);

// ================================
// 方法
// ================================
const handleSubmit = () => {
  if (validateForm()) {
    console.log('表单提交:', formValues);
  }
};
</script>

<style scoped>
/* ================================ */
/* 组件样式 */
/* ================================ */

.vue-components-demo {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  outline: none;
}

.btn:focus {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5);
}

.btn-primary {
  background-color: #3b82f6;
  color: white;
}

.btn-primary:hover:not(.btn-disabled) {
  background-color: #2563eb;
}

.btn-secondary {
  background-color: #6b7280;
  color: white;
}

.btn-secondary:hover:not(.btn-disabled) {
  background-color: #4b5563;
}

.btn-danger {
  background-color: #ef4444;
  color: white;
}

.btn-danger:hover:not(.btn-disabled) {
  background-color: #dc2626;
}

.btn-success {
  background-color: #10b981;
  color: white;
}

.btn-success:hover:not(.btn-disabled) {
  background-color: #059669;
}

.btn-small {
  padding: 4px 8px;
  font-size: 12px;
}

.btn-medium {
  padding: 8px 16px;
  font-size: 14px;
}

.btn-large {
  padding: 12px 24px;
  font-size: 16px;
}

.btn-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-loading {
  opacity: 0.7;
  cursor: wait;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 输入框样式 */
.input-group {
  margin-bottom: 16px;
}

.input-label {
  display: block;
  margin-bottom: 4px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.required {
  color: #ef4444;
  margin-left: 2px;
}

.input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.input-error {
  border-color: #ef4444;
}

.input-error:focus {
  border-color: #ef4444;
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.1);
}

.input-disabled {
  background-color: #f9fafb;
  cursor: not-allowed;
}

.input-error-text {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #ef4444;
}

.input-helper-text {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #6b7280;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 8px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-small {
  width: 400px;
}

.modal-medium {
  width: 600px;
}

.modal-large {
  width: 800px;
}

.modal-fullscreen {
  width: 95vw;
  height: 95vh;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6b7280;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.modal-close:hover {
  background-color: #f3f4f6;
  color: #374151;
}

.modal-body {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
}

/* 模态框动画 */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal,
.modal-leave-active .modal {
  transition: transform 0.3s ease;
}

.modal-enter-from .modal,
.modal-leave-to .modal {
  transform: scale(0.9);
}

/* 表格样式 */
.data-table {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.table-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #6b7280;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

th {
  background-color: #f9fafb;
  font-weight: 600;
  color: #374151;
}

th.sortable {
  cursor: pointer;
  user-select: none;
}

th.sortable:hover {
  background-color: #f3f4f6;
}

.sort-icon {
  margin-left: 4px;
  font-size: 12px;
}

tr:hover {
  background-color: #f9fafb;
}

tr.selected {
  background-color: #eff6ff;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .vue-components-demo {
    padding: 10px;
  }
  
  .modal-medium,
  .modal-large {
    width: 95vw;
  }
  
  .data-table {
    overflow-x: auto;
  }
}
</style>

<!-- ================================ -->
<!-- 自定义指令示例 -->
<!-- ================================ -->

<script>
// 点击外部指令
const clickOutside = {
  beforeMount(el, binding) {
    el.clickOutsideEvent = function(event) {
      if (!(el === event.target || el.contains(event.target))) {
        binding.value(event);
      }
    };
    document.addEventListener('click', el.clickOutsideEvent);
  },
  unmounted(el) {
    document.removeEventListener('click', el.clickOutsideEvent);
  }
};

// 懒加载指令
const lazyLoad = {
  beforeMount(el, binding) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          el.src = binding.value;
          observer.unobserve(el);
        }
      });
    });
    observer.observe(el);
  }
};

// 防抖指令
const debounce = {
  beforeMount(el, binding) {
    let timer;
    el.addEventListener('input', () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        binding.value();
      }, binding.arg || 300);
    });
  }
};

// 权限指令
const permission = {
  beforeMount(el, binding) {
    const permissions = binding.value;
    const userPermissions = getUserPermissions(); // 获取用户权限
    
    const hasPermission = permissions.some(permission => 
      userPermissions.includes(permission)
    );
    
    if (!hasPermission) {
      el.style.display = 'none';
    }
  }
};

// 导出指令
export const directives = {
  clickOutside,
  lazyLoad,
  debounce,
  permission
};

// 模拟获取用户权限
function getUserPermissions() {
  return ['read', 'write']; // 模拟权限数据
}
</script>

<!-- ================================ -->
<!-- 使用说明 -->
<!-- ================================ -->

<!--
1. 组件设计原则：
   - 单一职责：每个组件只负责一个功能
   - 可复用性：通过props配置不同的行为
   - 可维护性：清晰的代码结构和注释
   - 性能优化：合理使用计算属性和监听器

2. 组合式API优势：
   - 更好的逻辑复用
   - 更好的TypeScript支持
   - 更灵活的代码组织
   - 更小的打包体积

3. 自定义组合函数：
   - 提取可复用的逻辑
   - 保持组件的简洁
   - 便于测试和维护

4. 响应式系统：
   - ref：基本类型的响应式
   - reactive：对象类型的响应式
   - computed：计算属性
   - watch：监听器

5. 生命周期：
   - onMounted：组件挂载后
   - onUpdated：组件更新后
   - onUnmounted：组件卸载前
   - onBeforeMount：组件挂载前

6. 依赖注入：
   - provide：提供数据
   - inject：注入数据
   - 避免prop drilling

7. 自定义指令：
   - 封装DOM操作
   - 提供可复用的功能
   - 增强模板能力

8. 最佳实践：
   - 使用TypeScript提高代码质量
   - 合理拆分组件
   - 避免过度优化
   - 保持代码简洁
   - 编写单元测试
-->