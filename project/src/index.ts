/**
 * 3AI项目主入口文件
 *
 * 这是项目的主要启动文件，负责初始化应用程序。
 */

import express, { Request, Response } from 'express';
import cors from 'cors';
import helmet from 'helmet';

// 导入配置
import { getAppConfig } from './config/config_reader';
const config = getAppConfig();

// 创建Express应用
const app = express();

// 设置端口和主机（完全依赖统一配置）
const PORT = config.port;
const HOST = config.host;

// 中间件配置
app.use(helmet()); // 安全中间件
app.use(cors()); // 跨域中间件
app.use(express.json()); // JSON解析中间件
app.use(express.urlencoded({ extended: true })); // URL编码中间件

// 基础路由
app.get('/', (req: Request, res: Response) => {
  res.json({
    message: '欢迎使用3AI工作室项目！',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development',
  });
});

// 健康检查端点
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
    memory: process.memoryUsage(),
  });
});

// API路由
app.get('/api/info', (req: Request, res: Response) => {
  res.json({
    project: '3AI工作室项目',
    description: '基于3AI工作室通用开发框架模板构建',
    features: [
      '标准化目录结构',
      '开发环境容器化',
      '代码规范自动化',
      'CI/CD流水线',
      '健康检查机制',
    ],
  });
});

// 错误处理中间件
app.use((err: any, req: Request, res: Response) => {
  console.error('错误详情:', err.stack);
  res.status(500).json({
    error: '服务器内部错误',
    message:
      process.env.NODE_ENV === 'development' ? err.message : '请联系管理员',
  });
});

// 404处理
app.use((req: Request, res: Response) => {
  res.status(404).json({
    error: '页面未找到',
    path: req.path,
    method: req.method,
  });
});

// 启动服务器
function startServer() {
  app.listen(PORT, () => {
    console.log('🚀 3AI项目服务器启动成功!');
    console.log(`📍 服务地址: http://${HOST}:${PORT}`);
    console.log(`🌍 环境: ${process.env.NODE_ENV || 'development'}`);
    console.log(`⏰ 启动时间: ${new Date().toLocaleString('zh-CN')}`);
    console.log('='.repeat(50));
  });
}

// 优雅关闭处理
process.on('SIGTERM', () => {
  console.log('\n收到SIGTERM信号，正在优雅关闭服务器...');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('\n收到SIGINT信号，正在优雅关闭服务器...');
  process.exit(0);
});

// 启动应用
if (require.main === module) {
  startServer();
}

export default app;
