const HOST = process.env.HOST || 'localhost';
const PORT = process.env.PORT || '3000';

module.exports = {
  ci: {
    collect: {
      // 收集配置
      url: [
        `http://${HOST}:${PORT}`,
        `http://${HOST}:${PORT}/dashboard`,
        `http://${HOST}:${PORT}/api/health`
      ],
      startServerCommand: 'npm run build && npx serve -s build -l 3000',
      startServerReadyPattern: 'Local:',
      startServerReadyTimeout: 30000,
      numberOfRuns: 3,
      settings: {
        chromeFlags: '--no-sandbox --headless',
        preset: 'desktop',
        onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
        skipAudits: [
          'canonical',
          'maskable-icon',
          'offline-start-url',
          'service-worker'
        ]
      }
    },
    assert: {
      // 断言配置 - 性能阈值
      assertions: {
        'categories:performance': ['warn', { minScore: 0.8 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'categories:best-practices': ['warn', { minScore: 0.85 }],
        'categories:seo': ['warn', { minScore: 0.8 }],
        
        // 核心Web指标
        'first-contentful-paint': ['warn', { maxNumericValue: 2000 }],
        'largest-contentful-paint': ['warn', { maxNumericValue: 2500 }],
        'cumulative-layout-shift': ['warn', { maxNumericValue: 0.1 }],
        'total-blocking-time': ['warn', { maxNumericValue: 300 }],
        
        // 其他重要指标
        'speed-index': ['warn', { maxNumericValue: 3000 }],
        'interactive': ['warn', { maxNumericValue: 3000 }],
        'max-potential-fid': ['warn', { maxNumericValue: 130 }],
        
        // 资源优化
        'unused-javascript': ['warn', { maxNumericValue: 40000 }],
        'unused-css-rules': ['warn', { maxNumericValue: 20000 }],
        'render-blocking-resources': ['warn', { maxNumericValue: 500 }],
        
        // 图片优化
        'modern-image-formats': 'off',
        'uses-optimized-images': 'warn',
        'uses-responsive-images': 'warn',
        
        // 网络优化
        'uses-http2': 'warn',
        'uses-text-compression': 'warn',
        'efficient-animated-content': 'warn'
      }
    },
    upload: {
      // 上传配置
      target: 'temporary-public-storage',
      // 如果使用LHCI服务器，配置如下：
      // target: 'lhci',
      // serverBaseUrl: 'https://your-lhci-server.com',
      // token: process.env.LHCI_TOKEN
    },
    server: {
      // 本地服务器配置（如果运行LHCI服务器）
      port: 9001,
      storage: {
        storageMethod: 'sql',
        sqlDialect: 'sqlite',
        sqlDatabasePath: './lhci.db'
      }
    },
    wizard: {
      // 向导配置
      preset: 'ci'
    }
  }
};