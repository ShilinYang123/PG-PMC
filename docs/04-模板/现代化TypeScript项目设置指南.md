# 现代化 TypeScript 项目设置指南

> 3AI工作室 - 企业级 TypeScript 项目最佳实践

## 📋 目录

- [项目概述](#项目概述)
- [快速开始](#快速开始)
- [配置文件详解](#配置文件详解)
- [开发工作流](#开发工作流)
- [代码质量保证](#代码质量保证)
- [测试策略](#测试策略)
- [部署与发布](#部署与发布)
- [最佳实践](#最佳实践)
- [故障排除](#故障排除)

## 🚀 项目概述

本指南提供了一套完整的现代化 TypeScript 项目配置模板，包含：

- **类型安全**: 严格的 TypeScript 配置
- **代码质量**: ESLint + Prettier 代码规范
- **测试覆盖**: Jest 单元测试和集成测试
- **自动化**: Git hooks 和 CI/CD 流程
- **性能优化**: 构建优化和包大小控制
- **开发体验**: 热重载、调试支持、智能提示

## ⚡ 快速开始

### 1. 项目初始化

```bash
# 创建项目目录
mkdir my-typescript-project
cd my-typescript-project

# 初始化 npm 项目
npm init -y

# 复制配置文件模板
cp ../配置文件模板/* .
```

### 2. 安装依赖

```bash
# 安装生产依赖
npm install express cors helmet morgan compression dotenv joi winston

# 安装开发依赖
npm install -D typescript @types/node @types/express ts-node nodemon
npm install -D jest @types/jest ts-jest supertest @types/supertest
npm install -D eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
npm install -D prettier eslint-plugin-prettier
npm install -D husky lint-staged
```

### 3. 项目结构

```
my-typescript-project/
├── src/
│   ├── controllers/     # 控制器
│   ├── services/        # 业务逻辑
│   ├── models/          # 数据模型
│   ├── middleware/      # 中间件
│   ├── utils/           # 工具函数
│   ├── types/           # 类型定义
│   ├── config/          # 配置文件
│   ├── app.ts           # 应用入口
│   └── index.ts         # 服务器启动
├── tests/
│   ├── unit/            # 单元测试
│   ├── integration/     # 集成测试
│   ├── e2e/             # 端到端测试
│   ├── fixtures/        # 测试数据
│   └── setup.ts         # 测试配置
├── dist/                # 编译输出
├── coverage/            # 测试覆盖率
├── docs/                # 文档
├── scripts/             # 构建脚本
├── .github/             # GitHub Actions
├── tsconfig.json        # TypeScript 配置
├── jest.config.ts       # Jest 配置
├── eslint.config.js     # ESLint 配置
├── prettier.config.js   # Prettier 配置
├── package.json         # 项目配置
└── README.md            # 项目说明
```

## 🔧 配置文件详解

### TypeScript 配置 (`tsconfig.json`)

我们的 TypeScript 配置采用分层架构：

- **基础配置**: 通用编译选项
- **开发配置**: 开发环境特定设置
- **生产配置**: 生产环境优化
- **测试配置**: 测试环境配置

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  }
}
```

**关键特性**:
- ✅ 严格模式启用
- ✅ 路径别名支持
- ✅ 声明文件生成
- ✅ 源码映射
- ✅ JSON 模块支持

### Jest 测试配置 (`jest.config.ts`)

```typescript
const config: Config = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  collectCoverage: true,
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
};
```

**特性**:
- ✅ TypeScript 原生支持
- ✅ 覆盖率阈值控制
- ✅ 并行测试执行
- ✅ 快照测试
- ✅ 模拟和间谍功能

### ESLint 配置 (`eslint.config.js`)

采用 ESLint 9.x 扁平配置格式：

```javascript
export default [
  js.configs.recommended,
  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: {
      parser: typescriptParser,
      parserOptions: {
        project: './tsconfig.json'
      }
    },
    plugins: {
      '@typescript-eslint': typescript
    },
    rules: {
      '@typescript-eslint/no-unused-vars': 'error',
      '@typescript-eslint/explicit-function-return-type': 'error'
    }
  }
];
```

**规则集**:
- ✅ TypeScript 严格检查
- ✅ 安全性规则
- ✅ 性能优化建议
- ✅ 代码风格统一
- ✅ 导入顺序规范

### Prettier 配置 (`prettier.config.js`)

```javascript
const config = {
  printWidth: 100,
  tabWidth: 2,
  useTabs: false,
  semi: true,
  singleQuote: true,
  trailingComma: 'es5',
  bracketSpacing: true,
  arrowParens: 'avoid'
};
```

## 🔄 开发工作流

### 日常开发命令

```bash
# 开发模式（热重载）
npm run dev

# 类型检查
npm run type-check

# 代码检查
npm run lint

# 代码格式化
npm run format

# 运行测试
npm test

# 测试覆盖率
npm run test:coverage

# 构建项目
npm run build

# 生产环境启动
npm start
```

### Git 工作流

```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 开发和提交
git add .
git commit -m "feat: add new feature"

# 3. 推送和创建 PR
git push origin feature/new-feature

# 4. 代码审查后合并
git checkout main
git pull origin main
git branch -d feature/new-feature
```

### 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式化
refactor: 代码重构
test: 测试相关
chore: 构建过程或辅助工具的变动
```

## 🛡️ 代码质量保证

### 自动化检查

通过 Git hooks 实现自动化质量检查：

```json
{
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ]
  },
  "husky": {
    "hooks": {
      "pre-commit": "lint-staged",
      "pre-push": "npm run type-check && npm run test:ci"
    }
  }
}
```

### 代码审查清单

- [ ] 类型定义完整且准确
- [ ] 函数有明确的返回类型
- [ ] 错误处理完善
- [ ] 单元测试覆盖核心逻辑
- [ ] 文档和注释清晰
- [ ] 性能考虑（避免不必要的计算）
- [ ] 安全性检查（输入验证、权限控制）

## 🧪 测试策略

### 测试金字塔

```
    /\     E2E Tests (10%)
   /  \    
  /____\   Integration Tests (20%)
 /______\  
/________\ Unit Tests (70%)
```

### 单元测试示例

```typescript
import { describe, test, expect } from '@jest/globals';
import { validateEmail } from '../utils/validation';

describe('validateEmail', () => {
  test('should return true for valid email', () => {
    expect(validateEmail('test@example.com')).toBe(true);
  });

  test('should return false for invalid email', () => {
    expect(validateEmail('invalid-email')).toBe(false);
  });
});
```

### 集成测试示例

```typescript
import request from 'supertest';
import { app } from '../app';

describe('POST /api/users', () => {
  test('should create a new user', async () => {
    const userData = {
      username: 'testuser',
      email: 'test@example.com',
      password: 'SecurePassword123!'
    };

    const response = await request(app)
      .post('/api/users')
      .send(userData)
      .expect(201);

    expect(response.body).toMatchObject({
      id: expect.any(String),
      username: userData.username,
      email: userData.email
    });
  });
});
```

## 🚀 部署与发布

### 构建优化

```bash
# 生产构建
npm run build:prod

# 分析包大小
npm run analyze

# 检查包大小限制
npm run size
```

### Docker 部署

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY dist ./dist

EXPOSE 3000

CMD ["node", "dist/index.js"]
```

### 环境变量管理

```bash
# 开发环境
NODE_ENV=development
PORT=3000
DB_URL=mongodb://localhost:27017/myapp-dev

# 生产环境
NODE_ENV=production
PORT=8080
DB_URL=mongodb://prod-server:27017/myapp
```

## 💡 最佳实践

### 1. 类型设计

```typescript
// ✅ 好的实践
interface User {
  readonly id: string;
  username: string;
  email: string;
  profile: UserProfile;
  createdAt: Date;
  updatedAt: Date;
}

type UserProfile = {
  firstName: string;
  lastName: string;
  bio?: string;
  avatar?: string;
};

// ❌ 避免的实践
interface User {
  id: any;
  data: any;
}
```

### 2. 错误处理

```typescript
// ✅ 好的实践
class AppError extends Error {
  constructor(
    public message: string,
    public statusCode: number,
    public isOperational = true
  ) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace(this, this.constructor);
  }
}

const handleAsync = (fn: Function) => {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
};
```

### 3. 配置管理

```typescript
// ✅ 好的实践
interface Config {
  port: number;
  database: {
    url: string;
    maxConnections: number;
  };
  jwt: {
    secret: string;
    expiresIn: string;
  };
}

const config: Config = {
  port: Number(process.env.PORT) || 3000,
  database: {
    url: process.env.DB_URL || 'mongodb://localhost:27017/myapp',
    maxConnections: Number(process.env.DB_MAX_CONNECTIONS) || 10,
  },
  jwt: {
    secret: process.env.JWT_SECRET || 'fallback-secret',
    expiresIn: process.env.JWT_EXPIRES_IN || '7d',
  },
};
```

### 4. 性能优化

```typescript
// ✅ 使用适当的数据结构
const userCache = new Map<string, User>();

// ✅ 避免不必要的计算
const memoizedExpensiveFunction = useMemo(() => {
  return expensiveCalculation(data);
}, [data]);

// ✅ 使用流式处理大数据
const processLargeFile = (filePath: string) => {
  return fs.createReadStream(filePath)
    .pipe(csv())
    .pipe(transform((chunk) => processChunk(chunk)));
};
```

## 🔧 故障排除

### 常见问题

#### 1. TypeScript 编译错误

```bash
# 清理编译缓存
npm run clean

# 重新安装依赖
rm -rf node_modules package-lock.json
npm install

# 检查 TypeScript 版本兼容性
npm list typescript
```

#### 2. 测试失败

```bash
# 运行特定测试
npm test -- --testNamePattern="specific test"

# 调试模式
npm run test:debug

# 更新快照
npm test -- --updateSnapshot
```

#### 3. ESLint 错误

```bash
# 自动修复
npm run lint:fix

# 检查配置
npx eslint --print-config src/index.ts

# 忽略特定规则
// eslint-disable-next-line @typescript-eslint/no-explicit-any
```

#### 4. 性能问题

```bash
# 分析构建时间
npm run build -- --verbose

# 检查包大小
npm run analyze

# 内存使用分析
node --inspect dist/index.js
```

### 调试技巧

```typescript
// 1. 使用调试器
debugger;

// 2. 条件断点
if (condition) {
  debugger;
}

// 3. 性能测量
console.time('operation');
// ... 操作代码
console.timeEnd('operation');

// 4. 内存使用
console.log(process.memoryUsage());
```

## 📚 参考资源

### 官方文档
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [ESLint User Guide](https://eslint.org/docs/user-guide/)
- [Prettier Configuration](https://prettier.io/docs/en/configuration.html)

### 社区资源
- [TypeScript Deep Dive](https://basarat.gitbook.io/typescript/)
- [Node.js Best Practices](https://github.com/goldbergyoni/nodebestpractices)
- [Clean Code TypeScript](https://github.com/labs42io/clean-code-typescript)

### 工具推荐
- **IDE**: Visual Studio Code + TypeScript 扩展
- **调试**: Node.js Inspector
- **性能**: Clinic.js
- **监控**: PM2
- **部署**: Docker + Kubernetes

---

## 📝 更新日志

### v1.0.0 (2024-01-15)
- ✨ 初始版本发布
- 🔧 完整的 TypeScript 配置
- 🧪 Jest 测试框架集成
- 🛡️ ESLint + Prettier 代码质量保证
- 📦 现代化构建流程
- 🚀 Docker 部署支持

---

**维护者**: 3AI工作室  
**最后更新**: 2024年1月15日  
**版本**: 1.0.0