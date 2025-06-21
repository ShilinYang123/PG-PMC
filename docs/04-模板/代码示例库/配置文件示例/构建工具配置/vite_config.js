/**
 * Vite 配置模板 - 3AI工作室
 * 现代前端构建工具配置
 * 支持 React/Vue/Vanilla JS/TypeScript
 */

import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';
import { createSvgIconsPlugin } from 'vite-plugin-svg-icons';
import { visualizer } from 'rollup-plugin-visualizer';
import legacy from '@vitejs/plugin-legacy';
import { createHtmlPlugin } from 'vite-plugin-html';
import eslint from 'vite-plugin-eslint';
import { defineConfig as defineVitestConfig } from 'vitest/config';

// 路径解析函数
const pathResolve = (dir) => resolve(process.cwd(), '.', dir);

// 导出配置
export default defineConfig(({ command, mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '');
  const isDev = command === 'serve';
  const isProd = command === 'build';
  
  // 基础配置
  const config = {
    // 基础路径
    base: env.VITE_PUBLIC_PATH || '/',
    
    // 环境变量前缀
    envPrefix: 'VITE_',
    
    // 开发服务器配置
    server: {
      host: '0.0.0.0',
      port: Number(env.VITE_PORT) || 3000,
      open: true,
      cors: true,
      strictPort: false,
      // 代理配置
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
        '/upload': {
          target: env.VITE_UPLOAD_URL || 'http://localhost:8000',
          changeOrigin: true,
        },
        // WebSocket 代理
        '/ws': {
          target: 'ws://localhost:8000',
          ws: true,
        },
      },
      // 预热文件
      warmup: {
        clientFiles: ['./src/main.{js,ts}', './src/App.{vue,jsx,tsx}'],
      },
    },
    
    // 预览服务器配置
    preview: {
      port: 4173,
      host: '0.0.0.0',
      strictPort: true,
    },
    
    // 路径解析
    resolve: {
      alias: {
        '@': pathResolve('src'),
        '@components': pathResolve('src/components'),
        '@utils': pathResolve('src/utils'),
        '@assets': pathResolve('src/assets'),
        '@styles': pathResolve('src/styles'),
        '@api': pathResolve('src/api'),
        '@store': pathResolve('src/store'),
        '@hooks': pathResolve('src/hooks'),
        '@types': pathResolve('src/types'),
        '@views': pathResolve('src/views'),
        '@layouts': pathResolve('src/layouts'),
        '@router': pathResolve('src/router'),
        '@plugins': pathResolve('src/plugins'),
        '@directives': pathResolve('src/directives'),
        // Vue 特定别名
        'vue-i18n': 'vue-i18n/dist/vue-i18n.cjs.js',
      },
      extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue'],
    },
    
    // CSS 配置
    css: {
      // CSS 预处理器
      preprocessorOptions: {
        scss: {
          additionalData: `
            @import "@/styles/variables.scss";
            @import "@/styles/mixins.scss";
          `,
          charset: false,
        },
        less: {
          additionalData: `@import "@/styles/variables.less";`,
          javascriptEnabled: true,
          modifyVars: {
            // Ant Design 主题定制
            '@primary-color': '#1890ff',
            '@link-color': '#1890ff',
            '@success-color': '#52c41a',
            '@warning-color': '#faad14',
            '@error-color': '#f5222d',
          },
        },
      },
      // PostCSS 配置
      postcss: {
        plugins: [
          require('autoprefixer'),
          require('postcss-preset-env'),
          require('cssnano')({
            preset: 'default',
          }),
        ],
      },
      // CSS Modules
      modules: {
        localsConvention: 'camelCase',
        generateScopedName: isDev
          ? '[name]__[local]___[hash:base64:5]'
          : '[hash:base64:8]',
      },
    },
    
    // 插件配置
    plugins: [
      // React 支持
      react({
        // React 刷新
        fastRefresh: isDev,
        // Babel 配置
        babel: {
          plugins: [
            ['@babel/plugin-proposal-decorators', { legacy: true }],
            ['@babel/plugin-proposal-class-properties', { loose: true }],
          ],
        },
      }),
      
      // Vue 支持
      vue({
        include: [/\.vue$/],
        reactivityTransform: true,
      }),
      
      // ESLint
      eslint({
        include: ['src/**/*.{js,jsx,ts,tsx,vue}'],
        exclude: ['node_modules'],
        cache: false,
      }),
      
      // HTML 模板
      createHtmlPlugin({
        minify: isProd,
        inject: {
          data: {
            title: env.VITE_APP_TITLE || '3AI工作室',
            description: env.VITE_APP_DESCRIPTION || '现代化前端应用',
            keywords: env.VITE_APP_KEYWORDS || 'vite,react,vue,typescript',
          },
        },
      }),
      
      // SVG 图标
      createSvgIconsPlugin({
        iconDirs: [pathResolve('src/assets/icons')],
        symbolId: 'icon-[dir]-[name]',
        inject: 'body-last',
        customDomId: '__svg__icons__dom__',
      }),
      
      // 浏览器兼容性
      legacy({
        targets: ['defaults', 'not IE 11'],
        additionalLegacyPolyfills: ['regenerator-runtime/runtime'],
        renderLegacyChunks: true,
        polyfills: [
          'es.symbol',
          'es.array.filter',
          'es.promise',
          'es.promise.finally',
          'es/map',
          'es/set',
          'es.array.for-each',
          'es.object.define-properties',
          'es.object.define-property',
          'es.object.get-own-property-descriptor',
          'es.object.get-own-property-descriptors',
          'es.object.keys',
          'es.object.to-string',
          'web.dom-collections.for-each',
          'esnext.global-this',
          'esnext.string.match-all',
        ],
      }),
      
      // 打包分析
      ...(env.ANALYZE === 'true' ? [
        visualizer({
          filename: 'dist/stats.html',
          open: true,
          gzipSize: true,
          brotliSize: true,
        }),
      ] : []),
    ],
    
    // 构建配置
    build: {
      target: 'es2015',
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: env.VITE_SOURCEMAP === 'true',
      minify: 'terser',
      // Terser 配置
      terserOptions: {
        compress: {
          drop_console: isProd,
          drop_debugger: isProd,
        },
      },
      // 分包策略
      rollupOptions: {
        input: {
          main: pathResolve('index.html'),
        },
        output: {
          chunkFileNames: 'js/[name]-[hash].js',
          entryFileNames: 'js/[name]-[hash].js',
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name.split('.');
            let extType = info[info.length - 1];
            if (/\.(mp4|webm|ogg|mp3|wav|flac|aac)(\?.*)?$/i.test(assetInfo.name)) {
              extType = 'media';
            } else if (/\.(png|jpe?g|gif|svg|webp)(\?.*)?$/i.test(assetInfo.name)) {
              extType = 'images';
            } else if (/\.(woff2?|eot|ttf|otf)(\?.*)?$/i.test(assetInfo.name)) {
              extType = 'fonts';
            }
            return `${extType}/[name]-[hash].[ext]`;
          },
          manualChunks: {
            // 第三方库分包
            vendor: ['react', 'react-dom'],
            antd: ['antd'],
            lodash: ['lodash-es'],
            // 工具库分包
            utils: ['axios', 'dayjs'],
          },
        },
        external: [],
      },
      // 资源内联阈值
      assetsInlineLimit: 4096,
      // CSS 代码分割
      cssCodeSplit: true,
      // 生成 manifest
      manifest: true,
      // 清空输出目录
      emptyOutDir: true,
      // 报告压缩后的大小
      reportCompressedSize: false,
      // 分块大小警告限制
      chunkSizeWarningLimit: 2000,
    },
    
    // 依赖优化
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-router-dom',
        'axios',
        'lodash-es',
        'dayjs',
      ],
      exclude: [
        'vue-demi',
      ],
      // 强制预构建
      force: false,
    },
    
    // 定义全局常量
    define: {
      __DEV__: isDev,
      __PROD__: isProd,
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
      __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
    },
    
    // 日志级别
    logLevel: 'info',
    
    // 清除控制台
    clearScreen: false,
    
    // 测试配置 (Vitest)
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.ts'],
      include: ['src/**/*.{test,spec}.{js,ts,jsx,tsx}'],
      exclude: ['node_modules', 'dist'],
      coverage: {
        provider: 'v8',
        reporter: ['text', 'json', 'html'],
        exclude: [
          'node_modules/',
          'src/test/',
          '**/*.d.ts',
          '**/*.config.{js,ts}',
        ],
      },
    },
  };
  
  return config;
});

