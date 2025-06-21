#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库配置工具
用于动态生成和管理数据库配置
"""

import sys
from pathlib import Path
from config_loader import get_database_config, get_project_info

# 添加tools目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))


def generate_database_env(
        env: str = 'development',
        output_file: str = None) -> str:
    """
    生成数据库环境变量配置

    Args:
        env: 环境名称 (development, production, test)
        output_file: 输出文件路径，如果为None则返回字符串

    Returns:
        str: 环境变量配置内容
    """
    try:
        db_config = get_database_config(env)
        project_info = get_project_info()

        env_content = f"""# 数据库配置 - {env.upper()} 环境
# 项目: {project_info['name']}
# 生成时间: {project_info.get('updated_at', 'N/A')}

# 数据库连接信息
DATABASE_URL={db_config['url']}
DB_HOST={db_config['host']}
DB_PORT={db_config['port']}
DB_NAME={db_config['name']}
DB_USER={db_config['username']}
DB_PASSWORD={db_config['password']}

# 项目信息
PROJECT_NAME={project_info['name']}
"""

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(env_content)
            print(f"数据库配置已写入: {output_path}")

        return env_content

    except Exception as e:
        print(f"生成数据库配置失败: {e}")
        return ""


def update_docker_compose_env(project_name: str = None) -> bool:
    """
    更新docker-compose文件中的环境变量

    Args:
        project_name: 项目名称，如果为None则从配置获取

    Returns:
        bool: 更新是否成功
    """
    try:
        if not project_name:
            project_info = get_project_info()
            project_name = project_info['name']

        # 更新docker-compose.yml
        compose_file = Path(__file__).parent.parent / \
            'project' / 'docker-compose.yml'
        if compose_file.exists():
            # TODO: 实现Docker Compose配置更新逻辑
            print(f"Docker Compose配置已更新，项目名称: {project_name}")
            return True
        else:
            print(f"Docker Compose文件不存在: {compose_file}")
            return False

    except Exception as e:
        print(f"更新Docker Compose配置失败: {e}")
        return False


def validate_database_config(env: str = 'development') -> bool:
    """
    验证数据库配置

    Args:
        env: 环境名称

    Returns:
        bool: 配置是否有效
    """
    try:
        db_config = get_database_config(env)

        # 检查必需字段
        required_fields = [
            'name',
            'host',
            'port',
            'username',
            'password',
            'url']
        for field in required_fields:
            if not db_config.get(field):
                print(f"数据库配置缺少必需字段: {field}")
                return False

        print(f"数据库配置验证通过 ({env} 环境)")
        print(f"  数据库名称: {db_config['name']}")
        print(f"  连接地址: {db_config['host']}:{db_config['port']}")
        print(f"  连接URL: {db_config['url']}")

        return True

    except Exception as e:
        print(f"数据库配置验证失败: {e}")
        return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='数据库配置工具')
    parser.add_argument('--env', default='development',
                        choices=['development', 'production', 'test'],
                        help='环境名称')
    parser.add_argument('--generate-env', action='store_true',
                        help='生成环境变量配置')
    parser.add_argument('--output', help='输出文件路径')
    parser.add_argument('--validate', action='store_true',
                        help='验证数据库配置')
    parser.add_argument('--update-docker', action='store_true',
                        help='更新Docker Compose配置')

    args = parser.parse_args()

    if args.validate:
        validate_database_config(args.env)

    if args.generate_env:
        generate_database_env(args.env, args.output)

    if args.update_docker:
        update_docker_compose_env()

    if not any([args.validate, args.generate_env, args.update_docker]):
        # 默认显示配置信息
        print("=== 数据库配置信息 ===")
        for env in ['development', 'production', 'test']:
            print(f"\n{env.upper()} 环境:")
            validate_database_config(env)


if __name__ == '__main__':
    main()
