/**
 * Babel 配置模板 - 3AI工作室
 * 支持现代 JavaScript/TypeScript 转译
 * 适用于 React/Vue/Node.js 等项目
 */

module.exports = function (api) {
  // 缓存配置
  api.cache(true);

  // 环境检测
  const isDevelopment = api.env('development');
  const isProduction = api.env('production');
  const isTest = api.env('test');

  // 基础预设
  const presets = [
    // ES6+ 转译
    [
      '@babel/preset-env',
      {
        // 目标环境
        targets: {
          // 浏览器兼容性
          browsers: [
            '> 1%',
            'last 2 versions',
            'not dead',
            'not ie <= 11',
          ],
          // Node.js 版本
          node: '14',
        },
        // 按需引入 polyfill
        useBuiltIns: 'usage',
        corejs: {
          version: 3,
          proposals: true,
        },
        // 模块转换
        modules: isTest ? 'commonjs' : false,
        // 调试信息
        debug: isDevelopment,
        // 包含转换的特性
        include: [
          '@babel/plugin-proposal-optional-chaining',
          '@babel/plugin-proposal-nullish-coalescing-operator',
        ],
        // 排除不需要的转换
        exclude: [
          'transform-typeof-symbol',
        ],
      },
    ],

    // React 支持
    [
      '@babel/preset-react',
      {
        // 运行时模式
        runtime: 'automatic', // React 17+ 新 JSX 转换
        // 开发模式
        development: isDevelopment,
        // 导入源
        importSource: '@emotion/react', // 如果使用 Emotion
      },
    ],

    // TypeScript 支持
    [
      '@babel/preset-typescript',
      {
        // 允许命名空间
        allowNamespaces: true,
        // 允许声明合并
        allowDeclareFields: true,
        // 仅移除类型导入
        onlyRemoveTypeImports: true,
        // 优化枚举
        optimizeConstEnums: true,
      },
    ],
  ];

  // 插件配置
  const plugins = [
    // 类属性支持
    '@babel/plugin-proposal-class-properties',
    
    // 对象展开支持
    '@babel/plugin-proposal-object-rest-spread',
    
    // 动态导入
    '@babel/plugin-syntax-dynamic-import',
    
    // 可选链操作符
    '@babel/plugin-proposal-optional-chaining',
    
    // 空值合并操作符
    '@babel/plugin-proposal-nullish-coalescing-operator',
    
    // 私有方法
    '@babel/plugin-proposal-private-methods',
    
    // 装饰器支持
    [
      '@babel/plugin-proposal-decorators',
      {
        legacy: true,
      },
    ],
    
    // 运行时助手
    [
      '@babel/plugin-transform-runtime',
      {
        corejs: false,
        helpers: true,
        regenerator: true,
        useESModules: !isTest,
        absoluteRuntime: false,
        version: '^7.12.0',
      },
    ],

    // 开发环境插件
    ...(isDevelopment ? [
      // React 热更新
      'react-refresh/babel',
    ] : []),

    // 生产环境插件
    ...(isProduction ? [
      // 移除 console
      [
        'babel-plugin-transform-remove-console',
        {
          exclude: ['error', 'warn'],
        },
      ],
      // 移除 debugger
      'babel-plugin-transform-remove-debugger',
    ] : []),

    // 测试环境插件
    ...(isTest ? [
      // 动态导入转换
      'babel-plugin-dynamic-import-node',
    ] : []),

    // 样式相关插件
    [
      'babel-plugin-styled-components',
      {
        displayName: isDevelopment,
        fileName: isDevelopment,
        minify: isProduction,
        pure: isProduction,
      },
    ],

    // 导入优化
    [
      'babel-plugin-import',
      {
        libraryName: 'antd',
        libraryDirectory: 'es',
        style: true,
      },
      'antd',
    ],
    [
      'babel-plugin-import',
      {
        libraryName: 'lodash',
        libraryDirectory: '',
        camel2DashComponentName: false,
      },
      'lodash',
    ],
  ].filter(Boolean);

  // 环境特定配置
  const env = {
    // 开发环境
    development: {
      plugins: [
        // 开发工具
        'babel-plugin-dev-expression',
      ],
    },

    // 生产环境
    production: {
      plugins: [
        // 压缩优化
        'babel-plugin-minify-dead-code-elimination',
        'babel-plugin-minify-constant-folding',
      ],
    },

    // 测试环境
    test: {
      presets: [
        [
          '@babel/preset-env',
          {
            targets: {
              node: 'current',
            },
            modules: 'commonjs',
          },
        ],
      ],
      plugins: [
        // 测试相关插件
        'babel-plugin-dynamic-import-node',
      ],
    },
  };

  return {
    presets,
    plugins,
    env,
    // 源码映射
    sourceMaps: isDevelopment ? 'inline' : true,
    // 输入源码映射
    inputSourceMap: true,
    // 紧凑输出
    compact: isProduction,
    // 注释
    comments: !isProduction,
    // 最小化
    minified: isProduction,
    // 辅助函数
    auxiliaryCommentBefore: ' istanbul ignore next ',
  };
};

