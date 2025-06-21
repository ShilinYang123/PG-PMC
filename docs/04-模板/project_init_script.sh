#!/bin/bash

# 3AI工作室项目初始化脚本 (Shell版本)
# 功能：快速创建标准项目结构
# 使用方法：./项目初始化脚本.sh <项目名称> <项目类型>
# 项目类型：frontend, backend, fullstack, api

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 显示帮助信息
show_help() {
    echo "3AI工作室项目初始化脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 <项目名称> <项目类型> [选项]"
    echo ""
    echo "项目类型:"
    echo "  frontend   - 前端项目 (React/Vue)"
    echo "  backend    - 后端项目 (Python/Node.js)"
    echo "  fullstack  - 全栈项目"
    echo "  api        - API服务项目"
    echo ""
    echo "选项:"
    echo "  --skip-install  跳过依赖安装"
    echo "  --skip-git      跳过Git初始化"
    echo "  --help          显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 my-project frontend"
    echo "  $0 my-api api --skip-install"
}

# 检查参数
if [ $# -lt 2 ]; then
    print_error "参数不足"
    show_help
    exit 1
fi

# 解析参数
PROJECT_NAME="$1"
PROJECT_TYPE="$2"
SKIP_INSTALL=false
SKIP_GIT=false

# 解析选项
shift 2
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-install)
            SKIP_INSTALL=true
            shift
            ;;
        --skip-git)
            SKIP_GIT=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 验证项目类型
case $PROJECT_TYPE in
    frontend|backend|fullstack|api)
        ;;
    *)
        print_error "无效的项目类型: $PROJECT_TYPE"
        print_info "支持的类型: frontend, backend, fullstack, api"
        exit 1
        ;;
esac

# 检查项目目录是否已存在
if [ -d "$PROJECT_NAME" ]; then
    print_error "项目目录 '$PROJECT_NAME' 已存在"
    exit 1
fi

# 开始初始化
print_info "🚀 开始初始化项目: $PROJECT_NAME"
print_info "项目类型: $PROJECT_TYPE"
echo "$(printf '%.0s-' {1..50})"

# 创建项目目录
print_info "创建项目目录结构..."
mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

# 基础目录结构
BASE_DIRS=(
    "src"
    "tests"
    "docs"
    "config"
    "scripts"
    "logs"
)

# 根据项目类型添加特定目录
case $PROJECT_TYPE in
    frontend|fullstack)
        FRONTEND_DIRS=(
            "public"
            "src/components"
            "src/pages"
            "src/utils"
            "src/services"
            "src/styles"
            "src/assets"
        )
        BASE_DIRS+=("${FRONTEND_DIRS[@]}")
        ;;
esac

case $PROJECT_TYPE in
    backend|fullstack|api)
        BACKEND_DIRS=(
            "src/models"
            "src/controllers"
            "src/services"
            "src/middleware"
            "src/routes"
            "src/utils"
            "migrations"
        )
        BASE_DIRS+=("${BACKEND_DIRS[@]}")
        ;;
esac

# 创建目录
for dir in "${BASE_DIRS[@]}"; do
    mkdir -p "$dir"
    print_success "创建目录: $dir"
done

# 创建 .env.example 文件
print_info "创建配置文件..."
cat > .env.example << EOF
# $PROJECT_NAME 环境配置

# 应用配置
APP_NAME=$PROJECT_NAME
APP_ENV=development
APP_DEBUG=true
APP_PORT=3000

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/$PROJECT_NAME
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
EOF
print_success "创建文件: .env.example"

# 创建 .gitignore 文件
cat > .gitignore << 'EOF'
# 依赖包
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
EOF
print_success "创建文件: .gitignore"

# 创建 README.md 文件
cat > README.md << EOF
# $PROJECT_NAME

$PROJECT_NAME 项目描述

## 项目信息

- **项目类型**: $PROJECT_TYPE
- **创建时间**: $(date +%Y-%m-%d)
- **版本**: 1.0.0

## 快速开始

### 环境要求

- Node.js >= 16.0.0
- Python >= 3.8
- Docker (可选)

### 安装依赖

