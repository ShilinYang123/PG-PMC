const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // 代理API请求
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:8000',
      changeOrigin: true,
      logLevel: 'debug'
    })
  );
  
  // 代理健康检查端点
  app.use(
    '/health',
    createProxyMiddleware({
      target: 'http://localhost:8000',
      changeOrigin: true,
      logLevel: 'debug'
    })
  );
};