#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证器
负责验证配置的完整性、有效性和安全性
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from urllib.parse import urlparse


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def clear_messages(self):
        """清空消息"""
        self.errors.clear()
        self.warnings.clear()
        self.info.clear()
    
    def validate_all(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证所有配置"""
        self.clear_messages()
        
        # 验证项目基本信息
        self._validate_project_info(config_data.get('project', {}))
        
        # 验证数据库配置
        self._validate_database_config(config_data.get('database', {}))
        
        # 验证服务器配置
        self._validate_server_config(config_data.get('server', {}))
        
        # 验证安全配置
        self._validate_security_config(config_data.get('security', {}))
        
        # 验证路径配置
        self._validate_paths_config(config_data.get('paths', {}))
        
        # 验证日志配置
        self._validate_logging_config(config_data.get('logging', {}))
        
        # 验证文件配置
        self._validate_file_config(config_data.get('file', {}))
        
        # 验证Redis配置
        self._validate_redis_config(config_data.get('redis', {}))
        
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors.copy(),
            'warnings': self.warnings.copy(),
            'info': self.info.copy()
        }
    
    def _validate_project_info(self, project_config: Dict[str, Any]):
        """验证项目基本信息"""
        required_fields = ['name', 'version', 'description']
        
        for field in required_fields:
            if not project_config.get(field):
                self.errors.append(f"项目配置缺少必需字段: {field}")
        
        # 验证项目名称格式
        name = project_config.get('name', '')
        if name and not re.match(r'^[A-Za-z0-9_-]+$', name):
            self.warnings.append("项目名称建议只包含字母、数字、下划线和连字符")
        
        # 验证版本号格式
        version = project_config.get('version', '')
        if version and not re.match(r'^\d+\.\d+\.\d+', version):
            self.warnings.append("版本号建议使用语义化版本格式 (如: 1.0.0)")
    
    def _validate_database_config(self, db_config: Dict[str, Any]):
        """验证数据库配置"""
        required_fields = ['host', 'port', 'username', 'database']
        
        for field in required_fields:
            if not db_config.get(field):
                self.errors.append(f"数据库配置缺少必需字段: {field}")
        
        # 验证端口号
        port = db_config.get('port')
        if port and (not isinstance(port, int) or port < 1 or port > 65535):
            self.errors.append("数据库端口号必须是1-65535之间的整数")
        
        # 验证主机名
        host = db_config.get('host', '')
        if host and not self._is_valid_hostname(host):
            self.warnings.append(f"数据库主机名格式可能不正确: {host}")
        
        # 检查密码安全性
        password = db_config.get('password', '')
        if password == 'password' or len(password) < 8:
            self.warnings.append("数据库密码过于简单，建议使用更强的密码")
    
    def _validate_server_config(self, server_config: Dict[str, Any]):
        """验证服务器配置"""
        # 验证端口号
        for port_field in ['port', 'frontend_port']:
            port = server_config.get(port_field)
            if port and (not isinstance(port, int) or port < 1 or port > 65535):
                self.errors.append(f"服务器{port_field}必须是1-65535之间的整数")
        
        # 验证主机名
        host = server_config.get('host', '')
        if host and not self._is_valid_hostname(host):
            self.warnings.append(f"服务器主机名格式可能不正确: {host}")
        
        # 验证CORS配置
        cors_origins = server_config.get('cors_origins', [])
        if isinstance(cors_origins, list):
            for origin in cors_origins:
                if not self._is_valid_url(origin):
                    self.warnings.append(f"CORS源格式可能不正确: {origin}")
    
    def _validate_security_config(self, security_config: Dict[str, Any]):
        """验证安全配置"""
        # 检查密钥强度
        secret_key = security_config.get('secret_key', '')
        if not secret_key:
            self.errors.append("安全配置缺少secret_key")
        elif secret_key in ['your-secret-key-change-in-production', 'secret']:
            self.errors.append("使用默认密钥，生产环境必须更改")
        elif len(secret_key) < 32:
            self.warnings.append("密钥长度建议至少32个字符")
        
        # 检查加密密钥
        encryption_key = security_config.get('encryption_key', '')
        if encryption_key == 'your-32-character-encryption-key':
            self.warnings.append("使用默认加密密钥，建议更改")
        
        # 检查token过期时间
        expire_minutes = security_config.get('access_token_expire_minutes')
        if expire_minutes and expire_minutes > 1440:  # 24小时
            self.warnings.append("访问令牌过期时间过长，建议不超过24小时")
    
    def _validate_paths_config(self, paths_config: Dict[str, Any]):
        """验证路径配置"""
        for path_name, path_value in paths_config.items():
            if not path_value:
                self.warnings.append(f"路径配置为空: {path_name}")
                continue
            
            path_obj = Path(path_value)
            
            # 检查路径是否存在
            if not path_obj.exists():
                if path_name in ['root', 'project_dir']:
                    self.errors.append(f"关键路径不存在: {path_name} = {path_value}")
                else:
                    self.warnings.append(f"路径不存在: {path_name} = {path_value}")
            
            # 检查路径权限
            if path_obj.exists():
                if not os.access(path_value, os.R_OK):
                    self.errors.append(f"路径无读取权限: {path_name} = {path_value}")
                if path_name in ['logs_dir', 'backup_dir'] and not os.access(path_value, os.W_OK):
                    self.errors.append(f"路径无写入权限: {path_name} = {path_value}")
    
    def _validate_logging_config(self, logging_config: Dict[str, Any]):
        """验证日志配置"""
        # 验证日志级别
        level = logging_config.get('level', '')
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if level and level.upper() not in valid_levels:
            self.errors.append(f"无效的日志级别: {level}，有效值: {', '.join(valid_levels)}")
        
        # 验证日志文件路径
        file_path = logging_config.get('file_path', '')
        if file_path:
            log_dir = Path(file_path).parent
            if not log_dir.exists():
                self.warnings.append(f"日志目录不存在: {log_dir}")
        
        # 验证备份数量
        backup_count = logging_config.get('backup_count')
        if backup_count and (not isinstance(backup_count, int) or backup_count < 0):
            self.errors.append("日志备份数量必须是非负整数")
    
    def _validate_file_config(self, file_config: Dict[str, Any]):
        """验证文件配置"""
        # 验证上传目录
        upload_dir = file_config.get('upload_dir', '')
        if upload_dir:
            upload_path = Path(upload_dir)
            if upload_path.exists() and not os.access(upload_dir, os.W_OK):
                self.errors.append(f"上传目录无写入权限: {upload_dir}")
        
        # 验证文件大小限制
        max_size = file_config.get('max_file_size')
        if max_size and (not isinstance(max_size, int) or max_size <= 0):
            self.errors.append("最大文件大小必须是正整数")
        elif max_size and max_size > 100 * 1024 * 1024:  # 100MB
            self.warnings.append("最大文件大小超过100MB，可能影响性能")
        
        # 验证允许的文件扩展名
        extensions = file_config.get('allowed_extensions', [])
        if isinstance(extensions, list):
            for ext in extensions:
                if not ext.startswith('.'):
                    self.warnings.append(f"文件扩展名应以点开头: {ext}")
    
    def _validate_redis_config(self, redis_config: Dict[str, Any]):
        """验证Redis配置"""
        # 验证端口号
        port = redis_config.get('port')
        if port and (not isinstance(port, int) or port < 1 or port > 65535):
            self.errors.append("Redis端口号必须是1-65535之间的整数")
        
        # 验证主机名
        host = redis_config.get('host', '')
        if host and not self._is_valid_hostname(host):
            self.warnings.append(f"Redis主机名格式可能不正确: {host}")
        
        # 验证数据库编号
        db = redis_config.get('db')
        if db is not None and (not isinstance(db, int) or db < 0 or db > 15):
            self.errors.append("Redis数据库编号必须是0-15之间的整数")
    
    def _is_valid_hostname(self, hostname: str) -> bool:
        """验证主机名格式"""
        if hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
            return True
        
        # 简单的IP地址验证
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        if re.match(ip_pattern, hostname):
            parts = hostname.split('.')
            return all(0 <= int(part) <= 255 for part in parts)
        
        # 简单的域名验证
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(domain_pattern, hostname))
    
    def _is_valid_url(self, url: str) -> bool:
        """验证URL格式"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False


class DefaultConfigProvider:
    """默认配置提供器"""
    
    @staticmethod
    def get_development_defaults() -> Dict[str, Any]:
        """获取开发环境默认配置"""
        return {
            'environment': {
                'name': 'development',
                'debug': True,
                'testing': False
            },
            'database': {
                'host': 'localhost',
                'port': 5432,
                'username': 'postgres',
                'password': 'password',
                'database': 'pmc_dev_db'
            },
            'server': {
                'host': 'localhost',
                'port': 8000,
                'frontend_port': 3000,
                'debug': True
            },
            'logging': {
                'level': 'DEBUG',
                'file_path': 'logs/pmc_dev.log'
            }
        }
    
    @staticmethod
    def get_production_defaults() -> Dict[str, Any]:
        """获取生产环境默认配置"""
        return {
            'environment': {
                'name': 'production',
                'debug': False,
                'testing': False
            },
            'database': {
                'host': 'localhost',
                'port': 5432,
                'username': 'postgres',
                'password': 'CHANGE_ME_IN_PRODUCTION',
                'database': 'pmc_db'
            },
            'server': {
                'host': '0.0.0.0',
                'port': 8000,
                'frontend_port': 80,
                'debug': False
            },
            'security': {
                'secret_key': 'CHANGE_ME_IN_PRODUCTION',
                'access_token_expire_minutes': 15
            },
            'logging': {
                'level': 'INFO',
                'file_path': '/var/log/pmc/pmc.log'
            }
        }
    
    @staticmethod
    def get_testing_defaults() -> Dict[str, Any]:
        """获取测试环境默认配置"""
        return {
            'environment': {
                'name': 'testing',
                'debug': True,
                'testing': True
            },
            'database': {
                'host': 'localhost',
                'port': 5432,
                'username': 'postgres',
                'password': 'password',
                'database': 'pmc_test_db'
            },
            'server': {
                'host': 'localhost',
                'port': 8001,
                'frontend_port': 3001,
                'debug': True
            },
            'logging': {
                'level': 'DEBUG',
                'file_path': 'logs/pmc_test.log'
            }
        }
    
    def get_default_config(self, env) -> Dict[str, Any]:
        """根据环境获取默认配置"""
        # 处理Environment枚举或字符串
        if hasattr(env, 'value'):
            env_name = env.value.lower()
        elif hasattr(env, 'name'):
            env_name = env.name.lower()
        else:
            env_name = str(env).lower()
        
        if env_name == 'production':
            return self.get_production_defaults()
        elif env_name == 'testing':
            return self.get_testing_defaults()
        else:
            return self.get_development_defaults()


def validate_config(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """验证配置数据"""
    validator = ConfigValidator()
    return validator.validate_all(config_data)


def get_environment_defaults(env_name: str) -> Dict[str, Any]:
    """根据环境名称获取默认配置"""
    env_name = env_name.lower()
    
    if env_name == 'production':
        return DefaultConfigProvider.get_production_defaults()
    elif env_name == 'testing':
        return DefaultConfigProvider.get_testing_defaults()
    else:
        return DefaultConfigProvider.get_development_defaults()


if __name__ == '__main__':
    # 测试配置验证
    test_config = {
        'project': {
            'name': 'PG-PMC',
            'version': '1.0.0',
            'description': 'Test project'
        },
        'database': {
            'host': 'localhost',
            'port': 5432,
            'username': 'postgres',
            'password': 'password',
            'database': 'test_db'
        },
        'security': {
            'secret_key': 'your-secret-key-change-in-production'
        }
    }
    
    result = validate_config(test_config)
    print(f"配置验证结果: {result}")