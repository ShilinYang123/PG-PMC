# PMC全流程管理系统 - Makefile
# 使用说明: make <target>

.PHONY: help build up down restart logs clean dev-up dev-down dev-logs test lint format

# 默认目标
help:
	@echo "PMC全流程管理系统 - 可用命令:"
	@echo ""
	@echo "生产环境:"
	@echo "  build      - 构建生产环境镜像"
	@echo "  up         - 启动生产环境服务"
	@echo "  down       - 停止生产环境服务"
	@echo "  restart    - 重启生产环境服务"
	@echo "  logs       - 查看生产环境日志"
	@echo ""
	@echo "开发环境:"
	@echo "  dev-build  - 构建开发环境镜像"
	@echo "  dev-up     - 启动开发环境服务"
	@echo "  dev-down   - 停止开发环境服务"
	@echo "  dev-restart- 重启开发环境服务"
	@echo "  dev-logs   - 查看开发环境日志"
	@echo ""
	@echo "代码质量:"
	@echo "  test       - 运行测试"
	@echo "  lint       - 代码检查"
	@echo "  format     - 代码格式化"
	@echo ""
	@echo "工具:"
	@echo "  clean      - 清理Docker资源"
	@echo "  backup     - 备份数据库"
	@echo "  restore    - 恢复数据库"
	@echo "  shell-be   - 进入后端容器"
	@echo "  shell-fe   - 进入前端容器"
	@echo "  shell-db   - 进入数据库容器"

# 生产环境命令
build:
	@echo "🔨 构建生产环境镜像..."
	docker-compose build --no-cache

up:
	@echo "🚀 启动生产环境服务..."
	docker-compose up -d
	@echo "✅ 服务已启动，访问地址:"
	@echo "   前端: http://localhost:3000"
	@echo "   后端: http://localhost:8000"
	@echo "   文档: http://localhost:8000/docs"

down:
	@echo "🛑 停止生产环境服务..."
	docker-compose down

restart:
	@echo "🔄 重启生产环境服务..."
	docker-compose restart

logs:
	@echo "📋 查看生产环境日志..."
	docker-compose logs -f

# 开发环境命令
dev-build:
	@echo "🔨 构建开发环境镜像..."
	docker-compose -f docker-compose.dev.yml build --no-cache

dev-up:
	@echo "🚀 启动开发环境服务..."
	docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ 开发环境已启动，访问地址:"
	@echo "   前端: http://localhost:3001"
	@echo "   后端: http://localhost:8001"
	@echo "   文档: http://localhost:8001/docs"
	@echo "   数据库管理: http://localhost:5050"
	@echo "   Redis管理: http://localhost:8081"

dev-down:
	@echo "🛑 停止开发环境服务..."
	docker-compose -f docker-compose.dev.yml down

dev-restart:
	@echo "🔄 重启开发环境服务..."
	docker-compose -f docker-compose.dev.yml restart

dev-logs:
	@echo "📋 查看开发环境日志..."
	docker-compose -f docker-compose.dev.yml logs -f

# 代码质量命令
test:
	@echo "🧪 运行测试..."
	docker exec pmc_backend_dev pytest -v --cov=app tests/

lint:
	@echo "🔍 代码检查..."
	docker exec pmc_backend_dev flake8 app/
	docker exec pmc_backend_dev mypy app/

format:
	@echo "🎨 代码格式化..."
	docker exec pmc_backend_dev black app/
	docker exec pmc_backend_dev isort app/

# 工具命令
clean:
	@echo "🧹 清理Docker资源..."
	docker-compose down -v --rmi all
	docker system prune -f

backup:
	@echo "💾 备份数据库..."
	docker exec pmc_postgres pg_dump -U pmc_user pmc_db > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore:
	@echo "📥 恢复数据库..."
	@read -p "请输入备份文件路径: " backup_file; \
	docker exec -i pmc_postgres psql -U pmc_user -d pmc_db < $$backup_file

shell-be:
	@echo "🐚 进入后端容器..."
	docker exec -it pmc_backend bash

shell-fe:
	@echo "🐚 进入前端容器..."
	docker exec -it pmc_frontend sh

shell-db:
	@echo "🐚 进入数据库容器..."
	docker exec -it pmc_postgres psql -U pmc_user -d pmc_db

# 开发环境容器命令
dev-shell-be:
	@echo "🐚 进入开发后端容器..."
	docker exec -it pmc_backend_dev bash

dev-shell-fe:
	@echo "🐚 进入开发前端容器..."
	docker exec -it pmc_frontend_dev sh

dev-shell-db:
	@echo "🐚 进入开发数据库容器..."
	docker exec -it pmc_postgres_dev psql -U pmc_user -d pmc_db_dev

# 监控命令
status:
	@echo "📊 服务状态..."
	docker-compose ps

dev-status:
	@echo "📊 开发环境服务状态..."
	docker-compose -f docker-compose.dev.yml ps

# 快速启动命令
quick-start: build up
	@echo "⚡ 快速启动完成！"

dev-quick-start: dev-build dev-up
	@echo "⚡ 开发环境快速启动完成！"