\`\`\`bash
# 安装 Node.js 依赖
npm install

# 安装 Python 依赖
pip install -r requirements.txt
\`\`\`

### 配置环境

\`\`\`bash
# 复制环境配置文件
cp .env.example .env

# 编辑环境配置
vim .env
\`\`\`

### 启动开发服务器

\`\`\`bash
# 启动前端开发服务器
npm run dev

# 启动后端开发服务器
python src/main.py
\`\`\`

### 使用Docker

\`\`\`bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
\`\`\`

## 项目结构

\`\`\`
$PROJECT_NAME/
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
\`\`\`

## 开发指南

### 代码规范

- 遵循 ESLint 和 Prettier 配置
- 使用 TypeScript 进行类型检查
- 编写单元测试和集成测试

### 提交规范

\`\`\`bash
# 功能开发
git commit -m "feat: 添加用户登录功能"

# 问题修复
git commit -m "fix: 修复登录验证问题"

# 文档更新
git commit -m "docs: 更新API文档"
\`\`\`

### 测试

\`\`\`bash
# 运行单元测试
npm test

# 运行集成测试
npm run test:integration

# 生成测试覆盖率报告
npm run test:coverage
\`\`\`

## 部署

### 生产环境构建

\`\`\`bash
# 构建前端
npm run build

# 构建Docker镜像
docker build -t $PROJECT_NAME .
\`\`\`

### 环境配置

- 开发环境: \`.env.development\`
- 测试环境: \`.env.test\`
- 生产环境: \`.env.production\`

## 贡献指南

1. Fork 项目
2. 创建功能分支 (\`git checkout -b feature/AmazingFeature\`)
3. 提交更改 (\`git commit -m 'Add some AmazingFeature'\`)
4. 推送到分支 (\`git push origin feature/AmazingFeature\`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

- 项目维护者: 3AI工作室
- 邮箱: contact@3ai.studio
- 项目地址: [GitHub](https://github.com/3ai-studio/$PROJECT_NAME)
EOF
print_success "创建文件: README.md"

# 根据项目类型创建特定文件
case $PROJECT_TYPE in
    frontend|fullstack)
        # 创建 package.json
        cat > package.json << EOF
{
  "name": "$PROJECT_NAME",
  "version": "1.0.0",
  "description": "$PROJECT_NAME 项目",
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
    "start": "node dist/index.js"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.4.0",
    "react-router-dom": "^6.14.0"
  },
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
    "webpack-dev-server": "^4.15.0"
  },
  "keywords": ["$PROJECT_TYPE", "3ai-studio"],
  "author": "3AI工作室",
  "license": "MIT"
}
EOF
        print_success "创建文件: package.json"
        ;;
esac

case $PROJECT_TYPE in
    backend|fullstack|api)
        # 创建 requirements.txt
        cat > requirements.txt << 'EOF'
# Web框架
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
EOF
        print_success "创建文件: requirements.txt"
        ;;
esac

# 创建 Dockerfile
print_info "创建Docker配置文件..."
if [[ "$PROJECT_TYPE" == "frontend" || "$PROJECT_TYPE" == "fullstack" ]]; then
    cat > Dockerfile << 'EOF'
# 多阶段构建 - Node.js 前端
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
EOF
else
    cat > Dockerfile << 'EOF'
# Python 后端
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
EOF
fi
print_success "创建文件: Dockerfile"

# 创建 docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'

services:
  app:
    build: .
    container_name: ${PROJECT_NAME}-app
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://postgres:password@db:5432/$PROJECT_NAME
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - .:/app
      - /app/node_modules
    depends_on:
      - db
      - redis
    networks:
      - ${PROJECT_NAME}-network

  db:
    image: postgres:15-alpine
    container_name: ${PROJECT_NAME}-db
    environment:
      - POSTGRES_DB=$PROJECT_NAME
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - ${PROJECT_NAME}-network

  redis:
    image: redis:7-alpine
    container_name: ${PROJECT_NAME}-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - ${PROJECT_NAME}-network

  nginx:
    image: nginx:alpine
    container_name: ${PROJECT_NAME}-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    networks:
      - ${PROJECT_NAME}-network

volumes:
  postgres_data:
  redis_data:

networks:
  ${PROJECT_NAME}-network:
    driver: bridge
EOF
print_success "创建文件: docker-compose.yml"

# 创建 .dockerignore
cat > .dockerignore << 'EOF'
# 依赖包
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
EOF
print_success "创建文件: .dockerignore"

# 安装依赖
if [ "$SKIP_INSTALL" = false ]; then
    print_info "安装依赖包..."
    
    case $PROJECT_TYPE in
        frontend|fullstack)
            if command -v npm &> /dev/null; then
                print_info "安装 Node.js 依赖..."
                npm install
                print_success "Node.js 依赖安装完成"
            else
                print_warning "npm 未找到，跳过 Node.js 依赖安装"
            fi
            ;;
    esac
    
    case $PROJECT_TYPE in
        backend|fullstack|api)
            if command -v pip &> /dev/null; then
                print_info "安装 Python 依赖..."
                pip install -r requirements.txt
                print_success "Python 依赖安装完成"
            else
                print_warning "pip 未找到，跳过 Python 依赖安装"
            fi
            ;;
    esac
else
    print_info "跳过依赖安装"
fi

# 初始化Git仓库
if [ "$SKIP_GIT" = false ]; then
    if command -v git &> /dev/null; then
        print_info "初始化Git仓库..."
        git init
        git add .
        git commit -m "Initial commit"
        print_success "Git仓库初始化完成"
    else
        print_warning "git 未找到，跳过Git初始化"
    fi
else
    print_info "跳过Git初始化"
fi

# 完成提示
echo "$(printf '%.0s-' {1..50})"
print_success "项目 $PROJECT_NAME 初始化完成!"
echo ""
print_info "下一步操作:"
echo "1. cd $PROJECT_NAME"
echo "2. 复制 .env.example 为 .env 并配置环境变量"
echo "3. 根据需要修改配置文件"
echo "4. 开始开发!"
echo ""
print_info "常用命令:"
case $PROJECT_TYPE in
    frontend|fullstack)
        echo "  npm run dev      # 启动前端开发服务器"
        echo "  npm run build    # 构建生产版本"
        echo "  npm test         # 运行测试"
        ;;
esac
case $PROJECT_TYPE in
    backend|fullstack|api)
        echo "  python src/main.py  # 启动后端服务器"
        echo "  pytest              # 运行测试"
        ;;
esac
echo "  docker-compose up   # 使用Docker启动服务"
echo ""
print_success "祝您开发愉快! 🎉"