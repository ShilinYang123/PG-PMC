#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证和迁移工具
负责验证配置完整性，迁移分散的配置文件到统一配置管理中心
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import asdict
from datetime import datetime

from .config_manager import ConfigManager, get_config_manager
from .environment import get_current_environment
from .path_manager import PathManager


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or get_config_manager()
        self.path_manager = PathManager()
        self.validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
    
    def validate_all(self) -> Dict[str, Any]:
        """执行完整的配置验证"""
        self.validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        # 验证配置文件存在性
        self._validate_config_file_exists()
        
        # 验证配置结构
        self._validate_config_structure()
        
        # 验证路径配置
        self._validate_paths()
        
        # 验证数据库配置
        self._validate_database_config()
        
        # 验证服务器配置
        self._validate_server_config()
        
        # 验证安全配置
        self._validate_security_config()
        
        # 验证日志配置
        self._validate_logging_config()
        
        # 检查分散的配置文件
        self._check_scattered_configs()
        
        # 设置总体验证状态
        self.validation_results['valid'] = len(self.validation_results['errors']) == 0
        
        return self.validation_results
    
    def _validate_config_file_exists(self):
        """验证配置文件是否存在"""
        if not self.config_manager.config_file.exists():
            self._add_error(f"配置文件不存在: {self.config_manager.config_file}")
    
    def _validate_config_structure(self):
        """验证配置结构"""
        required_sections = ['project', 'database', 'server', 'security', 'logging', 'paths']
        config_data = self.config_manager.get_config()
        
        for section in required_sections:
            if section not in config_data:
                self._add_error(f"缺少必需的配置段: {section}")
    
    def _validate_paths(self):
        """验证路径配置"""
        paths_config = self.config_manager.get_config('paths')
        
        # 检查必需的路径
        required_paths = ['root', 'docs_dir', 'logs_dir', 'tools_dir', 'project_dir']
        for path_key in required_paths:
            if path_key not in paths_config:
                self._add_error(f"缺少必需的路径配置: {path_key}")
                continue
            
            path_value = paths_config[path_key]
            if not Path(path_value).exists():
                self._add_warning(f"路径不存在: {path_key} = {path_value}")
    
    def _validate_database_config(self):
        """验证数据库配置"""
        db_config = self.config_manager.database
        
        # 检查必需的数据库配置
        if not db_config.host:
            self._add_error("数据库主机地址未配置")
        
        if not db_config.username:
            self._add_error("数据库用户名未配置")
        
        if not db_config.database:
            self._add_error("数据库名称未配置")
        
        # 检查端口范围
        if not (1 <= db_config.port <= 65535):
            self._add_error(f"数据库端口无效: {db_config.port}")
    
    def _validate_server_config(self):
        """验证服务器配置"""
        server_config = self.config_manager.server
        
        # 检查端口范围
        if not (1 <= server_config.port <= 65535):
            self._add_error(f"服务器端口无效: {server_config.port}")
        
        if not (1 <= server_config.frontend_port <= 65535):
            self._add_error(f"前端端口无效: {server_config.frontend_port}")
        
        # 检查端口冲突
        if server_config.port == server_config.frontend_port:
            self._add_warning("后端和前端使用相同端口，可能导致冲突")
    
    def _validate_security_config(self):
        """验证安全配置"""
        security_config = self.config_manager.security
        
        # 检查密钥安全性
        if security_config.secret_key == "your-secret-key-change-in-production":
            self._add_warning("使用默认密钥，生产环境请更改")
        
        if len(security_config.secret_key) < 32:
            self._add_warning("密钥长度过短，建议至少32个字符")
        
        # 检查token过期时间
        if security_config.access_token_expire_minutes <= 0:
            self._add_error("访问令牌过期时间必须大于0")
    
    def _validate_logging_config(self):
        """验证日志配置"""
        logging_config = self.config_manager.logging
        
        # 检查日志级别
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if logging_config.level.upper() not in valid_levels:
            self._add_error(f"无效的日志级别: {logging_config.level}")
        
        # 检查日志目录
        log_dir = Path(logging_config.file_path).parent
        if not log_dir.exists():
            self._add_suggestion(f"创建日志目录: {log_dir}")
    
    def _check_scattered_configs(self):
        """检查分散的配置文件"""
        project_root = Path(self.config_manager.project_root)
        
        # 检查常见的配置文件
        config_files = [
            '.env',
            '.env.local',
            '.env.development',
            '.env.production',
            'config.ini',
            'settings.ini',
            'app.config'
        ]
        
        found_configs = []
        for config_file in config_files:
            config_path = project_root / config_file
            if config_path.exists():
                found_configs.append(str(config_path))
        
        if found_configs:
            self._add_suggestion(f"发现分散的配置文件，建议迁移到统一配置管理: {', '.join(found_configs)}")
    
    def _add_error(self, message: str):
        """添加错误信息"""
        self.validation_results['errors'].append(message)
    
    def _add_warning(self, message: str):
        """添加警告信息"""
        self.validation_results['warnings'].append(message)
    
    def _add_suggestion(self, message: str):
        """添加建议信息"""
        self.validation_results['suggestions'].append(message)


