/**
 * 3AI项目客户端入口文件
 */

// 基础样式导入
import './styles/main.css';

// 主应用初始化
class App {
  constructor() {
    this.init();
  }

  private init(): void {
    console.log('3AI项目客户端已启动');
    this.setupEventListeners();
    this.renderWelcomeMessage();
  }

  private setupEventListeners(): void {
    document.addEventListener('DOMContentLoaded', () => {
      console.log('DOM已加载完成');
    });
  }

  private renderWelcomeMessage(): void {
    const app = document.getElementById('app');
    if (app) {
      app.innerHTML = `
        <div class="container mx-auto px-4 py-8">
          <h1 class="text-4xl font-bold text-center mb-8">欢迎使用3AI工作室项目</h1>
          <div class="max-w-2xl mx-auto">
            <p class="text-lg text-gray-600 mb-4">这是一个基于现代技术栈构建的全栈项目。</p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="bg-blue-50 p-4 rounded-lg">
                <h3 class="font-semibold mb-2">前端技术</h3>
                <ul class="text-sm text-gray-600">
                  <li>• TypeScript</li>
                  <li>• Webpack</li>
                  <li>• Tailwind CSS</li>
                </ul>
              </div>
              <div class="bg-green-50 p-4 rounded-lg">
                <h3 class="font-semibold mb-2">后端技术</h3>
                <ul class="text-sm text-gray-600">
                  <li>• Node.js</li>
                  <li>• Express</li>
                  <li>• TypeScript</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      `;
    }
  }
}

// 启动应用
new App();
