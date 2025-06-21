#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一配置加载模块
支持多种配置文件格式和验证功能
"""
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

# 导入错误处理机制
from exceptions import ValidationError, ErrorHandler

# 配置文件路径
PROJECT_CONFIG_PATH = Path(__file__).parent.parent / \
    "docs" / "03-管理" / "project_config.yaml"
STRUCTURE_CONFIG_PATH = Path(__file__).parent / "structure_check_config.yaml"

# 缓存配置
_project_config = None
_structure_config = None

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化错误处理器
error_handler = ErrorHandler()


class ConfigLoadError(Exception):
    """配置加载错误异常类"""
    pass


def load_yaml_config(
        config_path: Union[str, Path], validate: bool = True) -> Dict[str, Any]:
    """加载YAML配置文件

    Args:
        config_path: 配置文件路径
        validate: 是否进行配置验证

    Returns:
        Dict: 配置字典

    Raises:
        ConfigLoadError: 配置加载失败
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise ConfigLoadError(f"配置文件不存在: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if config is None:
            raise ConfigLoadError(f"配置文件为空: {config_path}")

        logger.info(f"成功加载配置文件: {config_path}")

        # 配置验证
        if validate and config_path.name == 'structure_check_config.yaml':
            try:
                from .config_validator import ConfigValidator
                validator = ConfigValidator()
                if not validator.validate_structure_check_config(config):
                    logger.warning("配置验证发现问题，但仍继续使用")
            except ImportError:
                logger.warning("配置验证模块不可用，跳过验证")
            except Exception as e:
                logger.warning(f"配置验证失败: {e}")

        return config

    except yaml.YAMLError as e:
        raise ConfigLoadError(f"配置文件格式错误: {config_path}\n{e}")
    except Exception as e:
        raise ConfigLoadError(f"加载配置文件时发生错误: {config_path}\n{e}")


def get_config():
    """加载并返回项目配置字典

    Returns:
        Dict: 项目配置字典

    Raises:
        ConfigLoadError: 配置加载失败
    """
    global _project_config

    if _project_config is None:
        _project_config = load_yaml_config(PROJECT_CONFIG_PATH, validate=False)

        # 处理项目根目录路径
        if 'project_root' in _project_config and _project_config['project_root']:
            _project_config['project_root'] = Path(
                _project_config['project_root']).resolve()
        else:
            # 默认为配置文件所在目录的上两级目录
            _project_config['project_root'] = Path(
                __file__).parent.parent.resolve()

        # 处理模板变量替换
        _process_template_variables(_project_config)

        logger.info(f"项目根目录: {_project_config['project_root']}")

    return _project_config


def get_mcp_config() -> Dict[str, Any]:
    """获取MCP配置

    Returns:
        Dict: MCP配置字典，包含memory和task_manager配置
    """
    config = get_config()
    mcp_config = config.get('mcp', {})

    # 设置默认值
    default_mcp_config = {
        'memory': {
            'storage_path': 'docs/02-开发/memory.json',
            'isolation_mode': 'project'
        },
        'task_manager': {
            'storage_path': 'docs/02-开发/tasks.json',
            'isolation_mode': 'project'
        }
    }

    # 合并默认配置和用户配置
    for service in ['memory', 'task_manager']:
        if service not in mcp_config:
            mcp_config[service] = default_mcp_config[service]
        else:
            # 确保必要的字段存在
            for key, value in default_mcp_config[service].items():
                if key not in mcp_config[service]:
                    mcp_config[service][key] = value

    return mcp_config


def _process_template_variables(
        config: Dict[str, Any], project_name: Optional[str] = None) -> None:
    """
    处理配置中的模板变量

    Args:
        config: 配置字典
        project_name: 项目名称，如果为None则使用默认值
    """
    from datetime import datetime

    # 获取模板配置
    template_config = config.get('template', {})

    # 如果没有提供项目名称，使用默认值
    if project_name is None:
        project_name = template_config.get(
            'default_project_name', config.get(
                'project_name', '3AI'))

    # 准备替换变量
    variables = {
        'PROJECT_NAME': project_name,
        'PROJECT_DESCRIPTION': template_config.get(
            'default_description',
            'AI项目开发框架'),
        'CREATED_AT': datetime.now().strftime('%Y-%m-%d'),
        'UPDATED_AT': datetime.now().strftime('%Y-%m-%d')}

    def replace_in_dict(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = replace_in_dict(value)
        elif isinstance(obj, list):
            return [replace_in_dict(item) for item in obj]
        elif isinstance(obj, str):
            result = obj
            for var_name, var_value in variables.items():
                result = result.replace(f'{{{{{var_name}}}}}', str(var_value))
            return result
        return obj

    replace_in_dict(config)


def get_database_config(env: str = 'development') -> Dict[str, Any]:
    """获取数据库配置

    Args:
        env: 环境名称 (development, production, test)

    Returns:
        Dict: 数据库配置
    """
    import os
    config = get_config()
    db_config = config.get('database', {})

    # 根据环境选择数据库名称
    if env == 'test':
        db_name = db_config.get(
            'test_name', f"{
                config.get(
                    'project_name', '3AI')}_test_db")
    elif env == 'development':
        db_name = db_config.get(
            'dev_name', f"{
                config.get(
                    'project_name', '3AI')}_dev_db")
    else:
        db_name = db_config.get(
            'name', f"{
                config.get(
                    'project_name', '3AI')}_db")

    # 从环境变量或配置获取默认值
    default_host = os.getenv('DB_HOST', db_config.get('host', 'localhost'))
    default_port = int(os.getenv('DB_PORT', db_config.get('port', 5432)))
    default_username = os.getenv(
        'DB_USER', db_config.get(
            'username', 'postgres'))
    default_password = os.getenv(
        'DB_PASSWORD', db_config.get(
            'password', 'password'))

    # 构建数据库URL
    url_template = db_config.get(
        'url_template',
        'postgresql://{username}:{password}@{host}:{port}/{database_name}')
    database_url = url_template.format(
        username=default_username,
        password=default_password,
        host=default_host,
        port=default_port,
        database_name=db_name
    )

    return {
        'name': db_name,
        'host': default_host,
        'port': default_port,
        'username': default_username,
        'password': default_password,
        'url': database_url
    }


def get_app_config() -> Dict[str, Any]:
    """获取应用配置

    Returns:
        Dict: 应用配置
    """
    config = get_config()
    return config.get('app', {})


def get_paths_config() -> Dict[str, Any]:
    """获取路径配置

    Returns:
        Dict: 路径配置
    """
    config = get_config()
    paths = config.get('paths', {})
    project_root = config.get('project_root', Path.cwd())

    # 转换相对路径为绝对路径
    result = {}
    for key, value in paths.items():
        if isinstance(value, str):
            result[key] = project_root / value
        elif isinstance(value, list):
            result[key] = [
                project_root /
                item if isinstance(
                    item,
                    str) else item for item in value]
        else:
            result[key] = value

    return result


def get_project_info() -> Dict[str, Any]:
    """获取项目基本信息

    Returns:
        Dict: 项目信息
    """
    config = get_config()
    return {
        'name': config.get('project_name', '3AI'),
        'version': config.get('project_version', '1.0.0'),
        'description': config.get('project_description', ''),
        'root': config.get('project_root', Path.cwd()),
        'created_at': config.get('created_at', ''),
        'updated_at': config.get('updated_at', '')
    }


def get_structure_config() -> Dict[str, Any]:
    """加载并返回结构检查配置字典

    Returns:
        Dict: 结构检查配置字典

    Raises:
        ConfigLoadError: 配置加载失败
    """
    global _structure_config

    if _structure_config is None:
        _structure_config = load_yaml_config(
            STRUCTURE_CONFIG_PATH, validate=True)
        logger.info("结构检查配置加载完成")

    return _structure_config


def reload_configs():
    """重新加载所有配置（清除缓存）"""
    global _project_config, _structure_config
    _project_config = None
    _structure_config = None
    logger.info("配置缓存已清除")


def get_config_info() -> Dict[str, Any]:
    """获取配置信息摘要

    Returns:
        Dict: 配置信息摘要
    """
    info = {
        'project_config_path': str(PROJECT_CONFIG_PATH),
        'structure_config_path': str(STRUCTURE_CONFIG_PATH),
        'project_config_exists': PROJECT_CONFIG_PATH.exists(),
        'structure_config_exists': STRUCTURE_CONFIG_PATH.exists(),
        'project_config_loaded': _project_config is not None,
        'structure_config_loaded': _structure_config is not None
    }

    if _project_config:
        info['project_root'] = str(_project_config.get('project_root', 'N/A'))

    if _structure_config:
        sc_config = _structure_config.get('structure_check', {})
        info['config_version'] = sc_config.get('config_version', 'N/A')
        info['performance_config'] = 'performance' in sc_config
        info['logging_config'] = 'logging' in sc_config

    return info


if __name__ == "__main__":
    import json

    try:
        logger.info("=== 配置加载器测试 ===")

        # 测试配置信息
        logger.info("\n1. 配置文件信息:")
        info = get_config_info()
        logger.info(json.dumps(info, indent=2, ensure_ascii=False))

        # 测试项目配置加载
        logger.info("\n2. 测试项目配置加载:")
        try:
            config = get_config()
            logger.info("✓ 项目配置加载成功")
            logger.info(f"  项目根目录: {config.get('project_root')}")
            if 'structure_check' in config:
                report_dir = config.get(
                    'project_root') / config['structure_check'].get('report_dir', '')
                logger.info(f"  自检报告目录: {report_dir}")
        except Exception as e:
            logger.error(f"✗ 项目配置加载失败: {e}")

        # 测试结构检查配置加载
        logger.info("\n3. 测试结构检查配置加载:")
        try:
            sc_config = get_structure_config()
            logger.info("✓ 结构检查配置加载成功")
            sc_data = sc_config.get('structure_check', {})
            logger.info(f"  配置版本: {sc_data.get('config_version', 'N/A')}")
            logger.info(f"  性能配置: {'✓' if 'performance' in sc_data else '✗'}")
            logger.info(f"  日志配置: {'✓' if 'logging' in sc_data else '✗'}")
            logger.info(f"  文件类型配置: {'✓' if 'file_types' in sc_data else '✗'}")
        except Exception as e:
            logger.error(f"✗ 结构检查配置加载失败: {e}")

        # 测试配置验证
        logger.info("\n4. 测试配置验证:")
        try:
            from config_validator import validate_config_file
            result = validate_config_file(STRUCTURE_CONFIG_PATH)
            logger.info(f"✓ 配置验证完成，结果: {'通过' if result else '有问题'}")
        except Exception as e:
            error_handler.handle_error(ValidationError(f"配置验证失败: {e}"))

        logger.info("\n=== 测试完成 ===")
    except Exception as e:
        error_handler.handle_error(ValidationError(f"配置加载器测试失败: {e}"))