/**
 * 配置说明：
 * 
 * 1. 预设 (Presets)：
 *    - @babel/preset-env: ES6+ 语法转换
 *    - @babel/preset-react: React JSX 转换
 *    - @babel/preset-typescript: TypeScript 转换
 * 
 * 2. 插件 (Plugins)：
 *    - 语法支持: 类属性、对象展开、可选链等
 *    - 运行时优化: transform-runtime
 *    - 开发工具: react-refresh (热更新)
 *    - 生产优化: 移除 console、debugger
 *    - 样式处理: styled-components
 *    - 按需导入: antd、lodash
 * 
 * 3. 环境配置：
 *    - development: 开发模式，保留调试信息
 *    - production: 生产模式，代码优化
 *    - test: 测试模式，CommonJS 模块
 * 
 * 4. 安装依赖：
 *    npm install --save-dev @babel/core @babel/cli
 *    npm install --save-dev @babel/preset-env @babel/preset-react @babel/preset-typescript
 *    npm install --save-dev @babel/plugin-proposal-class-properties
 *    npm install --save-dev @babel/plugin-proposal-object-rest-spread
 *    npm install --save-dev @babel/plugin-syntax-dynamic-import
 *    npm install --save-dev @babel/plugin-proposal-optional-chaining
 *    npm install --save-dev @babel/plugin-proposal-nullish-coalescing-operator
 *    npm install --save-dev @babel/plugin-proposal-private-methods
 *    npm install --save-dev @babel/plugin-proposal-decorators
 *    npm install --save-dev @babel/plugin-transform-runtime
 *    npm install --save @babel/runtime
 * 
 * 5. 可选插件：
 *    npm install --save-dev react-refresh babel-plugin-styled-components
 *    npm install --save-dev babel-plugin-import babel-plugin-transform-remove-console
 *    npm install --save-dev babel-plugin-transform-remove-debugger
 *    npm install --save-dev babel-plugin-dynamic-import-node
 * 
 * 6. 使用方法：
 *    - 命令行: npx babel src --out-dir dist
 *    - Webpack: 配合 babel-loader 使用
 *    - Jest: 自动读取配置
 *    - Rollup: 配合 @rollup/plugin-babel 使用
 * 
 * 7. 配置文件优先级：
 *    - babel.config.js (推荐，项目级配置)
 *    - .babelrc.js
 *    - .babelrc
 *    - package.json 中的 babel 字段
 * 
 * 8. 性能优化：
 *    - 启用缓存: api.cache(true)
 *    - 按需转换: useBuiltIns: 'usage'
 *    - 排除不必要的插件
 *    - 使用 transform-runtime 减少重复代码
 */

/**
 * 常用配置示例：
 * 
 * // React 项目
 * module.exports = {
 *   presets: [
 *     ['@babel/preset-env', { useBuiltIns: 'usage', corejs: 3 }],
 *     ['@babel/preset-react', { runtime: 'automatic' }]
 *   ],
 *   plugins: [
 *     '@babel/plugin-proposal-class-properties'
 *   ]
 * };
 * 
 * // Vue 项目
 * module.exports = {
 *   presets: [
 *     ['@babel/preset-env', { useBuiltIns: 'usage', corejs: 3 }]
 *   ],
 *   plugins: [
 *     '@babel/plugin-proposal-class-properties',
 *     '@babel/plugin-syntax-dynamic-import'
 *   ]
 * };
 * 
 * // Node.js 项目
 * module.exports = {
 *   presets: [
 *     ['@babel/preset-env', {
 *       targets: { node: 'current' },
 *       modules: 'commonjs'
 *     }],
 *     '@babel/preset-typescript'
 *   ]
 * };
 */