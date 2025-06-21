/**
 * Rollup 配置模板 - 3AI工作室
 * 现代 JavaScript 库打包工具配置
 * 适用于组件库、工具库、SDK 等项目
 */

import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import typescript from '@rollup/plugin-typescript';
import babel from '@rollup/plugin-babel';
import terser from '@rollup/plugin-terser';
import postcss from 'rollup-plugin-postcss';
import { visualizer } from 'rollup-plugin-visualizer';
import copy from 'rollup-plugin-copy';
import del from 'rollup-plugin-delete';
import json from '@rollup/plugin-json';
import alias from '@rollup/plugin-alias';
import replace from '@rollup/plugin-replace';
import filesize from 'rollup-plugin-filesize';
import progress from 'rollup-plugin-progress';
import { createRequire } from 'module';
import path from 'path';

const require = createRequire(import.meta.url);
const pkg = require('./package.json');

// 环境变量
const isDevelopment = process.env.NODE_ENV === 'development';
const isProduction = process.env.NODE_ENV === 'production';
const isAnalyze = process.env.ANALYZE === 'true';

// 外部依赖 (不打包进最终文件)
const external = [
  ...Object.keys(pkg.dependencies || {}),
  ...Object.keys(pkg.peerDependencies || {}),
  // React 相关
  'react',
  'react-dom',
  'react/jsx-runtime',
  // Vue 相关
  'vue',
  '@vue/runtime-core',
  // Node.js 内置模块
  'path',
  'fs',
  'util',
  'crypto',
  'stream',
  'events',
];

// 全局变量映射
const globals = {
  react: 'React',
  'react-dom': 'ReactDOM',
  vue: 'Vue',
  lodash: '_',
  axios: 'axios',
  dayjs: 'dayjs',
};

// 通用插件
const getPlugins = (format) => [
  // 清理输出目录
  del({ targets: 'dist/*' }),
  
  // 进度显示
  progress(),
  
  // 路径别名
  alias({
    entries: [
      { find: '@', replacement: path.resolve('src') },
      { find: '@components', replacement: path.resolve('src/components') },
      { find: '@utils', replacement: path.resolve('src/utils') },
      { find: '@types', replacement: path.resolve('src/types') },
    ],
  }),
  
  // JSON 支持
  json(),
  
  // Node.js 模块解析
  resolve({
    browser: format === 'umd',
    preferBuiltins: format !== 'umd',
    extensions: ['.js', '.jsx', '.ts', '.tsx', '.json'],
  }),
  
  // CommonJS 转换
  commonjs({
    include: 'node_modules/**',
    exclude: ['node_modules/process-es6/**'],
  }),
  
  // TypeScript 编译
  typescript({
    tsconfig: './tsconfig.json',
    declaration: format === 'es',
    declarationDir: 'dist/types',
    exclude: ['**/*.test.*', '**/*.spec.*', 'src/test/**'],
    sourceMap: !isProduction,
  }),
  
  // Babel 转换
  babel({
    babelHelpers: 'bundled',
    exclude: 'node_modules/**',
    extensions: ['.js', '.jsx', '.ts', '.tsx'],
    presets: [
      [
        '@babel/preset-env',
        {
          targets: format === 'umd' ? '> 1%, not dead' : { node: '12' },
          modules: false,
        },
      ],
      '@babel/preset-react',
      '@babel/preset-typescript',
    ],
    plugins: [
      '@babel/plugin-proposal-class-properties',
      '@babel/plugin-proposal-object-rest-spread',
    ],
  }),
  
  // CSS 处理
  postcss({
    extract: true,
    minimize: isProduction,
    sourceMap: !isProduction,
    plugins: [
      require('autoprefixer'),
      require('postcss-preset-env'),
    ],
  }),
  
  // 环境变量替换
  replace({
    preventAssignment: true,
    values: {
      'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV),
      __VERSION__: JSON.stringify(pkg.version),
      __DEV__: !isProduction,
      __PROD__: isProduction,
    },
  }),
  
  // 生产环境压缩
  ...(isProduction ? [
    terser({
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
      format: {
        comments: false,
      },
    }),
  ] : []),
  
  // 复制静态文件
  copy({
    targets: [
      { src: 'README.md', dest: 'dist' },
      { src: 'LICENSE', dest: 'dist' },
      { src: 'package.json', dest: 'dist' },
    ],
  }),
  
  // 文件大小报告
  filesize(),
  
  // 打包分析
  ...(isAnalyze ? [
    visualizer({
      filename: 'dist/stats.html',
      open: true,
      gzipSize: true,
      brotliSize: true,
    }),
  ] : []),
];

// 配置数组
const configs = [];

// ES Module 构建
configs.push({
  input: 'src/index.ts',
  output: {
    file: pkg.module || 'dist/index.esm.js',
    format: 'es',
    sourcemap: !isProduction,
    exports: 'named',
  },
  external,
  plugins: getPlugins('es'),
});

// CommonJS 构建
configs.push({
  input: 'src/index.ts',
  output: {
    file: pkg.main || 'dist/index.cjs.js',
    format: 'cjs',
    sourcemap: !isProduction,
    exports: 'named',
  },
  external,
  plugins: getPlugins('cjs'),
});

// UMD 构建 (浏览器)
configs.push({
  input: 'src/index.ts',
  output: {
    file: pkg.browser || 'dist/index.umd.js',
    format: 'umd',
    name: pkg.name.replace(/[@\/\-]/g, ''),
    sourcemap: !isProduction,
    globals,
    exports: 'named',
  },
  external: Object.keys(globals),
  plugins: getPlugins('umd'),
});

