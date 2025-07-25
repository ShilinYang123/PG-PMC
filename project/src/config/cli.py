#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理CLI工具
提供命令行接口来管理和验证配置
"""

import argparse
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from . import (
        get_settings_manager,
        get_settings,
        create_default_env,
        validate_config,
        export_env_vars,
        init_config
    )
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    try:
        from src.config import (
            get_settings_manager,
            get_settings,
            create_default_env,
            validate_config,
            export_env_vars,
            init_config
        )
    except ImportError as e:
        print(f"错误: 无法导入配置模块: {e}")
        sys.exit(1)


def print_success(message: str):
    """打印成功消息"""
    print(f"✅ {message}")


def print_error(message: str):
    """打印错误消息"""
    print(f"❌ {message}")


def print_warning(message: str):
    """打印警告消息"""
    print(f"⚠️ {message}")


def print_info(message: str):
    """打印信息消息"""
    print(f"ℹ️ {message}")


def cmd_init(args):
    """初始化配置"""
    try:
        print_info("正在初始化配置...")
        
        # 初始化配置
        config_file = args.config_file or None
        environment = args.environment or 'development'
        
        result = init_config(config_file=config_file, environment=environment)
        
        if result.get('success', False):
            print_success("配置初始化完成")
            print_info(f"配置文件: {result.get('config_file', 'N/A')}")
            print_info(f"环境: {result.get('environment', 'N/A')}")
        else:
            print_error(f"配置初始化失败: {result.get('error', '未知错误')}")
            return 1
            
    except Exception as e:
        print_error(f"初始化配置时发生错误: {e}")
        return 1
    
    return 0


def cmd_validate(args):
    """验证配置"""
    try:
        print_info("正在验证配置...")
        
        # 验证配置
        result = validate_config()
        
        if result.get('valid', False):
            print_success("配置验证通过")
        else:
            print_error("配置验证失败")
        
        # 显示错误
        errors = result.get('errors', [])
        if errors:
            print_error("发现以下错误:")
            for error in errors:
                print(f"  - {error}")
        
        # 显示警告
        warnings = result.get('warnings', [])
        if warnings:
            print_warning("发现以下警告:")
            for warning in warnings:
                print(f"  - {warning}")
        
        # 显示信息
        info = result.get('info', [])
        if info:
            print_info("配置信息:")
            for item in info:
                print(f"  - {item}")
        
        return 0 if result.get('valid', False) else 1
        
    except Exception as e:
        print_error(f"验证配置时发生错误: {e}")
        return 1


def cmd_show(args):
    """显示配置"""
    try:
        settings_manager = get_settings_manager()
        if not settings_manager:
            print_error("无法获取配置管理器")
            return 1
        
        settings = get_settings()
        if not settings:
            print_error("无法获取配置")
            return 1
        
        print_info("当前配置:")
        
        if args.section:
            # 显示特定部分
            section_data = getattr(settings, args.section, None)
            if section_data is None:
                print_error(f"配置部分 '{args.section}' 不存在")
                return 1
            
            if hasattr(section_data, '__dict__'):
                data = section_data.__dict__
            else:
                data = section_data
            
            if args.format == 'json':
                print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
            elif args.format == 'yaml':
                print(yaml.dump(data, default_flow_style=False, allow_unicode=True))
            else:
                for key, value in data.items():
                    print(f"  {key}: {value}")
        else:
            # 显示所有配置
            config_dict = {
                'project_name': settings.project_name,
                'version': settings.version,
                'description': settings.description,
                'environment': settings.environment,
                'debug': settings.debug,
                'host': settings.host,
                'port': settings.port,
                'database_url': settings.database_url,
                'redis_url': settings.redis_url,
                'log_level': settings.log_level,
                'log_file': settings.log_file,
            }
            
            if args.format == 'json':
                print(json.dumps(config_dict, indent=2, ensure_ascii=False))
            elif args.format == 'yaml':
                print(yaml.dump(config_dict, default_flow_style=False, allow_unicode=True))
            else:
                for key, value in config_dict.items():
                    print(f"  {key}: {value}")
        
        return 0
        
    except Exception as e:
        print_error(f"显示配置时发生错误: {e}")
        return 1


def cmd_export(args):
    """导出环境变量"""
    try:
        print_info("正在导出环境变量...")
        
        # 导出环境变量
        env_vars = export_env_vars()
        
        if args.output:
            # 写入文件
            output_path = Path(args.output)
            
            if args.format == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(env_vars, f, indent=2, ensure_ascii=False)
            elif args.format == 'yaml':
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(env_vars, f, default_flow_style=False, allow_unicode=True)
            else:
                # .env格式
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write("# PMC全流程管理系统 - 环境变量配置\n")
                    f.write("# 由配置管理CLI工具自动生成\n\n")
                    
                    for key, value in env_vars.items():
                        if isinstance(value, str):
                            f.write(f"{key}={value}\n")
                        else:
                            f.write(f"{key}={json.dumps(value)}\n")
            
            print_success(f"环境变量已导出到: {output_path}")
        else:
            # 输出到控制台
            if args.format == 'json':
                print(json.dumps(env_vars, indent=2, ensure_ascii=False))
            elif args.format == 'yaml':
                print(yaml.dump(env_vars, default_flow_style=False, allow_unicode=True))
            else:
                for key, value in env_vars.items():
                    if isinstance(value, str):
                        print(f"{key}={value}")
                    else:
                        print(f"{key}={json.dumps(value)}")
        
        return 0
        
    except Exception as e:
        print_error(f"导出环境变量时发生错误: {e}")
        return 1


def cmd_create_env(args):
    """创建.env文件"""
    try:
        print_info("正在创建.env文件...")
        
        # 创建.env文件
        env_file = args.output or '.env'
        environment = args.environment or 'development'
        
        result = create_default_env(env_file=env_file, environment=environment)
        
        if result.get('success', False):
            print_success(f".env文件已创建: {result.get('file_path', env_file)}")
            print_info(f"环境: {environment}")
        else:
            print_error(f"创建.env文件失败: {result.get('error', '未知错误')}")
            return 1
        
        return 0
        
    except Exception as e:
        print_error(f"创建.env文件时发生错误: {e}")
        return 1


def cmd_health(args):
    """健康检查"""
    try:
        print_info("正在执行健康检查...")
        
        settings_manager = get_settings_manager()
        
        # 检查配置管理器
        if settings_manager:
            print_success("配置管理器: 正常")
        else:
            print_error("配置管理器: 未加载")
            return 1
        
        # 检查配置文件
        config_file = settings_manager.config_manager.config_file
        if config_file.exists():
            print_success(f"配置文件: {config_file}")
        else:
            print_warning(f"配置文件不存在: {config_file}")
        
        # 检查环境管理器
        try:
            env_manager = settings_manager.environment_manager
            current_env = env_manager.get_current_environment()
            print_success(f"环境管理器: 正常 (当前环境: {current_env})")
        except Exception as e:
            print_error(f"环境管理器: 异常 - {e}")
        
        # 检查路径管理器
        try:
            path_manager = settings_manager.path_manager
            paths = path_manager.get_all_paths()
            print_success(f"路径管理器: 正常 (管理 {len(paths)} 个路径)")
        except Exception as e:
            print_error(f"路径管理器: 异常 - {e}")
        
        # 验证配置
        validation_result = validate_config()
        if validation_result.get('valid', False):
            print_success("配置验证: 通过")
        else:
            print_warning("配置验证: 有警告或错误")
            
            errors = validation_result.get('errors', [])
            if errors:
                print_error("错误:")
                for error in errors:
                    print(f"  - {error}")
            
            warnings = validation_result.get('warnings', [])
            if warnings:
                print_warning("警告:")
                for warning in warnings:
                    print(f"  - {warning}")
        
        print_success("健康检查完成")
        return 0
        
    except Exception as e:
        print_error(f"健康检查时发生错误: {e}")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="PMC配置管理CLI工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s init --environment development
  %(prog)s validate
  %(prog)s show --section database --format json
  %(prog)s export --output .env --format env
  %(prog)s create-env --environment production --output .env.prod
  %(prog)s health
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # init命令
    init_parser = subparsers.add_parser('init', help='初始化配置')
    init_parser.add_argument('--config-file', help='配置文件路径')
    init_parser.add_argument('--environment', choices=['development', 'production', 'testing', 'local'], 
                           default='development', help='环境类型')
    init_parser.set_defaults(func=cmd_init)
    
    # validate命令
    validate_parser = subparsers.add_parser('validate', help='验证配置')
    validate_parser.set_defaults(func=cmd_validate)
    
    # show命令
    show_parser = subparsers.add_parser('show', help='显示配置')
    show_parser.add_argument('--section', help='显示特定配置部分')
    show_parser.add_argument('--format', choices=['text', 'json', 'yaml'], 
                           default='text', help='输出格式')
    show_parser.set_defaults(func=cmd_show)
    
    # export命令
    export_parser = subparsers.add_parser('export', help='导出环境变量')
    export_parser.add_argument('--output', help='输出文件路径')
    export_parser.add_argument('--format', choices=['env', 'json', 'yaml'], 
                             default='env', help='输出格式')
    export_parser.set_defaults(func=cmd_export)
    
    # create-env命令
    create_env_parser = subparsers.add_parser('create-env', help='创建.env文件')
    create_env_parser.add_argument('--output', default='.env', help='输出文件路径')
    create_env_parser.add_argument('--environment', choices=['development', 'production', 'testing', 'local'], 
                                 default='development', help='环境类型')
    create_env_parser.set_defaults(func=cmd_create_env)
    
    # health命令
    health_parser = subparsers.add_parser('health', help='健康检查')
    health_parser.set_defaults(func=cmd_health)
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # 执行命令
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print_warning("操作被用户中断")
        return 1
    except Exception as e:
        print_error(f"执行命令时发生未预期的错误: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())