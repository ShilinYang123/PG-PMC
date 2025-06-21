#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3AI工作室项目初始化脚本模板

功能：
- 创建标准项目目录结构
- 初始化配置文件
- 安装依赖包
- 设置开发环境

使用方法：
python 项目初始化脚本.py --project-name <项目名称> --project-type <项目类型>

项目类型：
- frontend: 前端项目 (React/Vue)
- backend: 后端项目 (Python/Node.js)
- fullstack: 全栈项目
- api: API服务项目
"""

import os
import sys
import json
import yaml
import argparse
import subprocess
from pathlib import Path
from datetime import datetime


class ProjectInitializer:
    """项目初始化器"""

    def __init__(self, project_name, project_type, base_path=None):
        self.project_name = project_name
        self.project_type = project_type
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.project_path = self.base_path / project_name

    def create_directory_structure(self):
        """创建项目目录结构"""
        print(f"创建项目目录结构: {self.project_path}")

        # 基础目录结构
        base_dirs = [
            'src',
            'tests',
            'docs',
            'config',
            'scripts',
            'logs',
        ]

        # 根据项目类型添加特定目录
        if self.project_type in ['frontend', 'fullstack']:
            base_dirs.extend([
                'public',
                'src/components',
                'src/pages',
                'src/utils',
                'src/services',
                'src/styles',
                'src/assets',
            ])

        if self.project_type in ['backend', 'fullstack', 'api']:
            base_dirs.extend([
                'src/models',
                'src/controllers',
                'src/services',
                'src/middleware',
                'src/routes',
                'src/utils',
                'migrations',
            ])

        # 创建目录
        for dir_name in base_dirs:
            dir_path = self.project_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ 创建目录: {dir_name}")

    def create_config_files(self):
        """创建配置文件"""
        print("创建配置文件...")

        # 创建 .env.example
        env_content = self._get_env_template()
        self._write_file('.env.example', env_content)

        # 创建 project_config.yaml
        config_content = self._get_project_config_template()
        self._write_file('project_config.yaml', config_content)

        # 创建 .gitignore
        gitignore_content = self._get_gitignore_template()
        self._write_file('.gitignore', gitignore_content)

        # 创建 README.md
        readme_content = self._get_readme_template()
        self._write_file('README.md', readme_content)

    def create_package_files(self):
        """创建包管理文件"""
        print("创建包管理文件...")

        if self.project_type in ['frontend', 'fullstack']:
            # 创建 package.json
            package_json = self._get_package_json_template()
            self._write_file(
                'package.json',
                json.dumps(
                    package_json,
                    indent=2,
                    ensure_ascii=False))

        if self.project_type in ['backend', 'fullstack', 'api']:
            # 创建 requirements.txt
            requirements = self._get_requirements_template()
            self._write_file('requirements.txt', requirements)

            # 创建 setup.py
            setup_py = self._get_setup_py_template()
            self._write_file('setup.py', setup_py)

    def create_docker_files(self):
        """创建Docker配置文件"""
        print("创建Docker配置文件...")

        # 创建 Dockerfile
        dockerfile_content = self._get_dockerfile_template()
        self._write_file('Dockerfile', dockerfile_content)

        # 创建 docker-compose.yml
        docker_compose_content = self._get_docker_compose_template()
        self._write_file('docker-compose.yml', docker_compose_content)

        # 创建 .dockerignore
        dockerignore_content = self._get_dockerignore_template()
        self._write_file('.dockerignore', dockerignore_content)

    def install_dependencies(self):
        """安装依赖包"""
        print("安装依赖包...")

        try:
            if self.project_type in ['frontend', 'fullstack']:
                print("  安装 Node.js 依赖...")
                subprocess.run(['npm', 'install'],
                               cwd=self.project_path, check=True)

            if self.project_type in ['backend', 'fullstack', 'api']:
                print("  安装 Python 依赖...")
                subprocess.run(['pip', 'install', '-r', 'requirements.txt'],
                               cwd=self.project_path, check=True)

        except subprocess.CalledProcessError as e:
            print(f"  ⚠️ 依赖安装失败: {e}")
            print("  请手动安装依赖包")

    def initialize_git(self):
        """初始化Git仓库"""
        print("初始化Git仓库...")

        try:
            subprocess.run(['git', 'init'], cwd=self.project_path, check=True)
            subprocess.run(['git', 'add', '.'],
                           cwd=self.project_path, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'],
                           cwd=self.project_path, check=True)
            print("  ✓ Git仓库初始化完成")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️ Git初始化失败: {e}")

    def run(self):
        """执行项目初始化"""
        print(f"\n🚀 开始初始化项目: {self.project_name}")
        print(f"项目类型: {self.project_type}")
        print(f"项目路径: {self.project_path}")
        print("-" * 50)

        try:
            self.create_directory_structure()
            self.create_config_files()
            self.create_package_files()
            self.create_docker_files()
            self.install_dependencies()
            self.initialize_git()

            print("-" * 50)
            print(f"✅ 项目 {self.project_name} 初始化完成!")
            print("\n下一步操作:")
            print(f"1. cd {self.project_name}")
            print("2. 复制 .env.example 为 .env 并配置环境变量")
            print("3. 根据需要修改配置文件")
            print("4. 开始开发!")

        except Exception as e:
            print(f"❌ 项目初始化失败: {e}")
            sys.exit(1)

    def _write_file(self, filename, content):
        """写入文件"""
        file_path = self.project_path / filename
        file_path.write_text(content, encoding='utf-8')
        print(f"  ✓ 创建文件: {filename}")

    def _get_env_template(self):
        """获取环境变量模板"""
        return """# {self.project_name} 环境配置

