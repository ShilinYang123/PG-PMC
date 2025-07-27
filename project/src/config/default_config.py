#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
默认配置提供器
提供所有配置项的默认值，确保系统在缺少配置时能正常运行
"""

import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class DefaultConfigProvider:
    """默认配置提供器"""
    
    def __init__(self, project_root: str = None):
        self.project_root = project_root or str(Path(__file__).parent.parent.parent.parent)
        self.project_name = "PG-PMC"
        self.version = "1.0.0"
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取完整的默认配置"""
        return {
            'project': self.get_project_defaults(),
            'database': self.get_database_defaults(),
            'server': self.get_server_defaults(),
            'environment': self.get_environment_defaults(),
            'paths': self.get_paths_defaults(),
            'logging': self.get_logging_defaults(),
            'security': self.get_security_defaults(),
            'redis': self.get_redis_defaults(),
            'files': self.get_files_defaults(),
            'performance': self.get_performance_defaults(),
            'quality': self.get_quality_defaults(),
            'compliance': self.get_compliance_defaults(),
            'backup': self.get_backup_defaults(),
            'git': self.get_git_defaults(),
            'mcp_tools': self.get_mcp_tools_defaults(),
            'migration': self.get_migration_defaults(),
            'structure_check': self.get_structure_check_defaults(),
            'validation': self.get_validation_defaults()
        }
    
    def get_project_defaults(self) -> Dict[str, Any]:
        """项目默认配置"""
        return {
            'name': self.project_name,
            'version': self.version,
            'description': '项目管理中心 - 统一配置管理系统',
            'author': 'PG-PMC Team',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    
    def get_database_defaults(self) -> Dict[str, Any]:
        """数据库默认配置"""
        return {
            'development': {
                'type': 'sqlite',
                'host': 'localhost',
                'port': 5432,
                'username': 'postgres',
                'password': 'password',
                'database': 'pmc_dev',
                'url': 'sqlite:///./pmc_dev.db'
            },
            'testing': {
                'type': 'sqlite',
                'host': 'localhost',
                'port': 5432,
                'username': 'postgres',
                'password': 'password',
                'database': 'pmc_test',
                'url': 'sqlite:///./pmc_test.db'
            },
            'production': {
                'type': 'postgresql',
                'host': 'localhost',
                'port': 5432,
                'username': 'postgres',
                'password': 'change-in-production',
                'database': 'pmc_prod',
                'url': 'postgresql://postgres:change-in-production@localhost:5432/pmc_prod'
            }
        }
    
    def get_server_defaults(self) -> Dict[str, Any]:
        """服务器默认配置"""
        return {
            'host': '0.0.0.0',
            'port': 8000,
            'frontend_host': '0.0.0.0',
            'frontend_port': 3000,
            'debug': True,
            'reload': True,
            'workers': 1,
            'cors_origins': [
                'http://localhost:3000',
                'http://127.0.0.1:3000',
                'http://localhost:8080',
                'http://127.0.0.1:8080'
            ]
        }
    
    def get_environment_defaults(self) -> Dict[str, Any]:
        """环境默认配置"""
        return {
            'current': 'development',
            'cache': {
                'enabled': True,
                'ttl': 3600,
                'max_size': 1000
            },
            'external_services': {
                'timeout': 30,
                'retry_count': 3,
                'retry_delay': 1
            },
            'email': {
                'smtp_server': 'localhost',
                'smtp_port': 587,
                'use_tls': True,
                'username': '',
                'password': '',
                'from_email': 'noreply@pmc.local'
            },
            'monitoring': {
                'enabled': True,
                'interval': 60,
                'metrics_retention': 7
            },
            'network': {
                'timeout': 30,
                'max_connections': 100,
                'keep_alive': True
            },
            'production': {
                'debug': False,
                'testing': False,
                'log_level': 'INFO'
            },
            'rate_limiting': {
                'enabled': True,
                'requests_per_minute': 60,
                'burst_size': 10
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'password': None,
                'url': 'redis://localhost:6379/0'
            },
            'security': {
                'https_only': False,
                'secure_cookies': False,
                'csrf_protection': True
            },
            'storage': {
                'type': 'local',
                'path': './storage',
                'max_size': '100MB'
            },
            'testing': {
                'parallel': True,
                'coverage': True,
                'mock_external': True
            }
        }
    
    def get_paths_defaults(self) -> Dict[str, Any]:
        """路径默认配置"""
        return {
            'root': self.project_root,
            'project_dir': os.path.join(self.project_root, 'project'),
            'docs_dir': os.path.join(self.project_root, 'docs'),
            'tools_dir': os.path.join(self.project_root, 'tools'),
            'logs_dir': os.path.join(self.project_root, 'logs'),
            'backup_dir': os.path.join(self.project_root, 'bak'),
            'temp_dir': os.path.join(self.project_root, 'temp'),
            'upload_dir': os.path.join(self.project_root, 'uploads'),
            'static_dir': os.path.join(self.project_root, 'static'),
            'config_file': os.path.join(self.project_root, 'docs', '03-管理', 'project_config.yaml')
        }
    
    def get_logging_defaults(self) -> Dict[str, Any]:
        """日志默认配置"""
        return {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'date_format': '%Y-%m-%d %H:%M:%S',
            'file_path': os.path.join(self.project_root, 'logs', 'app.log'),
            'max_file_size': '10MB',
            'backup_count': 5,
            'rotation': 'daily',
            'compression': True,
            'console_output': True,
            'file_output': True,
            'json_format': False
        }
    
    def get_security_defaults(self) -> Dict[str, Any]:
        """安全默认配置"""
        return {
            'secret_key': 'your-secret-key-change-in-production',
            'algorithm': 'HS256',
            'access_token_expire_minutes': 30,
            'refresh_token_expire_days': 7,
            'password_min_length': 8,
            'password_require_uppercase': True,
            'password_require_lowercase': True,
            'password_require_numbers': True,
            'password_require_symbols': False,
            'max_login_attempts': 5,
            'lockout_duration_minutes': 15,
            'session_timeout_minutes': 60,
            'csrf_token_expire_minutes': 60,
            'allowed_hosts': ['localhost', '127.0.0.1'],
            'cors_allow_credentials': True,
            'cors_max_age': 86400
        }
    
    def get_redis_defaults(self) -> Dict[str, Any]:
        """Redis默认配置"""
        return {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': None,
            'url': 'redis://localhost:6379/0',
            'connection_pool_size': 10,
            'socket_timeout': 5,
            'socket_connect_timeout': 5,
            'retry_on_timeout': True,
            'health_check_interval': 30
        }
    
    def get_files_defaults(self) -> Dict[str, Any]:
        """文件默认配置"""
        return {
            'allowed_extensions': [
                '.py', '.js', '.ts', '.jsx', '.tsx', '.vue', '.html', '.css', '.scss', '.sass',
                '.json', '.yaml', '.yml', '.xml', '.md', '.txt', '.csv', '.sql',
                '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.zip', '.tar', '.gz', '.rar'
            ],
            'max_file_size': 10485760,  # 10MB
            'upload_path': './uploads',
            'temp_path': './temp',
            'encoding': 'utf-8',
            'exclude_patterns': [
                '*.pyc', '*.pyo', '*.pyd', '__pycache__',
                '.git', '.svn', '.hg',
                'node_modules', '.venv', 'venv',
                '.DS_Store', 'Thumbs.db',
                '*.log', '*.tmp'
            ],
            'backup_enabled': True,
            'backup_retention_days': 30,
            'compression_enabled': True,
            'virus_scan_enabled': False
        }
    
    def get_performance_defaults(self) -> Dict[str, Any]:
        """性能默认配置"""
        return {
            'cache_size': 1000,
            'connection_pool': {
                'min_size': 5,
                'max_size': 20,
                'timeout': 30
            },
            'request_timeout': 30,
            'cpu_limit': 80,
            'memory_limit': '1GB',
            'disk_space_limit': '10GB',
            'concurrent_requests': 100,
            'worker_processes': 1,
            'thread_pool_size': 10
        }
    
    def get_quality_defaults(self) -> Dict[str, Any]:
        """代码质量默认配置"""
        return {
            'max_line_length': 88,
            'max_function_length': 50,
            'max_file_length': 1000,
            'require_docstrings': True,
            'require_type_hints': True,
            'complexity_threshold': 10,
            'test_coverage_threshold': 80,
            'code_style': 'black',
            'linting_enabled': True,
            'formatting_enabled': True
        }
    
    def get_compliance_defaults(self) -> Dict[str, Any]:
        """合规性默认配置"""
        return {
            'enabled': True,
            'check_interval': 3600,  # 1小时
            'monitoring': {
                'enabled': True,
                'real_time': True,
                'alert_threshold': 5
            },
            'violation_handling': {
                'auto_fix': False,
                'notify_admin': True,
                'log_violations': True,
                'quarantine_files': False
            },
            'audit': {
                'enabled': True,
                'retention_days': 90,
                'detailed_logging': True
            },
            'dependency_scan': True,
            'vulnerability_scan': True,
            'license_check': True
        }
    
    def get_backup_defaults(self) -> Dict[str, Any]:
        """备份默认配置"""
        return {
            'enabled': True,
            'interval': 'daily',
            'retention_days': 30,
            'compression': True,
            'encryption': False,
            'remote_backup': False,
            'backup_path': os.path.join(self.project_root, 'bak'),
            'exclude_patterns': [
                '*.log', '*.tmp', '__pycache__',
                '.git', 'node_modules', '.venv'
            ]
        }
    
    def get_git_defaults(self) -> Dict[str, Any]:
        """Git默认配置"""
        return {
            'auto_commit': False,
            'auto_push': False,
            'default_branch': 'main',
            'commit_message_prefix': '[AUTO]',
            'ignore_patterns': [
                '*.log', '*.tmp', '__pycache__',
                '.env', '.env.local',
                'node_modules', '.venv'
            ]
        }
    
    def get_mcp_tools_defaults(self) -> Dict[str, Any]:
        """MCP工具默认配置"""
        return {
            'github': {
                'enabled': True,
                'token': '',
                'default_org': '',
                'auto_sync': False
            },
            'memory': {
                'enabled': True,
                'max_entities': 10000,
                'auto_cleanup': True
            },
            'task_manager': {
                'enabled': True,
                'auto_approve': False,
                'notification': True
            }
        }
    
    def get_migration_defaults(self) -> Dict[str, Any]:
        """迁移默认配置"""
        return {
            'auto_migrate': False,
            'backup_before_migrate': True,
            'validate_after_migrate': True,
            'cleanup_old_files': False,
            'update_mode': 'safe',
            'reset_files': [],
            'cleanup_directories': []
        }
    
    def get_structure_check_defaults(self) -> Dict[str, Any]:
        """结构检查默认配置"""
        return {
            'enabled': True,
            'max_depth': 10,
            'exclude_dirs': ['.git', '__pycache__', 'node_modules', '.venv'],
            'exclude_files': ['*.pyc', '*.pyo', '*.log', '*.tmp'],
            'allowed_hidden': ['.gitignore', '.env.example', '.editorconfig'],
            'naming_rules': {
                'files': '^[a-z0-9_.-]+$',
                'directories': '^[a-z0-9_-]+$'
            },
            'report_format': 'json',
            'report_dir': './reports',
            'auto_fix': False
        }
    
    def get_validation_defaults(self) -> Dict[str, Any]:
        """验证默认配置"""
        return {
            'strict_mode': False,
            'require_docs': True,
            'check_empty_files': True,
            'validate_naming': True,
            'check_permissions': True,
            'validate_encoding': True,
            'check_line_endings': True,
            'max_file_size': '10MB',
            'allowed_encodings': ['utf-8', 'ascii']
        }
    
    def merge_with_defaults(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """将用户配置与默认配置合并"""
        default_config = self.get_default_config()
        return self._deep_merge(default_config, user_config)
    
    def _deep_merge(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并两个字典"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_minimal_config(self) -> Dict[str, Any]:
        """获取最小化配置（仅包含必需项）"""
        return {
            'project': {
                'name': self.project_name,
                'version': self.version
            },
            'database': {
                'development': {
                    'url': 'sqlite:///./pmc_dev.db'
                }
            },
            'server': {
                'host': '0.0.0.0',
                'port': 8000
            },
            'paths': {
                'root': self.project_root
            },
            'logging': {
                'level': 'INFO',
                'file_path': os.path.join(self.project_root, 'logs', 'app.log')
            },
            'security': {
                'secret_key': 'your-secret-key-change-in-production',
                'algorithm': 'HS256'
            }
        }


# 全局默认配置提供器实例
_default_provider = None


def get_default_provider(project_root: str = None) -> DefaultConfigProvider:
    """获取默认配置提供器实例"""
    global _default_provider
    if _default_provider is None:
        _default_provider = DefaultConfigProvider(project_root)
    return _default_provider


def get_default_config(project_root: str = None) -> Dict[str, Any]:
    """获取默认配置"""
    provider = get_default_provider(project_root)
    return provider.get_default_config()


def get_minimal_config(project_root: str = None) -> Dict[str, Any]:
    """获取最小化配置"""
    provider = get_default_provider(project_root)
    return provider.get_minimal_config()


if __name__ == '__main__':
    # 测试默认配置
    provider = DefaultConfigProvider()
    config = provider.get_default_config()
    
    print("=== 默认配置预览 ===")
    for section, values in config.items():
        print(f"\n[{section}]")
        if isinstance(values, dict):
            for key, value in values.items():
                if isinstance(value, dict):
                    print(f"  {key}: {{...}}")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"  {values}")