// 压缩版 UMD 构建
if (isProduction) {
  configs.push({
    input: 'src/index.ts',
    output: {
      file: 'dist/index.umd.min.js',
      format: 'umd',
      name: pkg.name.replace(/[@\/\-]/g, ''),
      sourcemap: true,
      globals,
      exports: 'named',
    },
    external: Object.keys(globals),
    plugins: [
      ...getPlugins('umd'),
      terser({
        compress: {
          drop_console: true,
          drop_debugger: true,
          pure_funcs: ['console.log'],
        },
        format: {
          comments: false,
        },
      }),
    ],
  });
}

// 组件库单独构建
if (pkg.components) {
  const componentConfigs = Object.entries(pkg.components).map(([name, entry]) => ({
    input: entry,
    output: [
      {
        file: `dist/components/${name}.esm.js`,
        format: 'es',
        sourcemap: !isProduction,
      },
      {
        file: `dist/components/${name}.cjs.js`,
        format: 'cjs',
        sourcemap: !isProduction,
      },
    ],
    external,
    plugins: getPlugins('es'),
  }));
  
  configs.push(...componentConfigs);
}

export default configs;

/**
 * 配置说明：
 * 
 * 1. 输出格式：
 *    - ES Module (esm): 现代打包工具使用
 *    - CommonJS (cjs): Node.js 环境使用
 *    - UMD (umd): 浏览器直接引用
 *    - 压缩版: 生产环境优化
 * 
 * 2. 插件功能：
 *    - @rollup/plugin-node-resolve: 解析 Node.js 模块
 *    - @rollup/plugin-commonjs: CommonJS 转换
 *    - @rollup/plugin-typescript: TypeScript 编译
 *    - @rollup/plugin-babel: Babel 转换
 *    - @rollup/plugin-terser: 代码压缩
 *    - rollup-plugin-postcss: CSS 处理
 *    - rollup-plugin-visualizer: 打包分析
 * 
 * 3. 安装依赖：
 *    npm install --save-dev rollup
 *    npm install --save-dev @rollup/plugin-node-resolve
 *    npm install --save-dev @rollup/plugin-commonjs
 *    npm install --save-dev @rollup/plugin-typescript
 *    npm install --save-dev @rollup/plugin-babel
 *    npm install --save-dev @rollup/plugin-terser
 *    npm install --save-dev @rollup/plugin-json
 *    npm install --save-dev @rollup/plugin-alias
 *    npm install --save-dev @rollup/plugin-replace
 *    npm install --save-dev rollup-plugin-postcss
 *    npm install --save-dev rollup-plugin-visualizer
 *    npm install --save-dev rollup-plugin-copy
 *    npm install --save-dev rollup-plugin-delete
 *    npm install --save-dev rollup-plugin-filesize
 *    npm install --save-dev rollup-plugin-progress
 * 
 * 4. package.json 配置：
 *    {
 *      "main": "dist/index.cjs.js",
 *      "module": "dist/index.esm.js",
 *      "browser": "dist/index.umd.js",
 *      "types": "dist/types/index.d.ts",
 *      "files": ["dist"],
 *      "scripts": {
 *        "build": "rollup -c",
 *        "build:watch": "rollup -c -w",
 *        "build:analyze": "ANALYZE=true rollup -c"
 *      }
 *    }
 * 
 * 5. 使用场景：
 *    - 组件库打包
 *    - 工具库打包
 *    - SDK 开发
 *    - 插件开发
 *    - 多格式输出
 * 
 * 6. 优化特性：
 *    - Tree Shaking
 *    - 代码分割
 *    - 外部依赖排除
 *    - 压缩优化
 *    - 源码映射
 *    - 类型定义生成
 * 
 * 7. 开发命令：
 *    npm run build          # 构建所有格式
 *    npm run build:watch    # 监听模式构建
 *    npm run build:analyze  # 分析打包结果
 * 
 * 8. 目录结构：
 *    src/
 *    ├── index.ts          # 主入口
 *    ├── components/       # 组件
 *    ├── utils/           # 工具函数
 *    └── types/           # 类型定义
 *    dist/
 *    ├── index.esm.js     # ES Module
 *    ├── index.cjs.js     # CommonJS
 *    ├── index.umd.js     # UMD
 *    ├── index.umd.min.js # 压缩版 UMD
 *    ├── types/           # 类型定义
 *    └── components/      # 单独组件
 */

/**
 * 高级配置示例：
 * 
 * // 多入口构建
 * export default {
 *   input: {
 *     main: 'src/index.ts',
 *     utils: 'src/utils/index.ts',
 *     components: 'src/components/index.ts'
 *   },
 *   output: {
 *     dir: 'dist',
 *     format: 'es',
 *     entryFileNames: '[name].js',
 *     chunkFileNames: '[name]-[hash].js'
 *   }
 * };
 * 
 * // 条件构建
 * const config = {
 *   input: 'src/index.ts',
 *   output: {
 *     file: 'dist/index.js',
 *     format: process.env.FORMAT || 'es'
 *   },
 *   plugins: [
 *     // 基础插件
 *     resolve(),
 *     commonjs(),
 *     // 条件插件
 *     ...(process.env.NODE_ENV === 'production' ? [terser()] : [])
 *   ]
 * };
 * 
 * // 外部依赖配置
 * const external = (id) => {
 *   return /^react/.test(id) || /^lodash/.test(id);
 * };
 */