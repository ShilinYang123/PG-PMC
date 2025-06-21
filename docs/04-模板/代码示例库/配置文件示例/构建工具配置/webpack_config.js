/**
 * Webpack 配置模板 - 3AI工作室
 * 支持开发和生产环境的完整配置
 * 适用于 React/Vue/Angular 等现代前端项目
 */

const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const TerserPlugin = require('terser-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const webpack = require('webpack');
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;
const CopyWebpackPlugin = require('copy-webpack-plugin');
const ESLintPlugin = require('eslint-webpack-plugin');

// 环境变量
const isDevelopment = process.env.NODE_ENV !== 'production';
const isProduction = !isDevelopment;
const isAnalyze = process.env.ANALYZE === 'true';

// 基础配置
const baseConfig = {
  // 入口文件
  entry: {
    main: './src/index.js',
    // vendor: ['react', 'react-dom'], // 第三方库单独打包
  },

  // 输出配置
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: isProduction 
      ? 'js/[name].[contenthash:8].js' 
      : 'js/[name].js',
    chunkFilename: isProduction 
      ? 'js/[name].[contenthash:8].chunk.js' 
      : 'js/[name].chunk.js',
    publicPath: '/',
    clean: true, // 清理输出目录
    assetModuleFilename: 'assets/[name].[contenthash:8][ext]',
  },

  // 模块解析
  resolve: {
    extensions: ['.js', '.jsx', '.ts', '.tsx', '.json', '.css', '.scss', '.less'],
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@components': path.resolve(__dirname, 'src/components'),
      '@utils': path.resolve(__dirname, 'src/utils'),
      '@assets': path.resolve(__dirname, 'src/assets'),
      '@styles': path.resolve(__dirname, 'src/styles'),
      '@api': path.resolve(__dirname, 'src/api'),
      '@store': path.resolve(__dirname, 'src/store'),
      '@hooks': path.resolve(__dirname, 'src/hooks'),
      '@types': path.resolve(__dirname, 'src/types'),
    },
    fallback: {
      // Node.js polyfills for browser
      "crypto": require.resolve("crypto-browserify"),
      "stream": require.resolve("stream-browserify"),
      "buffer": require.resolve("buffer"),
    },
  },

  // 模块规则
  module: {
    rules: [
      // JavaScript/TypeScript
      {
        test: /\.(js|jsx|ts|tsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              ['@babel/preset-env', {
                useBuiltIns: 'usage',
                corejs: 3,
                targets: {
                  browsers: ['> 1%', 'last 2 versions', 'not ie <= 8']
                }
              }],
              '@babel/preset-react',
              '@babel/preset-typescript'
            ],
            plugins: [
              '@babel/plugin-proposal-class-properties',
              '@babel/plugin-proposal-object-rest-spread',
              '@babel/plugin-syntax-dynamic-import',
              isDevelopment && 'react-refresh/babel'
            ].filter(Boolean),
            cacheDirectory: true,
          },
        },
      },

      // CSS/SCSS/LESS
      {
        test: /\.css$/,
        use: [
          isDevelopment ? 'style-loader' : MiniCssExtractPlugin.loader,
          {
            loader: 'css-loader',
            options: {
              modules: {
                auto: true,
                localIdentName: isDevelopment 
                  ? '[name]__[local]--[hash:base64:5]' 
                  : '[hash:base64:8]',
              },
              sourceMap: isDevelopment,
            },
          },
          {
            loader: 'postcss-loader',
            options: {
              postcssOptions: {
                plugins: [
                  ['autoprefixer'],
                  ['postcss-preset-env'],
                ],
              },
            },
          },
        ],
      },
      {
        test: /\.(scss|sass)$/,
        use: [
          isDevelopment ? 'style-loader' : MiniCssExtractPlugin.loader,
          'css-loader',
          'postcss-loader',
          'sass-loader',
        ],
      },
      {
        test: /\.less$/,
        use: [
          isDevelopment ? 'style-loader' : MiniCssExtractPlugin.loader,
          'css-loader',
          'postcss-loader',
          {
            loader: 'less-loader',
            options: {
              lessOptions: {
                javascriptEnabled: true,
              },
            },
          },
        ],
      },

      // 图片和字体
      {
        test: /\.(png|jpe?g|gif|svg|webp)$/i,
        type: 'asset',
        parser: {
          dataUrlCondition: {
            maxSize: 8 * 1024, // 8KB
          },
        },
        generator: {
          filename: 'images/[name].[contenthash:8][ext]',
        },
      },
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'fonts/[name].[contenthash:8][ext]',
        },
      },

      // 其他资源
      {
        test: /\.(mp4|webm|ogg|mp3|wav|flac|aac)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'media/[name].[contenthash:8][ext]',
        },
      },
    ],
  },

  // 插件
  plugins: [
    // HTML 模板
    new HtmlWebpackPlugin({
      template: './public/index.html',
      filename: 'index.html',
      inject: true,
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeRedundantAttributes: true,
        useShortDoctype: true,
        removeEmptyAttributes: true,
        removeStyleLinkTypeAttributes: true,
        keepClosingSlash: true,
        minifyJS: true,
        minifyCSS: true,
        minifyURLs: true,
      } : false,
    }),

    // 环境变量
    new webpack.DefinePlugin({
      'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV),
      'process.env.PUBLIC_URL': JSON.stringify(process.env.PUBLIC_URL || ''),
      __DEV__: isDevelopment,
      __PROD__: isProduction,
    }),

    // ESLint
    new ESLintPlugin({
      extensions: ['js', 'jsx', 'ts', 'tsx'],
      exclude: 'node_modules',
      emitWarning: isDevelopment,
      emitError: isProduction,
      failOnError: isProduction,
    }),

    // 复制静态资源
    new CopyWebpackPlugin({
      patterns: [
        {
          from: 'public',
          to: '.',
          globOptions: {
            ignore: ['**/index.html'],
          },
        },
      ],
    }),

    // 生产环境插件
    ...(isProduction ? [
      new MiniCssExtractPlugin({
        filename: 'css/[name].[contenthash:8].css',
        chunkFilename: 'css/[name].[contenthash:8].chunk.css',
      }),
    ] : []),

    // 开发环境插件
    ...(isDevelopment ? [
      new webpack.HotModuleReplacementPlugin(),
    ] : []),

    // 分析插件
    ...(isAnalyze ? [
      new BundleAnalyzerPlugin({
        analyzerMode: 'static',
        openAnalyzer: false,
        reportFilename: 'bundle-analyzer-report.html',
      }),
    ] : []),
  ].filter(Boolean),

  // 优化配置
  optimization: {
    minimize: isProduction,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: isProduction,
            drop_debugger: isProduction,
          },
          format: {
            comments: false,
          },
        },
        extractComments: false,
      }),
      new CssMinimizerPlugin(),
    ],
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
          priority: 10,
        },
        common: {
          name: 'common',
          minChunks: 2,
          chunks: 'all',
          priority: 5,
          reuseExistingChunk: true,
        },
      },
    },
    runtimeChunk: {
      name: 'runtime',
    },
  },

  // 性能配置
  performance: {
    hints: isProduction ? 'warning' : false,
    maxEntrypointSize: 512000,
    maxAssetSize: 512000,
  },

  // 统计信息
  stats: {
    colors: true,
    modules: false,
    children: false,
    chunks: false,
    chunkModules: false,
  },
};

