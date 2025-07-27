#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理命令行工具
提供统一配置管理中心的命令行接口
"""

import os
import sys
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# 添加项目路径到sys.path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from project.src.config.config_manager import get_config_manager
from project.src.config.config_validator import ConfigValidator, ConfigMigrator
from project.src.config.default_config import get_default_provider
from project.src.config.path_manager import get_path_manager
from project.src.config.environment import get_current_environment, get_environment_manager


class ConfigCLI:
    """配置管理命令行接口"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.path_manager = get_path_manager()
        self.validator = ConfigValidator()
        self.migrator = ConfigMigrator()
        self.default_provider = get_default_provider()
    
    def show_config(self, section: Optional[str] = None, format_type: str = 'yaml') -> None:
        """显示配置信息"""
        try:
            if section:
                config_data = self.config_manager.get_config(section)
                if config_data is None:
                    print(f"❌ 配置段不存在: {section}")
                    return
            else:
                config_data = self.config_manager.get_config()
            
            if format_type.lower() == 'json':
                print(json.dumps(config_data, indent=2, ensure_ascii=False))
            elif format_type.lower() == 'yaml':
                print(yaml.dump(config_data, default_flow_style=False, allow_unicode=True))
            else:
                print(f"❌ 不支持的格式: {format_type}")
                
        except Exception as e:
            print(f"❌ 显示配置失败: {e}")
    
    def validate_config(self, verbose: bool = False) -> bool:
        """验证配置"""
        print("🔍 验证配置中...")
        
        try:
            result = self.validator.validate_all()
            
            if result['valid']:
                print("✅ 配置验证通过")
            else:
                print("❌ 配置验证失败")
            
            if result['errors']:
                print("\n🚨 错误:")
                for error in result['errors']:
                    print(f"  • {error}")
            
            if result['warnings']:
                print("\n⚠️  警告:")
                for warning in result['warnings']:
                    print(f"  • {warning}")
            
            if result['suggestions']:
                print("\n💡 建议:")
                for suggestion in result['suggestions']:
                    print(f"  • {suggestion}")
            
            if verbose:
                print("\n📊 详细信息:")
                print(f"  • 错误数量: {len(result['errors'])}")
                print(f"  • 警告数量: {len(result['warnings'])}")
                print(f"  • 建议数量: {len(result['suggestions'])}")
            
            return result['valid']
            
        except Exception as e:
            print(f"❌ 验证配置失败: {e}")
            return False
    
    def migrate_config(self, force: bool = False) -> bool:
        """迁移配置"""
        print("🔄 迁移配置中...")
        
        try:
            # 先验证配置
            if not force:
                if not self.validate_config():
                    print("❌ 配置验证失败，请先修复配置问题或使用 --force 强制迁移")
                    return False
            
            # 执行迁移
            success = True
            
            # 迁移alembic配置
            print("  📝 迁移alembic配置...")
            if self.migrator.migrate_alembic_config():
                print("    ✅ alembic配置迁移成功")
            else:
                print("    ❌ alembic配置迁移失败")
                success = False
            
            # 创建.env文件
            print("  📝 创建.env文件...")
            if self.migrator.create_env_file():
                print("    ✅ .env文件创建成功")
            else:
                print("    ❌ .env文件创建失败")
                success = False
            
            # 导出前端配置
            print("  📝 导出前端配置...")
            if self.migrator.export_frontend_config():
                print("    ✅ 前端配置导出成功")
            else:
                print("    ❌ 前端配置导出失败")
                success = False
            
            # 导出后端配置
            print("  📝 导出后端配置...")
            if self.migrator.export_backend_config():
                print("    ✅ 后端配置导出成功")
            else:
                print("    ❌ 后端配置导出失败")
                success = False
            
            if success:
                print("✅ 配置迁移完成")
            else:
                print("❌ 配置迁移部分失败")
            
            return success
            
        except Exception as e:
            print(f"❌ 迁移配置失败: {e}")
            return False
    
    def create_env_file(self, output_path: Optional[str] = None) -> bool:
        """创建.env文件"""
        try:
            if self.migrator.create_env_file(output_path):
                print(f"✅ .env文件创建成功: {output_path or '.env'}")
                return True
            else:
                print("❌ .env文件创建失败")
                return False
        except Exception as e:
            print(f"❌ 创建.env文件失败: {e}")
            return False
    
    def export_config(self, target: str, output_path: Optional[str] = None) -> bool:
        """导出配置"""
        try:
            if target.lower() == 'frontend':
                if self.migrator.export_frontend_config(output_path):
                    print(f"✅ 前端配置导出成功: {output_path or 'project/frontend/src/config/config.json'}")
                    return True
                else:
                    print("❌ 前端配置导出失败")
                    return False
            elif target.lower() == 'backend':
                if self.migrator.export_backend_config(output_path):
                    print(f"✅ 后端配置导出成功: {output_path or 'project/backend/app/core/settings.py'}")
                    return True
                else:
                    print("❌ 后端配置导出失败")
                    return False
            else:
                print(f"❌ 不支持的导出目标: {target}")
                return False
        except Exception as e:
            print(f"❌ 导出配置失败: {e}")
            return False
    
    def show_paths(self, verbose: bool = False) -> None:
        """显示路径配置"""
        try:
            print("📁 项目路径配置:")
            
            all_paths = self.path_manager.get_all_paths()
            for name, path in all_paths.items():
                status = "✅" if path.exists() else "❌"
                print(f"  {status} {name}: {path}")
            
            if verbose:
                print("\n🔍 路径验证:")
                validation = self.path_manager.validate_paths()
                
                for category, paths in validation.items():
                    if paths:
                        print(f"\n{category}:")
                        for path in paths:
                            print(f"  • {path}")
                
                print("\n🌍 环境变量:")
                env_vars = self.path_manager.export_env_vars()
                for key, value in env_vars.items():
                    print(f"  {key}={value}")
                    
        except Exception as e:
            print(f"❌ 显示路径失败: {e}")
    
    def show_environment(self) -> None:
        """显示环境信息"""
        try:
            current_env = get_current_environment()
            print(f"🌍 当前环境: {current_env}")
            
            env_config = self.config_manager.get_config('environment')
            if env_config:
                print("\n📋 环境配置:")
                for key, value in env_config.items():
                    if isinstance(value, dict):
                        print(f"  {key}: {{...}}")
                    else:
                        print(f"  {key}: {value}")
                        
        except Exception as e:
            print(f"❌ 显示环境信息失败: {e}")
    
    def set_environment(self, environment: str) -> bool:
        """设置环境"""
        try:
            valid_envs = ['development', 'testing', 'production']
            if environment not in valid_envs:
                print(f"❌ 无效的环境: {environment}")
                print(f"   有效环境: {', '.join(valid_envs)}")
                return False
            
            # 使用环境管理器设置环境
            env_manager = get_environment_manager()
            env_manager.set_environment(environment)
            print(f"✅ 环境已设置为: {environment}")
            return True
            
        except Exception as e:
            print(f"❌ 设置环境失败: {e}")
            return False
    
    def health_check(self) -> bool:
        """健康检查"""
        print("🏥 执行健康检查...")
        
        all_good = True
        
        # 检查配置文件
        print("\n📄 配置文件检查:")
        config_file = self.config_manager.config_file
        if config_file.exists():
            print(f"  ✅ 配置文件存在: {config_file}")
        else:
            print(f"  ❌ 配置文件不存在: {config_file}")
            all_good = False
        
        # 检查路径
        print("\n📁 路径检查:")
        path_validation = self.path_manager.validate_paths()
        
        if path_validation['valid']:
            print(f"  ✅ 有效路径: {len(path_validation['valid'])}个")
        
        if path_validation['missing']:
            print(f"  ❌ 缺失路径: {len(path_validation['missing'])}个")
            for missing in path_validation['missing']:
                print(f"    • {missing}")
            all_good = False
        
        if path_validation['permission_errors']:
            print(f"  ⚠️  权限问题: {len(path_validation['permission_errors'])}个")
            for error in path_validation['permission_errors']:
                print(f"    • {error}")
        
        # 检查配置有效性
        print("\n🔍 配置验证:")
        config_valid = self.validate_config(verbose=False)
        if not config_valid:
            all_good = False
        
        # 检查环境
        print("\n🌍 环境检查:")
        try:
            current_env = get_current_environment()
            print(f"  ✅ 当前环境: {current_env}")
        except Exception as e:
            print(f"  ❌ 环境检查失败: {e}")
            all_good = False
        
        print("\n" + "="*50)
        if all_good:
            print("✅ 健康检查通过 - 系统状态良好")
        else:
            print("❌ 健康检查失败 - 发现问题需要修复")
        
        return all_good
    
    def reset_config(self, section: Optional[str] = None, confirm: bool = False) -> bool:
        """重置配置到默认值"""
        if not confirm:
            print("⚠️  警告: 此操作将重置配置到默认值，所有自定义配置将丢失！")
            response = input("确认继续？(yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("❌ 操作已取消")
                return False
        
        try:
            if section:
                # 重置特定段
                default_config = self.default_provider.get_default_config()
                if section not in default_config:
                    print(f"❌ 配置段不存在: {section}")
                    return False
                
                self.config_manager.set_config(section, default_config[section])
                print(f"✅ 配置段 '{section}' 已重置为默认值")
            else:
                # 重置全部配置
                default_config = self.default_provider.get_default_config()
                
                # 保存到配置文件
                with open(self.config_manager.config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
                
                # 重新加载配置
                self.config_manager.load_config()
                print("✅ 所有配置已重置为默认值")
            
            return True
            
        except Exception as e:
            print(f"❌ 重置配置失败: {e}")
            return False
    
    def backup_config(self, output_path: Optional[str] = None) -> bool:
        """备份配置"""
        try:
            if output_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"config_backup_{timestamp}.yaml"
            
            config_data = self.config_manager.get_config()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            print(f"✅ 配置已备份到: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ 备份配置失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='PG-PMC 统一配置管理中心命令行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s show                    # 显示所有配置
  %(prog)s show database           # 显示数据库配置
  %(prog)s validate                # 验证配置
  %(prog)s migrate                 # 迁移配置
  %(prog)s env-file                # 创建.env文件
  %(prog)s export frontend         # 导出前端配置
  %(prog)s paths                   # 显示路径配置
  %(prog)s health                  # 健康检查
  %(prog)s reset database          # 重置数据库配置
  %(prog)s backup                  # 备份配置
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # show命令
    show_parser = subparsers.add_parser('show', help='显示配置')
    show_parser.add_argument('section', nargs='?', help='配置段名称')
    show_parser.add_argument('--format', choices=['yaml', 'json'], default='yaml', help='输出格式')
    
    # validate命令
    validate_parser = subparsers.add_parser('validate', help='验证配置')
    validate_parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    # migrate命令
    migrate_parser = subparsers.add_parser('migrate', help='迁移配置')
    migrate_parser.add_argument('--force', '-f', action='store_true', help='强制迁移')
    
    # env-file命令
    env_parser = subparsers.add_parser('env-file', help='创建.env文件')
    env_parser.add_argument('--output', '-o', help='输出文件路径')
    
    # export命令
    export_parser = subparsers.add_parser('export', help='导出配置')
    export_parser.add_argument('target', choices=['frontend', 'backend'], help='导出目标')
    export_parser.add_argument('--output', '-o', help='输出文件路径')
    
    # paths命令
    paths_parser = subparsers.add_parser('paths', help='显示路径配置')
    paths_parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    # environment命令
    env_group = subparsers.add_parser('environment', help='环境管理')
    env_subparsers = env_group.add_subparsers(dest='env_action')
    env_subparsers.add_parser('show', help='显示环境信息')
    set_env_parser = env_subparsers.add_parser('set', help='设置环境')
    set_env_parser.add_argument('env', choices=['development', 'testing', 'production'], help='环境名称')
    
    # health命令
    subparsers.add_parser('health', help='健康检查')
    
    # reset命令
    reset_parser = subparsers.add_parser('reset', help='重置配置')
    reset_parser.add_argument('section', nargs='?', help='配置段名称（可选）')
    reset_parser.add_argument('--yes', '-y', action='store_true', help='自动确认')
    
    # backup命令
    backup_parser = subparsers.add_parser('backup', help='备份配置')
    backup_parser.add_argument('--output', '-o', help='输出文件路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = ConfigCLI()
    
    try:
        if args.command == 'show':
            cli.show_config(args.section, args.format)
        
        elif args.command == 'validate':
            success = cli.validate_config(args.verbose)
            sys.exit(0 if success else 1)
        
        elif args.command == 'migrate':
            success = cli.migrate_config(args.force)
            sys.exit(0 if success else 1)
        
        elif args.command == 'env-file':
            success = cli.create_env_file(args.output)
            sys.exit(0 if success else 1)
        
        elif args.command == 'export':
            success = cli.export_config(args.target, args.output)
            sys.exit(0 if success else 1)
        
        elif args.command == 'paths':
            cli.show_paths(args.verbose)
        
        elif args.command == 'environment':
            if args.env_action == 'show':
                cli.show_environment()
            elif args.env_action == 'set':
                success = cli.set_environment(args.env)
                sys.exit(0 if success else 1)
            else:
                cli.show_environment()
        
        elif args.command == 'health':
            success = cli.health_check()
            sys.exit(0 if success else 1)
        
        elif args.command == 'reset':
            success = cli.reset_config(args.section, args.yes)
            sys.exit(0 if success else 1)
        
        elif args.command == 'backup':
            success = cli.backup_config(args.output)
            sys.exit(0 if success else 1)
        
        else:
            print(f"❌ 未知命令: {args.command}")
            parser.print_help()
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n❌ 操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行命令失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()