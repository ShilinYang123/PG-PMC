/**
 * PostCSS 配置模板 - 3AI工作室
 * CSS 后处理器配置
 * 支持现代 CSS 特性和优化
 */

module.exports = (ctx) => {
  // 环境检测
  const isDevelopment = ctx.env === 'development';
  const isProduction = ctx.env === 'production';
  const isTest = ctx.env === 'test';

  return {
    // 解析器配置
    parser: require('postcss-comment'),
    
    // 插件配置
    plugins: {
      // CSS 导入处理
      'postcss-import': {
        // 导入路径解析
        resolve: (id, basedir) => {
          // 处理别名
          if (id.startsWith('@/')) {
            return id.replace('@/', './src/');
          }
          if (id.startsWith('~')) {
            return id.slice(1);
          }
          return id;
        },
        // 插件选项
        plugins: [
          require('stylelint'),
        ],
      },

      // 嵌套规则展开
      'postcss-nested': {
        bubble: ['screen'],
        unwrap: ['supports'],
      },

      // 自定义属性 (CSS 变量)
      'postcss-custom-properties': {
        preserve: false,
        importFrom: [
          './src/styles/variables.css',
          {
            customProperties: {
              '--primary-color': '#1890ff',
              '--success-color': '#52c41a',
              '--warning-color': '#faad14',
              '--error-color': '#f5222d',
              '--text-color': '#000000d9',
              '--text-color-secondary': '#00000073',
              '--border-color': '#d9d9d9',
              '--background-color': '#ffffff',
            },
          },
        ],
      },

      // 自定义媒体查询
      'postcss-custom-media': {
        importFrom: [
          {
            customMedia: {
              '--mobile': '(max-width: 767px)',
              '--tablet': '(min-width: 768px) and (max-width: 1023px)',
              '--desktop': '(min-width: 1024px)',
              '--large-desktop': '(min-width: 1440px)',
            },
          },
        ],
      },

      // 自定义选择器
      'postcss-custom-selectors': {
        importFrom: [
          {
            customSelectors: {
              ':--heading': 'h1, h2, h3, h4, h5, h6',
              ':--button': 'button, .btn',
              ':--input': 'input, textarea, select',
            },
          },
        ],
      },

      // 现代 CSS 特性支持
      'postcss-preset-env': {
        // 目标浏览器
        browsers: [
          '> 1%',
          'last 2 versions',
          'not dead',
          'not ie <= 11',
        ],
        // 特性阶段 (0-4)
        stage: 2,
        // 启用的特性
        features: {
          'nesting-rules': true,
          'custom-properties': true,
          'custom-media-queries': true,
          'custom-selectors': true,
          'color-function': true,
          'color-mod-function': true,
          'hexadecimal-alpha-notation': true,
          'lab-function': true,
          'logical-properties-and-values': true,
          'media-query-ranges': true,
          'overflow-shorthand': true,
          'place-properties': true,
          'prefers-color-scheme-query': true,
        },
        // 自动前缀
        autoprefixer: {
          grid: true,
          flexbox: 'no-2009',
        },
      },

      // 浏览器前缀
      autoprefixer: {
        // 目标浏览器
        overrideBrowserslist: [
          '> 1%',
          'last 2 versions',
          'not dead',
          'not ie <= 11',
        ],
        // 网格布局支持
        grid: 'autoplace',
        // Flexbox 支持
        flexbox: 'no-2009',
        // 移除过时前缀
        remove: true,
        // 添加前缀
        add: true,
        // 忽略规则
        ignoreUnknownVersions: false,
      },

      // CSS 模块化
      'postcss-modules': {
        // 生成作用域名称
        generateScopedName: isDevelopment
          ? '[name]__[local]___[hash:base64:5]'
          : '[hash:base64:8]',
        // 全局模式
        globalModulePaths: [
          /node_modules/,
          /global\.css$/,
        ],
        // 导出格式
        exportGlobals: true,
        // 本地化关键词
        localsConvention: 'camelCase',
      },

      // 响应式设计
      'postcss-responsive-type': {
        minSize: '14px',
        maxSize: '18px',
        minWidth: '320px',
        maxWidth: '1200px',
      },

      // 颜色处理
      'postcss-color-function': {},
      'postcss-color-hex-alpha': {},
      'postcss-color-rebeccapurple': {},

      // 字体处理
      'postcss-font-variant': {},
      'postcss-font-family-system-ui': {},

      // 选择器处理
      'postcss-selector-matches': {},
      'postcss-selector-not': {},

      // 伪类处理
      'postcss-pseudo-class-any-link': {},
      'postcss-focus-visible': {},
      'postcss-focus-within': {},

      // 属性处理
      'postcss-logical': {
        preserve: true,
      },
      'postcss-dir-pseudo-class': {},

      // 单位处理
      'postcss-rem-to-pixel': {
        rootValue: 16,
        unitPrecision: 5,
        propList: ['*'],
        selectorBlackList: [],
        replace: true,
        mediaQuery: false,
        minPixelValue: 0,
      },

      // 开发环境插件
      ...(isDevelopment && {
        // CSS 报告
        'postcss-reporter': {
          clearReportedMessages: true,
          throwError: false,
        },
      }),

      // 生产环境插件
      ...(isProduction && {
        // CSS 优化
        cssnano: {
          preset: [
            'default',
            {
              // 丢弃注释
              discardComments: {
                removeAll: true,
              },
              // 标准化显示值
              normalizeDisplayValues: true,
              // 标准化位置值
              normalizePositions: true,
              // 标准化重复样式
              normalizeRepeatStyle: true,
              // 标准化字符串
              normalizeString: true,
              // 标准化时间
              normalizeTimingFunctions: true,
              // 标准化 Unicode
              normalizeUnicode: true,
              // 标准化 URL
              normalizeUrl: true,
              // 标准化空白
              normalizeWhitespace: true,
              // 排序媒体查询
              sortMediaQueries: true,
              // 合并规则
              mergeRules: true,
              // 合并长属性
              mergeLonghand: true,
              // 最小化选择器
              minifySelectors: true,
              // 最小化字体值
              minifyFontValues: true,
              // 最小化渐变
              minifyGradients: true,
              // 最小化参数
              minifyParams: true,
              // 转换颜色
              colormin: true,
              // 转换长度
              convertValues: {
                length: false,
              },
              // 丢弃重复
              discardDuplicates: true,
              // 丢弃空规则
              discardEmpty: true,
              // 丢弃覆盖
              discardOverridden: true,
              // 丢弃未使用
              discardUnused: false,
              // 减少标识符
              reduceIdents: false,
              // 减少初始值
              reduceInitial: true,
              // 减少变换
              reduceTransforms: true,
              // 唯一选择器
              uniqueSelectors: true,
            },
          ],
        },

        // 关键 CSS 提取
        '@fullhuman/postcss-purgecss': {
          content: [
            './src/**/*.{js,jsx,ts,tsx,vue,html}',
            './public/index.html',
          ],
          defaultExtractor: (content) => {
            const broadMatches = content.match(/[^<>"'`\s]*[^<>"'`\s:]/g) || [];
            const innerMatches = content.match(/[^<>"'`\s.()]*[^<>"'`\s.():]/g) || [];
            return broadMatches.concat(innerMatches);
          },
          safelist: {
            standard: [
              /^ant-/,
              /^el-/,
              /^v-/,
              /data-v-/,
              /^router-/,
              /^nuxt-/,
            ],
            deep: [
              /^ant-/,
              /^el-/,
            ],
            greedy: [
              /^ant-/,
              /^el-/,
            ],
          },
        },
      }),

      // 测试环境插件
      ...(isTest && {
        // 测试报告
        'postcss-reporter': {
          clearReportedMessages: true,
          throwError: true,
        },
      }),
    },

    // 源码映射
    map: isDevelopment ? 'inline' : false,
  };
};

/**
 * 使用说明：
 * 
 * 1. 安装依赖：
 *    npm install --save-dev postcss postcss-cli
 *    npm install --save-dev postcss-import postcss-nested
 *    npm install --save-dev postcss-custom-properties postcss-custom-media
 *    npm install --save-dev postcss-custom-selectors postcss-preset-env
 *    npm install --save-dev autoprefixer cssnano
 *    npm install --save-dev postcss-modules postcss-responsive-type
 *    npm install --save-dev @fullhuman/postcss-purgecss
 * 
 * 2. package.json 脚本：
 *    "scripts": {
 *      "css:build": "postcss src/styles/main.css -o dist/main.css",
 *      "css:watch": "postcss src/styles/main.css -o dist/main.css --watch",
 *      "css:prod": "NODE_ENV=production postcss src/styles/main.css -o dist/main.css"
 *    }
 * 
 * 3. 目录结构：
 *    src/
 *    ├── styles/
 *    │   ├── main.css         # 主样式文件
 *    │   ├── variables.css    # CSS 变量
 *    │   ├── components/      # 组件样式
 *    │   ├── utilities/       # 工具类
 *    │   └── vendor/          # 第三方样式
 * 
 * 4. CSS 变量文件 (variables.css)：
 *    :root {
 *      --primary-color: #1890ff;
 *      --success-color: #52c41a;
 *      --warning-color: #faad14;
 *      --error-color: #f5222d;
 *    }
 * 
 * 5. 媒体查询：
 *    @custom-media --mobile (max-width: 767px);
 *    @custom-media --desktop (min-width: 1024px);
 * 
 * 6. 自定义选择器：
 *    @custom-selector :--heading h1, h2, h3, h4, h5, h6;
 *    @custom-selector :--button button, .btn;
 * 
 * 7. 现代 CSS 特性：
 *    .example {
 *      color: color(var(--primary-color) alpha(0.8));
 *      margin-block: 1rem;
 *      inset-inline: 0;
 *    }
 * 
 * 8. CSS 模块化：
 *    .component {
 *      composes: base from './base.css';
 *      color: var(--primary-color);
 *    }
 * 
 * 9. 响应式字体：
 *    .title {
 *      font-size: responsive 14px 18px;
 *      font-range: 320px 1200px;
 *    }
 * 
 * 10. 构建集成：
 *     - Webpack: postcss-loader
 *     - Vite: 内置支持
 *     - Rollup: rollup-plugin-postcss
 *     - Parcel: 内置支持
 */

/**
 * 高级配置示例：
 * 
 * // 条件插件加载
 * const plugins = {
 *   'postcss-import': {},
 *   'postcss-nested': {},
 *   ...(process.env.NODE_ENV === 'production' && {
 *     cssnano: { preset: 'default' }
 *   })
 * };
 * 
 * // 自定义插件
 * const customPlugin = () => {
 *   return {
 *     postcssPlugin: 'custom-plugin',
 *     Rule(rule) {
 *       // 处理规则
 *     }
 *   };
 * };
 * customPlugin.postcss = true;
 * 
 * // 异步配置
 * module.exports = async (ctx) => {
 *   const config = await loadConfig();
 *   return {
 *     plugins: config.plugins
 *   };
 * };
 */