class ConfigMigrator:
    """配置迁移器"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or get_config_manager()
        self.project_root = Path(self.config_manager.project_root)
    
    def migrate_alembic_config(self) -> bool:
        """迁移alembic配置，使其使用统一配置管理中心的数据库配置"""
        try:
            alembic_ini_path = self.project_root / 'project/backend/alembic.ini'
            if not alembic_ini_path.exists():
                print(f"alembic.ini文件不存在: {alembic_ini_path}")
                return False
            
            # 读取现有配置
            with open(alembic_ini_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换数据库URL配置
            db_url = self.config_manager.database.url
            
            # 查找并替换sqlalchemy.url行
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('sqlalchemy.url'):
                    lines[i] = f'sqlalchemy.url = {db_url}'
                    break
            
            # 写回文件
            with open(alembic_ini_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            print(f"已更新alembic.ini配置，使用数据库URL: {db_url}")
            return True
            
        except Exception as e:
            print(f"迁移alembic配置失败: {e}")
            return False
    
    def create_env_file(self, env_file_path: Optional[str] = None) -> bool:
        """创建.env文件"""
        try:
            if env_file_path is None:
                env_file_path = self.project_root / '.env'
            else:
                env_file_path = Path(env_file_path)
            
            env_vars = self.config_manager.get_env_vars()
            
            with open(env_file_path, 'w', encoding='utf-8') as f:
                f.write(f"# 环境变量配置文件\n")
                f.write(f"# 生成时间: {datetime.now().isoformat()}\n")
                f.write(f"# 由统一配置管理中心自动生成\n\n")
                
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            
            print(f"已创建.env文件: {env_file_path}")
            return True
            
        except Exception as e:
            print(f"创建.env文件失败: {e}")
            return False
    
    def export_frontend_config(self, output_path: Optional[str] = None) -> bool:
        """导出前端配置文件"""
        try:
            if output_path is None:
                output_path = self.project_root / 'project/frontend/src/config/config.json'
            else:
                output_path = Path(output_path)
            
            # 确保目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            frontend_config = self.config_manager.export_frontend_config()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(frontend_config, f, indent=2, ensure_ascii=False)
            
            print(f"已导出前端配置: {output_path}")
            return True
            
        except Exception as e:
            print(f"导出前端配置失败: {e}")
            return False
    
    def export_backend_config(self, output_path: Optional[str] = None) -> bool:
        """导出后端配置文件"""
        try:
            if output_path is None:
                output_path = self.project_root / 'project/backend/app/core/settings.py'
            else:
                output_path = Path(output_path)
            
            # 确保目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            backend_config = self.config_manager.export_backend_config()
            
            # 生成Python配置文件
            config_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端配置文件
由统一配置管理中心自动生成
生成时间: {datetime.now().isoformat()}
"""

from typing import List
from pydantic import BaseSettings


class Settings(BaseSettings):
    """应用设置"""
    
    # 项目信息
    PROJECT_NAME: str = "{backend_config['PROJECT_NAME']}"
    VERSION: str = "{backend_config['VERSION']}"
    API_V1_STR: str = "{backend_config['API_V1_STR']}"
    
    # 服务器配置
    SERVER_HOST: str = "{backend_config['SERVER_HOST']}"
    SERVER_PORT: int = {backend_config['SERVER_PORT']}
    
    # 数据库配置
    DATABASE_URL: str = "{backend_config['DATABASE_URL']}"
    
    # 安全配置
    SECRET_KEY: str = "{backend_config['SECRET_KEY']}"
    ALGORITHM: str = "{backend_config['ALGORITHM']}"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = {backend_config['ACCESS_TOKEN_EXPIRE_MINUTES']}
    
    # CORS配置
    CORS_ORIGINS: List[str] = {backend_config['CORS_ORIGINS']}
    
    # 文件上传配置
    UPLOAD_DIR: str = "{backend_config['UPLOAD_DIR']}"
    MAX_FILE_SIZE: int = {backend_config['MAX_FILE_SIZE']}
    
    # 日志配置
    LOG_LEVEL: str = "{backend_config['LOG_LEVEL']}"
    
    # Redis配置
    REDIS_URL: str = "{backend_config['REDIS_URL']}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
'''
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            print(f"已导出后端配置: {output_path}")
            return True
            
        except Exception as e:
            print(f"导出后端配置失败: {e}")
            return False


def validate_config() -> Dict[str, Any]:
    """验证配置"""
    validator = ConfigValidator()
    return validator.validate_all()


def migrate_configs() -> bool:
    """迁移所有配置"""
    migrator = ConfigMigrator()
    
    success = True
    
    # 迁移alembic配置
    if not migrator.migrate_alembic_config():
        success = False
    
    # 创建.env文件
    if not migrator.create_env_file():
        success = False
    
    # 导出前端配置
    if not migrator.export_frontend_config():
        success = False
    
    # 导出后端配置
    if not migrator.export_backend_config():
        success = False
    
    return success


if __name__ == '__main__':
    print("=== 配置验证和迁移工具 ===")
    
    # 验证配置
    print("\n1. 验证配置...")
    validation_result = validate_config()
    
    print(f"配置有效性: {validation_result['valid']}")
    
    if validation_result['errors']:
        print("\n错误:")
        for error in validation_result['errors']:
            print(f"  ❌ {error}")
    
    if validation_result['warnings']:
        print("\n警告:")
        for warning in validation_result['warnings']:
            print(f"  ⚠️  {warning}")
    
    if validation_result['suggestions']:
        print("\n建议:")
        for suggestion in validation_result['suggestions']:
            print(f"  💡 {suggestion}")
    
    # 迁移配置
    print("\n2. 迁移配置...")
    if migrate_configs():
        print("✅ 配置迁移完成")
    else:
        print("❌ 配置迁移失败")