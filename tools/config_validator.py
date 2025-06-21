#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证模块
提供配置文件的完整性和正确性验证功能
"""

import re
import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging

# 导入错误处理机制
from exceptions import ValidationError, ErrorHandler
from config_loader import get_config, PROJECT_CONFIG_PATH

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化错误处理器
error_handler = ErrorHandler()


class ConfigValidationError(Exception):
    """配置验证错误异常类"""
    pass


class ConfigValidator:
    """配置验证器类"""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_structure_check_config(self, config: Dict[str, Any]) -> bool:
        """验证项目结构检查配置

        Args:
            config: 配置字典

        Returns:
            bool: 验证是否通过

        Raises:
            ConfigValidationError: 配置验证失败时抛出
        """
        self.errors.clear()
        self.warnings.clear()

        # 验证根节点
        if 'structure_check' not in config:
            self.errors.append("缺少根配置节点 'structure_check'")
            return False

        sc_config = config['structure_check']

        # 验证版本信息
        self._validate_version(sc_config)

        # 验证基本配置
        self._validate_basic_config(sc_config)

        # 验证性能配置
        self._validate_performance_config(sc_config)

        # 验证文件类型配置
        self._validate_file_types_config(sc_config)

        # 验证日志配置
        self._validate_logging_config(sc_config)

        # 验证默认规则
        self._validate_default_rules(sc_config)

        # 验证检查规则
        self._validate_check_rules(sc_config)

        # 输出验证结果
        self._report_validation_results()

        return len(self.errors) == 0

    def _validate_version(self, config: Dict[str, Any]) -> None:
        """验证版本配置"""
        if 'config_version' not in config:
            self.warnings.append("建议添加 'config_version' 字段")
        elif not isinstance(config['config_version'], str):
            self.errors.append("'config_version' 必须是字符串类型")
        elif not re.match(r'^\d+\.\d+\.\d+$', config['config_version']):
            self.warnings.append("'config_version' 建议使用语义化版本格式 (x.y.z)")

    def _validate_basic_config(self, config: Dict[str, Any]) -> None:
        """验证基本配置"""
        # 验证必需字段
        required_fields = [
            'standard_list_file',
            'report_dir',
            'report_name_format']
        for field in required_fields:
            if field not in config:
                self.errors.append(f"缺少必需字段 '{field}'")
            elif not isinstance(config[field], str):
                self.errors.append(f"'{field}' 必须是字符串类型")

        # 验证文件路径格式
        if 'standard_list_file' in config:
            path = config['standard_list_file']
            if not path.endswith(('.md', '.txt')):
                self.warnings.append("标准清单文件建议使用 .md 或 .txt 扩展名")

        # 验证报告名称格式
        if 'report_name_format' in config:
            format_str = config['report_name_format']
            if '{timestamp}' not in format_str:
                self.warnings.append("报告名称格式建议包含 {timestamp} 占位符")

    def _validate_performance_config(self, config: Dict[str, Any]) -> None:
        """验证性能配置"""
        if 'performance' not in config:
            self.warnings.append("建议添加 'performance' 配置节")
            return

        perf_config = config['performance']

        # 验证数值字段
        numeric_fields = {
            'max_file_size_mb': (1, 1000),
            'max_depth': (1, 50),
            'max_workers': (1, 32),
            'cache_size': (100, 10000),
            'timeout_seconds': (30, 3600)
        }

        for field, (min_val, max_val) in numeric_fields.items():
            if field in perf_config:
                value = perf_config[field]
                if not isinstance(value, (int, float)):
                    self.errors.append(f"performance.{field} 必须是数值类型")
                elif value < min_val or value > max_val:
                    self.warnings.append(
                        f"performance.{field} 建议在 {min_val}-{max_val} 范围内")

    def _validate_file_types_config(self, config: Dict[str, Any]) -> None:
        """验证文件类型配置"""
        if 'file_types' not in config:
            self.warnings.append("建议添加 'file_types' 配置节")
            return

        file_types = config['file_types']
        expected_sections = [
            'binary_extensions',
            'image_extensions',
            'media_extensions',
            'document_extensions']

        for section in expected_sections:
            if section not in file_types:
                self.warnings.append(f"建议在 'file_types' 中添加 '{section}' 配置")
            elif not isinstance(file_types[section], list):
                self.errors.append(f"file_types.{section} 必须是列表类型")
            else:
                # 验证扩展名格式
                for ext in file_types[section]:
                    if not isinstance(ext, str):
                        self.errors.append(
                            ""file_types.{section}' 中的扩展名必须是字符串")
                    elif not ext.startswith('.'):
                        self.errors.append("扩展名 "{ext}' 必须以点号开头")

    def _validate_logging_config(self, config: Dict[str, Any]) -> None:
        """验证日志配置"""
        if 'logging' not in config:
            self.warnings.append("建议添加 'logging' 配置节")
            return

        log_config = config['logging']

        # 验证日志级别
        if 'level' in log_config:
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if log_config['level'] not in valid_levels:
                self.errors.append(""logging.level' 必须是以下值之一: {valid_levels}")

        # 验证格式字符串
        if 'format' in log_config:
            format_str = log_config['format']
            required_parts = ['%(asctime)s', '%(levelname)s']
            for part in required_parts:
                if part not in format_str:
                    self.warnings.append(f"日志格式建议包含 {part}")

        # 验证文件配置
        if 'file_enabled' in log_config and log_config['file_enabled']:
            if 'file_path' not in log_config:
                self.errors.append("启用文件日志时必须指定 'file_path'")

    def _validate_default_rules(self, config: Dict[str, Any]) -> None:
        """验证默认规则"""
        # 验证禁止模式
        if 'default_forbidden_patterns' in config:
            patterns = config['default_forbidden_patterns']
            if not isinstance(patterns, list):
                self.errors.append("'default_forbidden_patterns' 必须是列表类型")
            else:
                for pattern in patterns:
                    if not isinstance(pattern, str):
                        self.errors.append("禁止模式必须是字符串类型")

        # 验证命名规则
        if 'default_naming_rules' in config:
            rules = config['default_naming_rules']
            if not isinstance(rules, dict):
                self.errors.append("'default_naming_rules' 必须是字典类型")
            else:
                for category, pattern in rules.items():
                    if not isinstance(pattern, str):
                        self.errors.append("命名规则 "{category}' 必须是字符串类型")
                    else:
                        # 验证正则表达式
                        try:
                            re.compile(pattern)
                        except re.error as e:
                            self.errors.append(
                                "命名规则 "{category}' 的正则表达式无效: {e}")

    def _validate_check_rules(self, config: Dict[str, Any]) -> None:
        """验证检查规则"""
        if 'rules' not in config:
            self.warnings.append("建议添加 'rules' 配置节")
            return

        rules = config['rules']

        # 验证布尔字段
        boolean_fields = [
            'check_file_size',
            'check_permissions',
            'check_encoding',
            'detailed_report',
            'include_suggestions']

        for field in boolean_fields:
            if field in rules and not isinstance(rules[field], bool):
                self.errors.append(""rules.{field}' 必须是布尔类型")

        # 验证编码
        if 'default_encoding' in rules:
            encoding = rules['default_encoding']
            if not isinstance(encoding, str):
                self.errors.append("'rules.default_encoding' 必须是字符串类型")
            else:
                # 验证编码是否有效
                try:
                    'test'.encode(encoding)
                except LookupError:
                    self.errors.append(f"不支持的编码格式: {encoding}")

    def _report_validation_results(self) -> None:
        """报告验证结果"""
        if self.errors:
            logger.error(f"配置验证发现 {len(self.errors)} 个错误:")
            for i, error in enumerate(self.errors, 1):
                logger.error(f"  {i}. {error}")

        if self.warnings:
            logger.warning(f"配置验证发现 {len(self.warnings)} 个警告:")
            for i, warning in enumerate(self.warnings, 1):
                logger.warning(f"  {i}. {warning}")

        if not self.errors and not self.warnings:
            logger.info("配置验证通过，未发现问题")

    def validate_project_config(self, config: Dict[str, Any]) -> bool:
        """验证项目配置

        Args:
            config: 项目配置字典

        Returns:
            bool: 验证是否通过
        """
        self.errors.clear()
        self.warnings.clear()

        # 验证项目基本信息
        self._validate_project_info(config)

        # 验证应用配置
        self._validate_app_config(config)

        # 验证数据库配置
        self._validate_database_config(config)

        # 验证Redis配置
        self._validate_redis_config(config)

        # 验证安全配置
        self._validate_security_config(config)

        # 输出验证结果
        self._report_validation_results()

        return len(self.errors) == 0

    def _validate_project_info(self, config: Dict[str, Any]) -> None:
        """验证项目基本信息"""
        required_fields = ['project_name', 'project_root']
        for field in required_fields:
            if field not in config:
                self.errors.append("缺少必需字段 "{field}'")
            elif not isinstance(config[field], str):
                self.errors.append(""{field}' 必须是字符串类型")

        # 验证项目根目录是否存在
        if 'project_root' in config:
            project_root = Path(config['project_root'])
            if not project_root.exists():
                self.warnings.append(f"项目根目录不存在: {project_root}")

    def _validate_app_config(self, config: Dict[str, Any]) -> None:
        """验证应用配置"""
        if 'app' not in config:
            self.warnings.append("建议添加 'app' 配置节")
            return

        app_config = config['app']

        # 验证端口配置
        port_fields = ['port', 'api_port']
        for field in port_fields:
            if field in app_config:
                port = app_config[field]
                if not isinstance(port, int):
                    self.errors.append(""app.{field}' 必须是整数类型")
                elif not (1 <= port <= 65535):
                    self.errors.append(""app.{field}' 必须在 1-65535 范围内")

        # 验证URL格式
        url_fields = ['url', 'api_url']
        for field in url_fields:
            if field in app_config:
                url = app_config[field]
                if not isinstance(url, str):
                    self.errors.append(""app.{field}' 必须是字符串类型")
                elif not re.match(r'^https?://', url):
                    self.warnings.append(""app.{field}' 建议使用完整的URL格式")

    def _validate_database_config(self, config: Dict[str, Any]) -> None:
        """验证数据库配置"""
        if 'database' not in config:
            self.errors.append("缺少必需的 'database' 配置节")
            return

        db_config = config['database']

        # 验证必需字段
        required_fields = ['host', 'port', 'username', 'name']
        for field in required_fields:
            if field not in db_config:
                self.errors.append("缺少必需字段 "database.{field}'")

        # 验证端口
        if 'port' in db_config:
            port = db_config['port']
            if not isinstance(port, int):
                self.errors.append("'database.port' 必须是整数类型")
            elif not (1 <= port <= 65535):
                self.errors.append("'database.port' 必须在 1-65535 范围内")

        # 验证URL模板
        if 'url_template' in db_config:
            template = db_config['url_template']
            if not isinstance(template, str):
                self.errors.append("'database.url_template' 必须是字符串类型")
            else:
                # 检查必需的占位符
                required_placeholders = [
                    '{username}',
                    '{password}',
                    '{host}',
                    '{port}',
                    '{database_name}']
                for placeholder in required_placeholders:
                    if placeholder not in template:
                        self.warnings.append(f"数据库URL模板缺少占位符: {placeholder}")

    def _validate_redis_config(self, config: Dict[str, Any]) -> None:
        """验证Redis配置"""
        if 'redis' not in config:
            self.warnings.append("建议添加 'redis' 配置节")
            return

        redis_config = config['redis']

        # 验证端口
        if 'port' in redis_config:
            port = redis_config['port']
            if not isinstance(port, int):
                self.errors.append("'redis.port' 必须是整数类型")
            elif not (1 <= port <= 65535):
                self.errors.append("'redis.port' 必须在 1-65535 范围内")

        # 验证主机
        if 'host' in redis_config and not isinstance(
                redis_config['host'], str):
            self.errors.append("'redis.host' 必须是字符串类型")

    def _validate_security_config(self, config: Dict[str, Any]) -> None:
        """验证安全配置"""
        if 'security' not in config:
            self.warnings.append("建议添加 'security' 配置节")
            return

        security_config = config['security']

        # 验证JWT密钥
        if 'jwt_secret' in security_config:
            jwt_secret = security_config['jwt_secret']
            if not isinstance(jwt_secret, str):
                self.errors.append("'security.jwt_secret' 必须是字符串类型")
            elif len(jwt_secret) < 32:
                self.warnings.append("'security.jwt_secret' 建议至少32个字符")

        # 验证CORS配置
        if 'cors_origin' in security_config:
            cors_origin = security_config['cors_origin']
            if not isinstance(cors_origin, str):
                self.errors.append("'security.cors_origin' 必须是字符串类型")

    def validate_env_file(self, env_path: Union[str, Path]) -> bool:
        """验证环境变量文件

        Args:
            env_path: .env 文件路径

        Returns:
            bool: 验证是否通过
        """
        self.errors.clear()
        self.warnings.clear()

        env_path = Path(env_path)
        if not env_path.exists():
            self.errors.append(f"环境变量文件不存在: {env_path}")
            return False

        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            self.errors.append(f"读取环境变量文件失败: {e}")
            return False

        # 验证环境变量格式
        env_vars = {}
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if '=' not in line:
                self.warnings.append(f"第{line_num}行格式可能有误: {line}")
                continue

            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            # 检查重复定义
            if key in env_vars:
                self.warnings.append("环境变量 "{key}' 重复定义")

            env_vars[key] = value

        # 验证必需的环境变量
        required_vars = [
            'PROJECT_NAME', 'NODE_ENV', 'PORT', 'API_PORT',
            'DB_HOST', 'DB_PORT', 'DB_USER', 'DB_NAME',
            'REDIS_HOST', 'REDIS_PORT', 'JWT_SECRET'
        ]

        for var in required_vars:
            if var not in env_vars:
                self.warnings.append(f"建议添加环境变量: {var}")

        # 验证端口值
        port_vars = ['PORT', 'API_PORT', 'DB_PORT', 'REDIS_PORT']
        for var in port_vars:
            if var in env_vars:
                try:
                    port = int(env_vars[var])
                    if not (1 <= port <= 65535):
                        self.errors.append("环境变量 "{var}' 端口值超出范围: {port}")
                except ValueError:
                    self.errors.append("环境变量 "{var}' 必须是有效的端口号")

        # 输出验证结果
        self._report_validation_results()

        return len(self.errors) == 0

    def get_validation_summary(self) -> Dict[str, Any]:
        """获取验证摘要

        Returns:
            Dict: 包含错误和警告信息的摘要
        """
        return {
            'passed': len(self.errors) == 0,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.errors.copy(),
            'warnings': self.warnings.copy()
        }


def validate_config_file(config_path: Union[str, Path]) -> bool:
    """验证配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        bool: 验证是否通过

    Raises:
        FileNotFoundError: 配置文件不存在
        ConfigValidationError: 配置验证失败
    """
    import yaml

    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigValidationError(f"配置文件格式错误: {e}")

    validator = ConfigValidator()
    return validator.validate_structure_check_config(config)


def main():
    """测试配置验证功能"""
    validator = ConfigValidator()

    # 测试结构检查配置验证
    structure_config_path = Path(
        __file__).parent.parent / "docs" / "03-管理" / "structure_check_config.yaml"

    if structure_config_path.exists():
        print(f"验证结构检查配置文件: {structure_config_path}")
        result = validate_config_file(structure_config_path)

        if result:
            print("✅ 结构检查配置验证通过")
        else:
            print("❌ 结构检查配置验证失败")

        # 显示验证摘要
        summary = validator.get_validation_summary()
        print("\n验证摘要:")
        print(f"- 错误数量: {summary['error_count']}")
        print(f"- 警告数量: {summary['warning_count']}")

        if summary['errors']:
            print("\n错误详情:")
            for error in summary['errors']:
                print(f"  - {error}")

        if summary['warnings']:
            print("\n警告详情:")
            for warning in summary['warnings']:
                print(f"  - {warning}")
    else:
        print(f"结构检查配置文件不存在: {structure_config_path}")

    print("\n" + "=" * 50)

    # 测试项目配置验证
    try:
        project_config = get_config()
        print(f"验证项目配置: {PROJECT_CONFIG_PATH}")
        result = validator.validate_project_config(project_config)

        if result:
            print("✅ 项目配置验证通过")
        else:
            print("❌ 项目配置验证失败")

        # 显示验证摘要
        summary = validator.get_validation_summary()
        print("\n验证摘要:")
        print(f"- 错误数量: {summary['error_count']}")
        print(f"- 警告数量: {summary['warning_count']}")

        if summary['errors']:
            print("\n错误详情:")
            for error in summary['errors']:
                print(f"  - {error}")

        if summary['warnings']:
            print("\n警告详情:")
            for warning in summary['warnings']:
                print(f"  - {warning}")
    except Exception as e:
        print(f"加载项目配置失败: {e}")

    print("\n" + "=" * 50)

    # 测试环境变量文件验证
    env_path = Path(__file__).parent.parent / "docs" / "03-管理" / ".env"

    if env_path.exists():
        print(f"验证环境变量文件: {env_path}")
        result = validator.validate_env_file(env_path)

        if result:
            print("✅ 环境变量文件验证通过")
        else:
            print("❌ 环境变量文件验证失败")

        # 显示验证摘要
        summary = validator.get_validation_summary()
        print("\n验证摘要:")
        print(f"- 错误数量: {summary['error_count']}")
        print(f"- 警告数量: {summary['warning_count']}")

        if summary['errors']:
            print("\n错误详情:")
            for error in summary['errors']:
                print(f"  - {error}")

        if summary['warnings']:
            print("\n警告详情:")
            for warning in summary['warnings']:
                print(f"  - {warning}")
    else:
        print(f"环境变量文件不存在: {env_path}")


if __name__ == '__main__':
    # 测试配置验证
    try:
        main()
    except Exception as e:
        error_handler.handle_error(ValidationError(f"验证过程中发生错误: {e}"))
