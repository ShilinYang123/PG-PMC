#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-PMC AI设计助理 - 配置完整性检查脚本

此脚本用于检查配置文件的完整性和正确性，确保所有必要的配置项都已正确设置。
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import asdict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import Settings
from src.config.config_manager import ConfigManager


class ConfigChecker:
    """配置检查器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_dir = project_root / "config"
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def check_all(self) -> bool:
        """执行所有检查
        
        Returns:
            bool: 检查是否通过
        """
        print("开始配置完整性检查...")
        print("=" * 50)
        
        # 检查配置文件存在性
        self._check_config_files_exist()
        
        # 检查环境变量文件
        self._check_env_files()
        
        # 检查配置文件语法
        self._check_config_syntax()
        
        # 检查配置完整性
        self._check_config_completeness()
        
        # 检查配置管理器
        self._check_config_manager()
        
        # 检查目录结构
        self._check_directory_structure()
        
        # 输出结果
        self._print_results()
        
        return len(self.errors) == 0
    
    def _check_config_files_exist(self) -> None:
        """检查配置文件是否存在"""
        print("检查配置文件存在性...")
        
        required_files = [
            "settings.yaml",
            "default.yaml",
            "user_settings.yaml"
        ]
        
        for filename in required_files:
            file_path = self.config_dir / filename
            if not file_path.exists():
                self.errors.append(f"配置文件不存在: {file_path}")
            else:
                print(f"  ✓ {filename}")
    
    def _check_env_files(self) -> None:
        """检查环境变量文件"""
        print("\n检查环境变量文件...")
        
        env_files = [
            ".env",
            ".env.local",
            ".env.production"
        ]
        
        for filename in env_files:
            file_path = self.project_root / filename
            if file_path.exists():
                print(f"  ✓ {filename}")
                # 检查文件内容
                self._check_env_file_content(file_path)
            else:
                if filename == ".env":
                    self.errors.append(f"环境变量文件不存在: {file_path}")
                else:
                    self.warnings.append(f"可选环境变量文件不存在: {file_path}")
    
    def _check_env_file_content(self, file_path: Path) -> None:
        """检查环境变量文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查是否包含敏感信息（API密钥等）
            sensitive_patterns = [
                "OPENAI_API_KEY=",
                "ANTHROPIC_API_KEY=",
                "SECRET_KEY=",
                "JWT_SECRET_KEY=",
                "DATABASE_PASSWORD="
            ]
            
            for pattern in sensitive_patterns:
                if pattern in content:
                    line_with_value = [line for line in content.split('\n') if pattern in line]
                    if line_with_value:
                        value = line_with_value[0].split('=', 1)[1].strip()
                        if not value or value in ['""', "''", '"your_key_here"', "'your_key_here'"]:
                            self.warnings.append(f"{file_path.name}: {pattern.rstrip('=')} 未设置")
                            
        except Exception as e:
            self.errors.append(f"读取环境变量文件失败 {file_path}: {e}")
    
    def _check_config_syntax(self) -> None:
        """检查配置文件语法"""
        print("\n检查配置文件语法...")
        
        yaml_files = [
            self.config_dir / "settings.yaml",
            self.config_dir / "default.yaml",
            self.config_dir / "user_settings.yaml"
        ]
        
        for file_path in yaml_files:
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        yaml.safe_load(f)
                    print(f"  ✓ {file_path.name} 语法正确")
                except yaml.YAMLError as e:
                    self.errors.append(f"YAML语法错误 {file_path}: {e}")
                except Exception as e:
                    self.errors.append(f"读取配置文件失败 {file_path}: {e}")
    
    def _check_config_completeness(self) -> None:
        """检查配置完整性"""
        print("\n检查配置完整性...")
        
        try:
            # 创建默认设置对象
            default_settings = Settings()
            default_dict = asdict(default_settings)
            
            # 检查主配置文件
            settings_file = self.config_dir / "settings.yaml"
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
                
                missing_sections = self._find_missing_config_sections(default_dict, config_data)
                if missing_sections:
                    for section in missing_sections:
                        self.warnings.append(f"配置节缺失: {section}")
                else:
                    print("  ✓ 配置结构完整")
                    
        except Exception as e:
            self.errors.append(f"检查配置完整性失败: {e}")
    
    def _find_missing_config_sections(self, default: Dict[str, Any], config: Dict[str, Any], prefix: str = "") -> List[str]:
        """查找缺失的配置节"""
        missing = []
        
        for key, value in default.items():
            current_path = f"{prefix}.{key}" if prefix else key
            
            if key not in config:
                missing.append(current_path)
            elif isinstance(value, dict) and isinstance(config[key], dict):
                missing.extend(self._find_missing_config_sections(value, config[key], current_path))
                
        return missing
    
    def _check_config_manager(self) -> None:
        """检查配置管理器"""
        print("\n检查配置管理器...")
        
        try:
            # 测试配置管理器初始化
            config_manager = ConfigManager()
            print("  ✓ 配置管理器初始化成功")
            
            # 测试配置加载
            settings = config_manager.get_settings()
            print("  ✓ 配置加载成功")
            
            # 验证配置
            validation_errors = settings.validate()
            if validation_errors:
                for error in validation_errors:
                    self.warnings.append(f"配置验证警告: {error}")
            else:
                print("  ✓ 配置验证通过")
                
        except Exception as e:
            self.errors.append(f"配置管理器测试失败: {e}")
    
    def _check_directory_structure(self) -> None:
        """检查目录结构"""
        print("\n检查目录结构...")
        
        required_dirs = [
            "config",
            "src",
            "src/config",
            "data",
            "temp",
            "logs",
            "uploads",
            "backups"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                if dir_name in ["data", "temp", "logs", "uploads", "backups"]:
                    # 这些目录可以自动创建
                    self.warnings.append(f"目录不存在（将自动创建）: {dir_path}")
                    try:
                        dir_path.mkdir(parents=True, exist_ok=True)
                        print(f"  ✓ 已创建目录: {dir_name}")
                    except Exception as e:
                        self.errors.append(f"创建目录失败 {dir_path}: {e}")
                else:
                    self.errors.append(f"必需目录不存在: {dir_path}")
            else:
                print(f"  ✓ {dir_name}")
    
    def _print_results(self) -> None:
        """输出检查结果"""
        print("\n" + "=" * 50)
        print("配置检查结果:")
        
        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️  发现 {len(self.warnings)} 个警告:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ 所有检查通过！配置完整且正确。")
        elif not self.errors:
            print("\n✅ 基本检查通过，但有一些警告需要注意。")
        else:
            print("\n❌ 检查失败，请修复上述错误后重试。")


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    checker = ConfigChecker(project_root)
    
    success = checker.check_all()
    
    if success:
        print("\n配置检查完成，可以继续开发。")
        sys.exit(0)
    else:
        print("\n配置检查失败，请修复错误后重试。")
        sys.exit(1)


if __name__ == "__main__":
    main()