# 应用配置
APP_NAME={self.project_name}
APP_ENV=development
APP_DEBUG=true
APP_PORT=3000

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/{self.project_name}
REDIS_URL=redis://localhost:6379/0

# API配置
API_BASE_URL=http://localhost:3000/api
API_VERSION=v1

# 认证配置
JWT_SECRET=your-jwt-secret-key
JWT_EXPIRES_IN=7d

# 第三方服务
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@gmail.com
# SMTP_PASS=your-password

# 日志配置
LOG_LEVEL=info
LOG_FILE=logs/app.log
"""

    def _get_project_config_template(self):
        """获取项目配置模板"""
        config = {
            'project': {
                'name': self.project_name,
                'type': self.project_type,
                'version': '1.0.0',
                'description': f'{self.project_name} 项目',
                'created_at': datetime.now().isoformat(),
            },
            'development': {
                'port': 3000,
                'host': 'localhost',
                'auto_reload': True,
                'debug': True,
            },
            'database': {
                'default_url': f'postgresql://user:password@localhost:5432/{self.project_name}',
                'pool_size': 10,
                'timeout': 30,
            },
            'build': {
                'output_dir': 'dist',
                'source_map': True,
                'minify': False,
            },
            'testing': {
                'coverage_threshold': 80,
                'test_timeout': 10000,
            }
        }
        return yaml.dump(config, default_flow_style=False, allow_unicode=True)

    def _get_gitignore_template(self):
        """获取.gitignore模板"""
        return """# 依赖包
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 环境配置
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# 日志文件
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# 运行时文件
*.pid
*.seed
*.pid.lock

# 编辑器
.vscode/
.idea/
*.swp
*.swo
*~

# 操作系统
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# 构建输出
dist/
build/
.next/
.nuxt/

# 测试覆盖率
coverage/
.nyc_output/

# 缓存
.cache/
.parcel-cache/

# Docker
.dockerignore
"""

    def _get_readme_template(self):
        """获取README模板"""
        return """# {self.project_name}

{self.project_name} 项目描述

