# TypeScript 配置文件说明

## 概述

本目录包含了完整的 TypeScript 配置文件模板，支持不同环境和用途的配置需求。

## 配置文件结构

### 1. tsconfig.json（主配置文件）
- **用途**: 开发环境的主要配置文件
- **特点**: 包含完整的编译选项和路径别名配置
- **注意**: 默认注释了需要额外安装的类型定义

### 2. tsconfig.test.json（测试配置）
- **用途**: 专门用于测试环境
- **继承**: 基于主配置文件
- **包含**: Jest 和测试相关的类型定义

### 3. tsconfig.build.json（构建配置）
- **用途**: 生产环境构建
- **优化**: 移除注释、生成声明文件
- **性能**: 优化构建速度和输出质量

## 类型定义配置说明

### 需要安装的类型包

在使用模板文件时，根据项目需要安装以下类型定义包：

```bash
# Node.js 类型定义（服务端项目必需）
npm install --save-dev @types/node

# Jest 测试类型定义
npm install --save-dev @types/jest

# Testing Library Jest DOM 扩展
npm install --save-dev @testing-library/jest-dom

# Vite 构建工具（前端项目）
npm install --save-dev vite
```

### 启用类型定义

安装相应包后，在 `tsconfig.json` 中取消注释对应的类型定义：

```json
{
  "compilerOptions": {
    "types": [
      "node",                    // 启用 Node.js 类型（需要 @types/node）
      "jest",                   // 启用 Jest 类型（需要 @types/jest）
      "@testing-library/jest-dom", // 启用测试库扩展
      "vite/client"             // Vite 项目类型（需要 vite 包）
    ]
  }
}
```

## 路径别名配置

模板文件包含了完整的路径别名配置，支持：

- `@/*` - 指向 `src` 目录
- `@components/*` - 组件目录
- `@pages/*` - 页面目录
- `@utils/*` - 工具函数目录
- `@services/*` - 服务层目录
- `@hooks/*` - React Hooks 目录
- `@store/*` - 状态管理目录
- `@types/*` - 类型定义目录
- `@assets/*` - 静态资源目录
- `@styles/*` - 样式文件目录
- `@config/*` - 配置文件目录
- `@constants/*` - 常量定义目录
- `@contexts/*` - React Context 目录
- `@layouts/*` - 布局组件目录
- `@middleware/*` - 中间件目录
- `@api/*` - API 相关目录
- `@lib/*` - 第三方库封装目录
- `@test/*` - 测试相关目录

## 使用建议

### 1. 项目初始化
1. 复制 `tsconfig.json` 到项目根目录
2. 根据项目类型安装必要的类型定义包
3. 取消注释需要的类型定义
4. 根据项目结构调整路径别名

### 2. 测试环境配置
1. 复制 `tsconfig.test.json` 到项目根目录
2. 确保安装了 Jest 相关类型定义
3. 在 `package.json` 中添加测试脚本：
   ```json
   {
     "scripts": {
       "type-check:test": "tsc --project tsconfig.test.json --noEmit"
     }
   }
   ```

### 3. 生产构建配置
1. 复制 `tsconfig.build.json` 到项目根目录
2. 在 `package.json` 中添加构建脚本：
   ```json
   {
     "scripts": {
       "build:types": "tsc --project tsconfig.build.json"
     }
   }
   ```

## 常见问题解决

### 1. 找不到类型定义文件
**错误**: `找不到"node"的类型定义文件`

**解决方案**:
```bash
npm install --save-dev @types/node
```

### 2. 路径别名无法解析
**问题**: IDE 无法识别路径别名

**解决方案**:
1. 确保 `baseUrl` 设置为 `"."`
2. 检查 `paths` 配置是否正确
3. 重启 IDE 或 TypeScript 服务

### 3. 测试文件类型错误
**问题**: 测试文件中 Jest 方法报类型错误

**解决方案**:
1. 安装 `@types/jest`
2. 在 `tsconfig.test.json` 中启用 Jest 类型
3. 确保测试文件被正确包含

## 版本兼容性

- **TypeScript**: 5.0+
- **Node.js**: 18+
- **Jest**: 29+
- **Vite**: 4+

## 更新日志

### v1.0.3 (2024-12-19)
- **新增**: 创建完整的测试依赖类型声明文件 `types/test-dependencies.d.ts`
- **配置**: 更新 `tsconfig.json` 添加测试库类型支持（Jest、Supertest、MongoDB Memory Server、Mongoose、Express）
- **优化**: 清理测试示例文件中的临时类型声明，使用统一的类型声明文件
- **完善**: 提供完整的测试环境类型支持，解决所有模块导入问题

### v1.0.2 (2024-12-19)
- **修复**: 修复 Jest 测试文件中 `@jest/globals` 模块导入问题
- **配置**: 在 `jest.config.ts` 中启用 `injectGlobals: true` 配置
- **示例**: 创建 `jest-import-solutions.ts` 文件，提供 Jest 导入问题解决方案
- **文档**: 提供多种 Jest 函数使用方式的最佳实践

### v1.0.1 (2024-12-20)
- 修复 rootDir 配置冲突问题
- 移除 include 中的 `*.js` 和 `*.jsx` 匹配，避免包含根目录配置文件
- 在 exclude 中明确排除常见配置文件（eslintrc.js, babel.config.js 等）
- 确保 TypeScript 只处理 src 目录下的源文件

### v1.0.0 (2024-12-20)
- 初始版本
- 完整的 TypeScript 配置模板
- 详细的配置说明和使用指南