/**
 * Prettier 配置文件 - 代码格式化配置
 * 3AI工作室 - 统一代码风格配置
 */

/** @type {import('prettier').Config} */
const config = {
  // ================================
  // 基础格式化选项
  // ================================
  
  // 每行最大字符数
  printWidth: 100,
  
  // 缩进空格数
  tabWidth: 2,
  
  // 使用空格而不是制表符
  useTabs: false,
  
  // 语句末尾添加分号
  semi: true,
  
  // 使用单引号
  singleQuote: true,
  
  // 对象属性引号策略
  // 'as-needed' | 'consistent' | 'preserve'
  quoteProps: 'as-needed',
  
  // JSX 中使用单引号
  jsxSingleQuote: true,
  
  // 尾随逗号策略
  // 'none' | 'es5' | 'all'
  trailingComma: 'es5',
  
  // 对象字面量的大括号内是否加空格
  bracketSpacing: true,
  
  // JSX 标签的反尖括号是否另起一行
  bracketSameLine: false,
  
  // 箭头函数参数括号策略
  // 'always' | 'avoid'
  arrowParens: 'avoid',
  
  // 换行符策略
  // 'lf' | 'crlf' | 'cr' | 'auto'
  endOfLine: 'lf',
  
  // ================================
  // 嵌入式语言格式化
  // ================================
  
  // HTML 中的空白敏感性
  // 'css' | 'strict' | 'ignore'
  htmlWhitespaceSensitivity: 'css',
  
  // Vue 文件中 script 和 style 标签的缩进
  vueIndentScriptAndStyle: false,
  
  // 嵌入式代码格式化
  embeddedLanguageFormatting: 'auto',
  
  // ================================
  // 文件范围格式化
  // ================================
  
  // 格式化范围开始（用于部分格式化）
  rangeStart: 0,
  
  // 格式化范围结束（用于部分格式化）
  rangeEnd: Infinity,
  
  // 是否格式化文件开头的 pragma
  requirePragma: false,
  
  // 是否在文件开头插入 pragma
  insertPragma: false,
  
  // Markdown 文本换行策略
  // 'always' | 'never' | 'preserve'
  proseWrap: 'preserve',
  
  // ================================
  // 特定文件类型覆盖
  // ================================
  
  overrides: [
    // JSON 文件
    {
      files: ['*.json', '*.jsonc'],
      options: {
        printWidth: 120,
        tabWidth: 2,
        trailingComma: 'none',
      },
    },
    
    // YAML 文件
    {
      files: ['*.yml', '*.yaml'],
      options: {
        printWidth: 120,
        tabWidth: 2,
        singleQuote: false,
      },
    },
    
    // Markdown 文件
    {
      files: ['*.md', '*.mdx'],
      options: {
        printWidth: 80,
        proseWrap: 'always',
        tabWidth: 2,
        useTabs: false,
      },
    },
    
    // HTML 文件
    {
      files: ['*.html'],
      options: {
        printWidth: 120,
        tabWidth: 2,
        htmlWhitespaceSensitivity: 'ignore',
      },
    },
    
    // CSS/SCSS/Less 文件
    {
      files: ['*.css', '*.scss', '*.less'],
      options: {
        printWidth: 120,
        tabWidth: 2,
        singleQuote: false,
      },
    },
    
    // Vue 文件
    {
      files: ['*.vue'],
      options: {
        printWidth: 100,
        tabWidth: 2,
        singleQuote: true,
        vueIndentScriptAndStyle: true,
      },
    },
    
    // React/JSX 文件
    {
      files: ['*.jsx', '*.tsx'],
      options: {
        printWidth: 100,
        tabWidth: 2,
        jsxSingleQuote: true,
        bracketSameLine: false,
      },
    },
    
    // TypeScript 声明文件
    {
      files: ['*.d.ts'],
      options: {
        printWidth: 120,
        tabWidth: 2,
      },
    },
    
    // 配置文件
    {
      files: [
        '*.config.js',
        '*.config.ts',
        '*.config.mjs',
        '.eslintrc.js',
        '.eslintrc.cjs',
        'webpack.config.js',
        'rollup.config.js',
        'vite.config.js',
        'vite.config.ts',
      ],
      options: {
        printWidth: 120,
        tabWidth: 2,
        trailingComma: 'es5',
      },
    },
    
    // Package.json 文件
    {
      files: ['package.json'],
      options: {
        printWidth: 120,
        tabWidth: 2,
        trailingComma: 'none',
      },
    },
    
    // 测试文件
    {
      files: [
        '*.test.js',
        '*.test.ts',
        '*.test.jsx',
        '*.test.tsx',
        '*.spec.js',
        '*.spec.ts',
        '*.spec.jsx',
        '*.spec.tsx',
      ],
      options: {
        printWidth: 120,
        tabWidth: 2,
      },
    },
    
    // 文档文件
    {
      files: ['README.md', 'CHANGELOG.md', 'CONTRIBUTING.md'],
      options: {
        printWidth: 80,
        proseWrap: 'always',
        tabWidth: 2,
      },
    },
  ],
  
  // ================================
  // 插件配置
  // ================================
  
  plugins: [
    // 可选插件（需要安装对应的包）
    // '@prettier/plugin-xml',
    // 'prettier-plugin-organize-imports',
    // 'prettier-plugin-packagejson',
    // 'prettier-plugin-sh',
    // 'prettier-plugin-sql',
    // 'prettier-plugin-toml',
  ],
};

module.exports = config;