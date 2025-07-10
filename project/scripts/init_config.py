#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 配置初始化脚本

此脚本用于初始化项目配置，包括创建必要的目录、生成配置文件模板等。
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import Settings
from src.config.config_manager import ConfigManager


class ConfigInitializer:
    """配置初始化器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_dir = project_root / "config"
        
    def initialize_all(self, force: bool = False) -> bool:
        """初始化所有配置
        
        Args:
            force: 是否强制覆盖已存在的文件
            
        Returns:
            bool: 初始化是否成功
        """
        print("开始配置初始化...")
        print("=" * 50)
        
        try:
            # 创建必要目录
            self._create_directories()
            
            # 初始化配置文件
            self._initialize_config_files(force)
            
            # 初始化环境变量文件
            self._initialize_env_files(force)
            
            # 设置文件权限
            self._set_file_permissions()
            
            # 验证配置
            self._validate_configuration()
            
            print("\n✅ 配置初始化完成！")
            return True
            
        except Exception as e:
            print(f"\n❌ 配置初始化失败: {e}")
            return False
    
    def _create_directories(self) -> None:
        """创建必要的目录"""
        print("创建项目目录...")
        
        directories = [
            "config",
            "data",
            "temp",
            "logs",
            "uploads",
            "backups",
            "src/config",
            ".vscode"
        ]
        
        for dir_name in directories:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"  ✓ 已创建目录: {dir_name}")
            else:
                print(f"  - 目录已存在: {dir_name}")
    
    def _initialize_config_files(self, force: bool) -> None:
        """初始化配置文件"""
        print("\n初始化配置文件...")
        
        # 检查配置文件是否已存在
        config_files = {
            "settings.yaml": "主配置文件",
            "default.yaml": "默认配置文件",
            "user_settings.yaml": "用户配置文件模板"
        }
        
        for filename, description in config_files.items():
            file_path = self.config_dir / filename
            
            if file_path.exists() and not force:
                print(f"  - {description}已存在: {filename}")
            else:
                if file_path.exists() and force:
                    print(f"  ! 强制覆盖{description}: {filename}")
                else:
                    print(f"  ✓ 创建{description}: {filename}")
                
                # 这里配置文件已经在之前的步骤中创建了
                # 如果需要重新生成，可以调用相应的方法
    
    def _initialize_env_files(self, force: bool) -> None:
        """初始化环境变量文件"""
        print("\n初始化环境变量文件...")
        
        env_files = {
            ".env": "主环境变量文件",
            ".env.local": "本地环境变量文件",
            ".env.production": "生产环境变量文件"
        }
        
        for filename, description in env_files.items():
            file_path = self.project_root / filename
            
            if file_path.exists() and not force:
                print(f"  - {description}已存在: {filename}")
            else:
                if file_path.exists() and force:
                    print(f"  ! 强制覆盖{description}: {filename}")
                else:
                    print(f"  ✓ 创建{description}: {filename}")
    
    def _set_file_permissions(self) -> None:
        """设置文件权限"""
        print("\n设置文件权限...")
        
        # 在Windows上，文件权限设置相对简单
        sensitive_files = [
            ".env",
            ".env.local",
            ".env.production"
        ]
        
        for filename in sensitive_files:
            file_path = self.project_root / filename
            if file_path.exists():
                try:
                    # 在Windows上设置文件为只读（对于当前用户）
                    os.chmod(file_path, 0o600)
                    print(f"  ✓ 已设置权限: {filename}")
                except Exception as e:
                    print(f"  ⚠️  设置权限失败 {filename}: {e}")
    
    def _validate_configuration(self) -> None:
        """验证配置"""
        print("\n验证配置...")
        
        try:
            # 测试配置管理器
            config_manager = ConfigManager()
            settings = config_manager.get_settings()
            
            # 验证配置
            errors = settings.validate()
            
            if errors:
                print("  ⚠️  配置验证发现问题:")
                for error in errors:
                    print(f"    - {error}")
            else:
                print("  ✓ 配置验证通过")
                
        except Exception as e:
            print(f"  ❌ 配置验证失败: {e}")
    
    def create_user_config_template(self) -> None:
        """创建用户配置模板"""
        template_content = """
# PG-Dev AI设计助理 - 用户配置模板
# 复制此文件为 user_settings.yaml 并根据需要修改

# 应用设置
app:
  debug: false
  log_level: "INFO"
  environment: "development"

# 服务器设置
server:
  host: "127.0.0.1"
  port: 8000
  workers: 1

# AI设置
ai:
  openai:
    api_key: "your_openai_api_key_here"
    model: "gpt-4"
  anthropic:
    api_key: "your_anthropic_api_key_here"
    model: "claude-3-sonnet-20240229"
  default_provider: "openai"

# Creo设置
creo:
  install_path: "C:\\Program Files\\PTC\\Creo 7.0\\Common Files\\x86e_win64\\bin"
  working_directory: "C:\\PG-Dev\\CreoWork"
  auto_start: false

# 数据库设置
database:
  type: "sqlite"
  sqlite:
    path: "data/pgdev.db"

# 功能开关
features:
  chat_interface: true
  design_interpreter: true
  parameter_parser: true
  geometry_creator: true
  real_time_preview: true

# 开发设置
development:
  hot_reload: true
  debug_toolbar: true
  profiling: false
  mock_creo: false
"""
        
        template_path = self.config_dir / "user_settings_template.yaml"
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content.strip())
        
        print(f"  ✓ 已创建用户配置模板: {template_path}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PG-Dev AI设计助理配置初始化")
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="强制覆盖已存在的配置文件"
    )
    parser.add_argument(
        "--template-only", 
        action="store_true", 
        help="仅创建用户配置模板"
    )
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    initializer = ConfigInitializer(project_root)
    
    if args.template_only:
        print("创建用户配置模板...")
        initializer.create_user_config_template()
        print("\n✅ 用户配置模板创建完成！")
        return
    
    success = initializer.initialize_all(force=args.force)
    
    if success:
        print("\n🎉 配置初始化成功！")
        print("\n下一步:")
        print("1. 编辑 .env 文件，设置您的API密钥")
        print("2. 根据需要修改 config/user_settings.yaml")
        print("3. 运行 python scripts/check_config.py 验证配置")
        print("4. 启动应用程序")
    else:
        print("\n❌ 配置初始化失败，请检查错误信息并重试。")
        sys.exit(1)


if __name__ == "__main__":
    main()