/**
 * 使用说明：
 * 
 * 1. 安装依赖：
 *    npm install --save-dev vite @vitejs/plugin-react @vitejs/plugin-vue
 *    npm install --save-dev @vitejs/plugin-legacy vite-plugin-eslint
 *    npm install --save-dev vite-plugin-html vite-plugin-svg-icons
 *    npm install --save-dev rollup-plugin-visualizer vitest jsdom
 * 
 * 2. 环境变量 (.env 文件)：
 *    VITE_PORT=3000
 *    VITE_PUBLIC_PATH=/
 *    VITE_API_BASE_URL=http://localhost:8000
 *    VITE_APP_TITLE=3AI工作室
 *    VITE_SOURCEMAP=true
 *    ANALYZE=false
 * 
 * 3. package.json 脚本：
 *    "scripts": {
 *      "dev": "vite",
 *      "build": "vite build",
 *      "preview": "vite preview",
 *      "test": "vitest",
 *      "test:ui": "vitest --ui",
 *      "coverage": "vitest --coverage",
 *      "analyze": "ANALYZE=true vite build"
 *    }
 * 
 * 4. 目录结构：
 *    src/
 *    ├── main.{js,ts}      # 入口文件
 *    ├── App.{vue,jsx,tsx} # 根组件
 *    ├── components/       # 组件
 *    ├── views/           # 页面
 *    ├── router/          # 路由
 *    ├── store/           # 状态管理
 *    ├── api/             # API接口
 *    ├── utils/           # 工具函数
 *    ├── hooks/           # 自定义Hooks
 *    ├── styles/          # 样式文件
 *    ├── assets/          # 静态资源
 *    └── types/           # 类型定义
 * 
 * 5. 特性：
 *    - 极快的冷启动
 *    - 即时热更新
 *    - 真正的按需编译
 *    - 丰富的插件生态
 *    - 内置 TypeScript 支持
 *    - CSS 预处理器支持
 *    - 现代浏览器原生 ESM
 *    - 生产环境 Rollup 打包
 * 
 * 6. 性能优化：
 *    - 预构建依赖
 *    - 代码分割
 *    - 资源压缩
 *    - Tree Shaking
 *    - 浏览器缓存
 *    - Gzip/Brotli 压缩
 * 
 * 7. 开发体验：
 *    - 快速重载
 *    - 错误覆盖
 *    - 源码映射
 *    - 调试支持
 *    - 类型检查
 *    - ESLint 集成
 */