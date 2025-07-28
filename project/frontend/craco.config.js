const path = require('path');

module.exports = {
  webpack: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  devServer: {
    setupMiddlewares: (middlewares, devServer) => {
      // 加载setupProxy.js
      if (devServer && devServer.app) {
        const setupProxy = require('./src/setupProxy');
        setupProxy(devServer.app);
      }
      return middlewares;
    },
  },
};