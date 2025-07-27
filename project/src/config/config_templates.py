#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置模板生成器
用于生成不同环境和场景的配置模板
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict

from .default_config import get_default_provider
from .path_manager import get_path_manager


@dataclass
class TemplateMetadata:
    """模板元数据"""
    name: str
    description: str
    version: str
    author: str
    created_at: str
    environment: str
    tags: List[str]
    requirements: List[str]


class ConfigTemplateGenerator:
    """配置模板生成器"""
    
    def __init__(self):
        self.default_provider = get_default_provider()
        self.path_manager = get_path_manager()
        self.templates_dir = Path('templates/config')
        self.templates_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_development_template(self) -> Dict[str, Any]:
        """生成开发环境配置模板"""
        config = self.default_provider.get_default_config()
        
        # 开发环境特定配置
        config['environment']['current'] = 'development'
        config['environment']['debug'] = True
        config['environment']['testing'] = True
        
        # 数据库配置
        config['database']['development']['host'] = 'localhost'
        config['database']['development']['port'] = 5432
        config['database']['development']['name'] = 'pmc_dev'
        config['database']['development']['user'] = 'dev_user'
        config['database']['development']['password'] = 'dev_password'
        
        # 服务器配置
        config['server']['host'] = '127.0.0.1'
        config['server']['port'] = 8000
        config['server']['debug'] = True
        config['server']['reload'] = True
        
        # 日志配置
        config['logging']['level'] = 'DEBUG'
        config['logging']['console'] = True
        config['logging']['file'] = True
        
        # Redis配置
        config['redis']['host'] = 'localhost'
        config['redis']['port'] = 6379
        config['redis']['db'] = 0
        
        # 安全配置（开发环境相对宽松）
        config['security']['secret_key'] = 'dev-secret-key-change-in-production'
        config['security']['cors_origins'] = ['http://localhost:3000', 'http://127.0.0.1:3000']
        config['security']['https_only'] = False
        
        return config
    
    def generate_testing_template(self) -> Dict[str, Any]:
        """生成测试环境配置模板"""
        config = self.default_provider.get_default_config()
        
        # 测试环境特定配置
        config['environment']['current'] = 'testing'
        config['environment']['debug'] = True
        config['environment']['testing'] = True
        
        # 数据库配置（使用内存数据库）
        config['database']['testing']['host'] = 'localhost'
        config['database']['testing']['port'] = 5432
        config['database']['testing']['name'] = 'pmc_test'
        config['database']['testing']['user'] = 'test_user'
        config['database']['testing']['password'] = 'test_password'
        
        # 服务器配置
        config['server']['host'] = '127.0.0.1'
        config['server']['port'] = 8001
        config['server']['debug'] = True
        
        # 日志配置
        config['logging']['level'] = 'INFO'
        config['logging']['console'] = True
        config['logging']['file'] = False
        
        # Redis配置
        config['redis']['host'] = 'localhost'
        config['redis']['port'] = 6379
        config['redis']['db'] = 1  # 使用不同的数据库
        
        # 安全配置
        config['security']['secret_key'] = 'test-secret-key'
        config['security']['cors_origins'] = ['http://localhost:3000']
        config['security']['https_only'] = False
        
        return config
    
    def generate_production_template(self) -> Dict[str, Any]:
        """生成生产环境配置模板"""
        config = self.default_provider.get_default_config()
        
        # 生产环境特定配置
        config['environment']['current'] = 'production'
        config['environment']['debug'] = False
        config['environment']['testing'] = False
        
        # 数据库配置（使用环境变量）
        config['database']['production']['host'] = '${DB_HOST}'
        config['database']['production']['port'] = '${DB_PORT:5432}'
        config['database']['production']['name'] = '${DB_NAME}'
        config['database']['production']['user'] = '${DB_USER}'
        config['database']['production']['password'] = '${DB_PASSWORD}'
        
        # 服务器配置
        config['server']['host'] = '0.0.0.0'
        config['server']['port'] = '${PORT:8000}'
        config['server']['debug'] = False
        config['server']['reload'] = False
        
        # 日志配置
        config['logging']['level'] = 'INFO'
        config['logging']['console'] = False
        config['logging']['file'] = True
        config['logging']['max_size'] = '100MB'
        config['logging']['backup_count'] = 10
        
        # Redis配置
        config['redis']['host'] = '${REDIS_HOST:localhost}'
        config['redis']['port'] = '${REDIS_PORT:6379}'
        config['redis']['password'] = '${REDIS_PASSWORD}'
        config['redis']['db'] = '${REDIS_DB:0}'
        
        # 安全配置
        config['security']['secret_key'] = '${SECRET_KEY}'
        config['security']['cors_origins'] = ['${FRONTEND_URL}']
        config['security']['https_only'] = True
        config['security']['secure_cookies'] = True
        
        return config
    
    def generate_docker_template(self) -> Dict[str, Any]:
        """生成Docker环境配置模板"""
        config = self.generate_production_template()
        
        # Docker特定配置
        config['database']['production']['host'] = 'postgres'
        config['redis']['host'] = 'redis'
        
        # 路径配置（容器内路径）
        config['paths']['project_root'] = '/app'
        config['paths']['logs'] = '/app/logs'
        config['paths']['uploads'] = '/app/uploads'
        config['paths']['temp'] = '/tmp'
        
        return config
    
    def generate_minimal_template(self) -> Dict[str, Any]:
        """生成最小化配置模板"""
        return {
            'project': {
                'name': 'PG-PMC',
                'version': '1.0.0'
            },
            'environment': {
                'current': 'development'
            },
            'database': {
                'development': {
                    'host': 'localhost',
                    'port': 5432,
                    'name': 'pmc_dev',
                    'user': 'dev_user',
                    'password': 'dev_password'
                }
            },
            'server': {
                'host': '127.0.0.1',
                'port': 8000
            },
            'logging': {
                'level': 'INFO'
            }
        }
    
    def generate_microservices_template(self) -> Dict[str, Any]:
        """生成微服务架构配置模板"""
        config = self.default_provider.get_default_config()
        
        # 微服务特定配置
        config['microservices'] = {
            'discovery': {
                'enabled': True,
                'service_name': 'pmc-service',
                'registry_url': '${REGISTRY_URL:http://localhost:8500}'
            },
            'load_balancer': {
                'enabled': True,
                'strategy': 'round_robin'
            },
            'circuit_breaker': {
                'enabled': True,
                'failure_threshold': 5,
                'timeout': 30
            },
            'tracing': {
                'enabled': True,
                'jaeger_endpoint': '${JAEGER_ENDPOINT}'
            }
        }
        
        # API网关配置
        config['api_gateway'] = {
            'enabled': True,
            'rate_limiting': {
                'enabled': True,
                'requests_per_minute': 1000
            },
            'authentication': {
                'jwt_secret': '${JWT_SECRET}',
                'token_expiry': 3600
            }
        }
        
        return config
    
    def generate_high_availability_template(self) -> Dict[str, Any]:
        """生成高可用配置模板"""
        config = self.generate_production_template()
        
        # 高可用特定配置
        config['high_availability'] = {
            'enabled': True,
            'cluster': {
                'nodes': [
                    '${NODE1_HOST}',
                    '${NODE2_HOST}',
                    '${NODE3_HOST}'
                ],
                'leader_election': True
            },
            'health_check': {
                'enabled': True,
                'interval': 30,
                'timeout': 10,
                'retries': 3
            },
            'failover': {
                'enabled': True,
                'auto_failback': True,
                'failback_delay': 300
            }
        }
        
        # 数据库集群配置
        config['database']['cluster'] = {
            'enabled': True,
            'master': '${DB_MASTER_HOST}',
            'slaves': [
                '${DB_SLAVE1_HOST}',
                '${DB_SLAVE2_HOST}'
            ],
            'read_preference': 'secondary_preferred'
        }
        
        # Redis集群配置
        config['redis']['cluster'] = {
            'enabled': True,
            'nodes': [
                '${REDIS_NODE1}',
                '${REDIS_NODE2}',
                '${REDIS_NODE3}'
            ]
        }
        
        return config
    
    def generate_env_template(self, environment: str = 'development') -> str:
        """生成.env文件模板"""
        env_vars = []
        
        # 基础环境变量
        env_vars.extend([
            f"# {environment.upper()} Environment Configuration",
            f"# Generated at {datetime.now().isoformat()}",
            "",
            "# Environment",
            f"ENVIRONMENT={environment}",
            f"DEBUG={'true' if environment == 'development' else 'false'}",
            "",
        ])
        
        if environment == 'production':
            env_vars.extend([
                "# Database",
                "DB_HOST=your-db-host",
                "DB_PORT=5432",
                "DB_NAME=your-db-name",
                "DB_USER=your-db-user",
                "DB_PASSWORD=your-db-password",
                "",
                "# Redis",
                "REDIS_HOST=your-redis-host",
                "REDIS_PORT=6379",
                "REDIS_PASSWORD=your-redis-password",
                "REDIS_DB=0",
                "",
                "# Security",
                "SECRET_KEY=your-secret-key-here",
                "JWT_SECRET=your-jwt-secret-here",
                "",
                "# Server",
                "PORT=8000",
                "FRONTEND_URL=https://your-frontend-domain.com",
                "",
                "# External Services",
                "SMTP_HOST=your-smtp-host",
                "SMTP_PORT=587",
                "SMTP_USER=your-smtp-user",
                "SMTP_PASSWORD=your-smtp-password",
                ""
            ])
        else:
            env_vars.extend([
                "# Database (Development)",
                "DB_HOST=localhost",
                "DB_PORT=5432",
                "DB_NAME=pmc_dev",
                "DB_USER=dev_user",
                "DB_PASSWORD=dev_password",
                "",
                "# Redis (Development)",
                "REDIS_HOST=localhost",
                "REDIS_PORT=6379",
                "REDIS_DB=0",
                "",
                "# Security (Development)",
                "SECRET_KEY=dev-secret-key-change-in-production",
                ""
            ])
        
        return "\n".join(env_vars)
    
    def generate_docker_compose_template(self) -> str:
        """生成docker-compose.yml模板"""
        return """
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DB_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    restart: unless-stopped

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=${DB_NAME:-pmc}
      - POSTGRES_USER=${DB_USER:-pmc_user}
      - POSTGRES_PASSWORD=${DB_PASSWORD:-pmc_password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD:-redis_password}
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  default:
    driver: bridge
"""
    
    def save_template(self, template_name: str, config: Dict[str, Any], 
                     metadata: Optional[TemplateMetadata] = None) -> Path:
        """保存配置模板"""
        template_file = self.templates_dir / f"{template_name}.yaml"
        
        # 添加元数据
        if metadata:
            config['_metadata'] = asdict(metadata)
        else:
            config['_metadata'] = {
                'name': template_name,
                'description': f'{template_name} configuration template',
                'version': '1.0.0',
                'author': 'PG-PMC Config Generator',
                'created_at': datetime.now().isoformat(),
                'environment': 'any',
                'tags': [],
                'requirements': []
            }
        
        with open(template_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        return template_file
    
    def load_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """加载配置模板"""
        template_file = self.templates_dir / f"{template_name}.yaml"
        
        if not template_file.exists():
            return None
        
        with open(template_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """列出所有可用模板"""
        templates = []
        
        for template_file in self.templates_dir.glob('*.yaml'):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    metadata = config.get('_metadata', {})
                    templates.append({
                        'name': template_file.stem,
                        'file': str(template_file),
                        'metadata': metadata
                    })
            except Exception as e:
                print(f"❌ 加载模板失败 {template_file}: {e}")
        
        return templates
    
    def generate_all_templates(self) -> Dict[str, Path]:
        """生成所有预定义模板"""
        templates = {
            'development': self.generate_development_template(),
            'testing': self.generate_testing_template(),
            'production': self.generate_production_template(),
            'docker': self.generate_docker_template(),
            'minimal': self.generate_minimal_template(),
            'microservices': self.generate_microservices_template(),
            'high_availability': self.generate_high_availability_template()
        }
        
        saved_files = {}
        
        for name, config in templates.items():
            metadata = TemplateMetadata(
                name=name,
                description=f'{name.title()} environment configuration template',
                version='1.0.0',
                author='PG-PMC Config Generator',
                created_at=datetime.now().isoformat(),
                environment=name,
                tags=[name, 'auto-generated'],
                requirements=[]
            )
            
            saved_files[name] = self.save_template(name, config, metadata)
        
        return saved_files
    
    def generate_env_files(self) -> Dict[str, Path]:
        """生成所有环境的.env文件模板"""
        env_files = {}
        
        for env in ['development', 'testing', 'production']:
            env_content = self.generate_env_template(env)
            env_file = self.templates_dir / f".env.{env}"
            
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            env_files[env] = env_file
        
        return env_files
    
    def generate_docker_files(self) -> Dict[str, Path]:
        """生成Docker相关文件模板"""
        docker_files = {}
        
        # docker-compose.yml
        compose_content = self.generate_docker_compose_template()
        compose_file = self.templates_dir / 'docker-compose.yml'
        
        with open(compose_file, 'w', encoding='utf-8') as f:
            f.write(compose_content)
        
        docker_files['docker-compose'] = compose_file
        
        return docker_files


# 全局模板生成器实例
_template_generator = None


def get_template_generator() -> ConfigTemplateGenerator:
    """获取全局模板生成器实例"""
    global _template_generator
    if _template_generator is None:
        _template_generator = ConfigTemplateGenerator()
    return _template_generator


def generate_template(template_type: str) -> Optional[Dict[str, Any]]:
    """生成指定类型的配置模板"""
    generator = get_template_generator()
    
    template_methods = {
        'development': generator.generate_development_template,
        'testing': generator.generate_testing_template,
        'production': generator.generate_production_template,
        'docker': generator.generate_docker_template,
        'minimal': generator.generate_minimal_template,
        'microservices': generator.generate_microservices_template,
        'high_availability': generator.generate_high_availability_template
    }
    
    method = template_methods.get(template_type)
    if method:
        return method()
    
    return None


if __name__ == '__main__':
    # 测试模板生成
    generator = ConfigTemplateGenerator()
    
    print("🔧 生成所有配置模板...")
    templates = generator.generate_all_templates()
    
    for name, file_path in templates.items():
        print(f"✅ {name}: {file_path}")
    
    print("\n🔧 生成环境文件模板...")
    env_files = generator.generate_env_files()
    
    for env, file_path in env_files.items():
        print(f"✅ .env.{env}: {file_path}")
    
    print("\n🔧 生成Docker文件模板...")
    docker_files = generator.generate_docker_files()
    
    for name, file_path in docker_files.items():
        print(f"✅ {name}: {file_path}")
    
    print("\n📋 可用模板列表:")
    available_templates = generator.list_templates()
    
    for template in available_templates:
        metadata = template['metadata']
        print(f"  • {template['name']}: {metadata.get('description', 'No description')}")