## 项目信息

- **项目类型**: {self.project_type}
- **创建时间**: {datetime.now().strftime('%Y-%m-%d')}
- **版本**: 1.0.0

## 快速开始

### 环境要求

- Node.js >= 16.0.0
- Python >= 3.8
- Docker (可选)

### 安装依赖

```bash
# 安装 Node.js 依赖
npm install

# 安装 Python 依赖
pip install -r requirements.txt
```

### 配置环境

```bash
# 复制环境配置文件
cp .env.example .env

# 编辑环境配置
vim .env
```

### 启动开发服务器

```bash
# 启动前端开发服务器
npm run dev

# 启动后端开发服务器
python src/main.py
```

### 使用Docker

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

## 项目结构

```
{self.project_name}/
├── src/                 # 源代码
├── tests/              # 测试文件
├── docs/               # 文档
├── config/             # 配置文件
├── scripts/            # 脚本文件
├── logs/               # 日志文件
├── package.json        # Node.js 依赖
├── requirements.txt    # Python 依赖
├── Dockerfile         # Docker 配置
├── docker-compose.yml # Docker Compose 配置
└── README.md          # 项目说明
```

## 开发指南

### 代码规范

- 遵循 ESLint 和 Prettier 配置
- 使用 TypeScript 进行类型检查
- 编写单元测试和集成测试

### 提交规范

```bash
# 功能开发
git commit -m "feat: 添加用户登录功能"

# 问题修复
git commit -m "fix: 修复登录验证问题"

# 文档更新
git commit -m "docs: 更新API文档"
```

### 测试

```bash
# 运行单元测试
npm test

# 运行集成测试
npm run test:integration

# 生成测试覆盖率报告
npm run test:coverage
```

## 部署

### 生产环境构建

```bash
# 构建前端
npm run build

# 构建Docker镜像
docker build -t {self.project_name} .
```

### 环境配置

- 开发环境: `.env.development`
- 测试环境: `.env.test`
- 生产环境: `.env.production`

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

- 项目维护者: 3AI工作室
- 邮箱: contact@3ai.studio
- 项目地址: [GitHub](https://github.com/3ai-studio/{self.project_name})
"""

    def _get_package_json_template(self):
        """获取package.json模板"""
        return {
            "name": self.project_name,
            "version": "1.0.0",
            "description": f"{
                self.project_name} 项目",
            "main": "src/index.js",
            "scripts": {
                "dev": "webpack serve --mode development",
                "build": "webpack --mode production",
                "test": "jest",
                "test:watch": "jest --watch",
                "test:coverage": "jest --coverage",
                "lint": "eslint src --ext .js,.jsx,.ts,.tsx",
                "lint:fix": "eslint src --ext .js,.jsx,.ts,.tsx --fix",
                "format": "prettier --write src/**/*.{js,jsx,ts,tsx,json,css,md}",
                "start": "node dist/index.js"},
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "axios": "^1.4.0",
                "react-router-dom": "^6.14.0"},
            "devDependencies": {
                "@types/react": "^18.2.0",
                "@types/react-dom": "^18.2.0",
                "@typescript-eslint/eslint-plugin": "^5.60.0",
                "@typescript-eslint/parser": "^5.60.0",
                "eslint": "^8.43.0",
                "eslint-plugin-react": "^7.32.0",
                "jest": "^29.5.0",
                "prettier": "^2.8.0",
                "typescript": "^5.1.0",
                "webpack": "^5.88.0",
                "webpack-cli": "^5.1.0",
                "webpack-dev-server": "^4.15.0"},
            "keywords": [
                self.project_type,
                "3ai-studio"],
            "author": "3AI工作室",
            "license": "MIT"}

    def _get_requirements_template(self):
        """获取requirements.txt模板"""
        return """# Web框架
fastapi==0.100.0
uvicorn[standard]==0.22.0
starlette==0.27.0

# 数据库
sqlalchemy==2.0.17
psycopg2-binary==2.9.6
alembic==1.11.1

# 认证和安全
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# 配置管理
python-dotenv==1.0.0
pydantic==2.0.2
pydantic-settings==2.0.1

# HTTP客户端
httpx==0.24.1
requests==2.31.0

# 日志和监控
loguru==0.7.0
prometheus-client==0.17.0

# 测试
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-cov==4.1.0
httpx==0.24.1

# 代码质量
flake8==6.0.0
black==23.3.0
isort==5.12.0
mypy==1.4.1

# 工具
click==8.1.3
rich==13.4.2
pyyaml==6.0
"""

    def _get_setup_py_template(self):
        """获取setup.py模板"""
        return """from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="{self.project_name}",
    version="1.0.0",
    author="3AI工作室",
    author_email="contact@3ai.studio",
    description="{self.project_name} 项目",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/3ai-studio/{self.project_name}",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={{
        "console_scripts": [
            "{self.project_name}=src.main:main",
        ],
    }},
)
"""

    def _get_dockerfile_template(self):
        """获取Dockerfile模板"""
        if self.project_type in ['frontend', 'fullstack']:
            return """# 多阶段构建 - Node.js 前端
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段 - Nginx
FROM nginx:alpine AS production