// 开发环境配置
const developmentConfig = {
  mode: 'development',
  devtool: 'eval-cheap-module-source-map',
  devServer: {
    static: {
      directory: path.join(__dirname, 'public'),
    },
    port: 3000,
    hot: true,
    open: true,
    compress: true,
    historyApiFallback: true,
    client: {
      overlay: {
        errors: true,
        warnings: false,
      },
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
};

// 生产环境配置
const productionConfig = {
  mode: 'production',
  devtool: 'source-map',
};

// 导出配置
module.exports = {
  ...baseConfig,
  ...(isDevelopment ? developmentConfig : productionConfig),
};

/**
 * 使用说明：
 * 
 * 1. 安装依赖：
 *    npm install --save-dev webpack webpack-cli webpack-dev-server
 *    npm install --save-dev html-webpack-plugin mini-css-extract-plugin
 *    npm install --save-dev css-minimizer-webpack-plugin terser-webpack-plugin
 *    npm install --save-dev clean-webpack-plugin copy-webpack-plugin
 *    npm install --save-dev eslint-webpack-plugin webpack-bundle-analyzer
 *    npm install --save-dev babel-loader @babel/core @babel/preset-env
 *    npm install --save-dev @babel/preset-react @babel/preset-typescript
 *    npm install --save-dev css-loader style-loader postcss-loader
 *    npm install --save-dev sass-loader less-loader autoprefixer
 * 
 * 2. package.json 脚本：
 *    "scripts": {
 *      "start": "webpack serve --mode development",
 *      "build": "webpack --mode production",
 *      "analyze": "ANALYZE=true webpack --mode production"
 *    }
 * 
 * 3. 环境变量：
 *    - NODE_ENV: development/production
 *    - ANALYZE: true (启用打包分析)
 *    - PUBLIC_URL: 公共资源路径
 * 
 * 4. 目录结构：
 *    src/
 *    ├── index.js          # 入口文件
 *    ├── components/       # 组件
 *    ├── utils/           # 工具函数
 *    ├── assets/          # 静态资源
 *    ├── styles/          # 样式文件
 *    ├── api/             # API接口
 *    ├── store/           # 状态管理
 *    ├── hooks/           # 自定义Hooks
 *    └── types/           # 类型定义
 * 
 * 5. 特性：
 *    - 支持 React/Vue/Angular
 *    - TypeScript 支持
 *    - CSS Modules
 *    - 热更新
 *    - 代码分割
 *    - 打包优化
 *    - ESLint 集成
 *    - 开发服务器
 *    - 生产构建
 */