# 复制构建结果
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY config/nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
"""
        else:
            return """# Python 后端
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动应用
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

    def _get_docker_compose_template(self):
        """获取docker-compose.yml模板"""
        return """version: '3.8'

services:
  app:
    build: .
    container_name: {self.project_name}-app
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://postgres:password@db:5432/{self.project_name}
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - .:/app
      - /app/node_modules
    depends_on:
      - db
      - redis
    networks:
      - {self.project_name}-network

  db:
    image: postgres:15-alpine
    container_name: {self.project_name}-db
    environment:
      - POSTGRES_DB={self.project_name}
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - {self.project_name}-network

  redis:
    image: redis:7-alpine
    container_name: {self.project_name}-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - {self.project_name}-network

  nginx:
    image: nginx:alpine
    container_name: {self.project_name}-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    networks:
      - {self.project_name}-network

volumes:
  postgres_data:
  redis_data:

networks:
  {self.project_name}-network:
    driver: bridge
"""

    def _get_dockerignore_template(self):
        """获取.dockerignore模板"""
        return """# 依赖包
node_modules
__pycache__
*.pyc
*.pyo
*.pyd
.Python
build
develop-eggs
dist
downloads
eggs
.eggs
lib
lib64
parts
sdist
var
wheels
*.egg-info
.installed.cfg
*.egg

# 环境配置
.env
.env.local
.env.*.local

# 日志文件
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# 运行时文件
*.pid
*.seed
*.pid.lock

# 编辑器
.vscode
.idea
*.swp
*.swo
*~

# 操作系统
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Git
.git
.gitignore

# 测试和构建
coverage
.nyc_output
.cache
.parcel-cache

# 文档
README.md
*.md
docs

# Docker
Dockerfile
docker-compose*.yml
.dockerignore
"""


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='3AI工作室项目初始化脚本')
    parser.add_argument('--project-name', required=True, help='项目名称')
    parser.add_argument('--project-type',
                        choices=['frontend', 'backend', 'fullstack', 'api'],
                        required=True, help='项目类型')
    parser.add_argument('--base-path', help='项目基础路径 (默认为当前目录)')
    parser.add_argument('--skip-install', action='store_true', help='跳过依赖安装')
    parser.add_argument('--skip-git', action='store_true', help='跳过Git初始化')

    args = parser.parse_args()

    # 创建项目初始化器
    initializer = ProjectInitializer(
        project_name=args.project_name,
        project_type=args.project_type,
        base_path=args.base_path
    )

    # 执行初始化
    initializer.run()


if __name__ == '__main__':
    main()
