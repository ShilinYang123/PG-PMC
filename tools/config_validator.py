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
from config_loader import load_yaml_config
from exceptions import ValidationError, ErrorHandler
from config_loader import get_config, PROJECT_CONFIG_PATH

# 日志配置移除（避免重复配置）
# logging.basicConfig 已在主程序中配置
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
                            f"file_types.{section} 中的扩展名必须是字符串")
                    elif not ext.startswith('.'):
                        self.errors.append(f"扩展名 '{ext}' 必须以点号开头")

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
                self.errors.append(f"'logging.level' 必须是以下值之一: {valid_levels}")

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
                        self.errors.append(f"命名规则 '{category}' 必须是字符串类型")
                    else:
                        # 验证正则表达式
                        try:
                            re.compile(pattern)
                        except re.error as e:
                            self.errors.append(
                                f"命名规则 '{category}' 的正则表达式无效: {e}")

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
                self.errors.append(f"'rules.{field}' 必须是布尔类型")

    def _validate_rules_config(self, config: Dict[str, Any]) -> None:
        """验证规则配置"""
        if 'rules' not in config:
            self.warnings.append("建议添加 'rules' 配置节")
            return

        rules_config = config['rules']

        # 验证validation子节
        if 'validation' in rules_config:
            validation = rules_config['validation']
            bool_fields = ['strict_mode', 'allow_empty_files', 'require_documentation', 'enforce_naming_conventions']
            for field in bool_fields:
                if field in validation and not isinstance(validation[field], bool):
                    self.errors.append(f"'rules.validation.{field}' 必须是布尔类型")

        # 验证code_quality子节
        if 'code_quality' in rules_config:
            quality = rules_config['code_quality']
            int_fields = ['max_line_length', 'max_function_length', 'max_file_length']
            for field in int_fields:
                if field in quality:
                    if not isinstance(quality[field], int):
                        self.errors.append(f"'rules.code_quality.{field}' 必须是整数类型")
                    elif quality[field] <= 0:
                        self.errors.append(f"'rules.code_quality.{field}' 必须是正整数")

        # 验证security子节
        if 'security' in rules_config:
            security = rules_config['security']
            bool_fields = ['scan_for_secrets', 'require_https', 'validate_inputs', 'sanitize_outputs']
            for field in bool_fields:
                if field in security and not isinstance(security[field], bool):
                    self.errors.append(f"'rules.security.{field}' 必须是布尔类型")

        # 验证compliance子节
        if 'compliance' in rules_config:
            compliance = rules_config['compliance']
            bool_fields = ['license_check', 'dependency_audit', 'vulnerability_scan']
            for field in bool_fields:
                if field in compliance and not isinstance(compliance[field], bool):
                    self.errors.append(f"'rules.compliance.{field}' 必须是布尔类型")

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

        # 验证版本信息
        self._validate_version(config)

        # 验证项目基本信息
        self._validate_project_info(config)

        # 验证应用配置
        self._validate_app_config(config)

        # 验证性能配置
        self._validate_performance_config(config)

        # 验证文件类型配置
        self._validate_file_types_config(config)

        # 验证日志配置
        self._validate_logging_config(config)

        # 验证规则配置
        self._validate_rules_config(config)

        # 验证数据库配置
        self._validate_database_config(config)

        # 验证Redis配置
        self._validate_redis_config(config)

        # 验证安全配置
        self._validate_security_config(config)

        # 验证环境变量配置（不清空错误和警告列表）
        if 'environment' in config:
            self._validate_environment_variables(config['environment'])

        # 输出验证结果
        self._report_validation_results()

        return len(self.errors) == 0

    def _validate_project_info(self, config: Dict[str, Any]) -> None:
        """验证项目基本信息"""
        required_fields = ['project_name', 'project_root']
        for field in required_fields:
            if field not in config:
                self.errors.append(f"缺少必需字段 '{field}'")
            elif not isinstance(config[field], str):
                self.errors.append(f"'{field}' 必须是字符串类型")

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
                    self.errors.append(f"'app.{field}' 必须是整数类型")
                elif not (1 <= port <= 65535):
                    self.errors.append(f"'app.{field}' 必须在 1-65535 范围内")

        # 验证URL格式
        url_fields = ['url', 'api_url']
        for field in url_fields:
            if field in app_config:
                url = app_config[field]
                if not isinstance(url, str):
                    self.errors.append(f"'app.{field}' 必须是字符串类型")
                elif not re.match(r'^https?://', url):
                    self.warnings.append(f"'app.{field}' 建议使用完整的URL格式")

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
                self.errors.append(f"缺少必需字段 'database.{field}'")

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
        # 检查顶层或environment节下的redis配置
        redis_config = None
        if 'redis' in config:
            redis_config = config['redis']
        elif 'environment' in config and 'redis' in config['environment']:
            redis_config = config['environment']['redis']
        
        if redis_config is None:
            self.warnings.append("建议添加 'redis' 配置节")
            return

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
        # 检查顶层或environment节下的security配置
        security_config = None
        if 'security' in config:
            security_config = config['security']
        elif 'environment' in config and 'security' in config['environment']:
            security_config = config['environment']['security']
        
        if security_config is None:
            self.warnings.append("建议添加 'security' 配置节")
            return

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
                self.warnings.append(f"环境变量 '{key}' 重复定义")

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
                        self.errors.append(f"环境变量 '{var}' 端口值超出范围: {port}")
                except ValueError:
                    self.errors.append(f"环境变量 '{var}' 必须是有效的端口号")

        # 输出验证结果
        self._report_validation_results()

        return len(self.errors) == 0

    def validate_environment_config(self, config: Dict[str, Any]) -> bool:
        """验证 project_config.yaml 中的环境变量配置

        Args:
            config: 项目配置字典

        Returns:
            bool: 验证是否通过
        """
        self.errors.clear()
        self.warnings.clear()

        if 'environment' not in config:
            self.errors.append("缺少 'environment' 配置节")
            return False

        env_config = config['environment']

        # 验证应用配置
        if 'app' in env_config:
            app_config = env_config['app']
            required_app_fields = ['name', 'version', 'port', 'api_port']
            for field in required_app_fields:
                if field not in app_config:
                    self.warnings.append(f"建议在 environment.app 中添加 '{field}' 配置")
            
            # 验证端口配置
            for port_field in ['port', 'api_port']:
                if port_field in app_config:
                    try:
                        port = int(app_config[port_field])
                        if not (1 <= port <= 65535):
                            self.errors.append(f"environment.app.{port_field} 端口值超出范围: {port}")
                    except (ValueError, TypeError):
                        self.errors.append(f"environment.app.{port_field} 必须是有效的端口号")

        # 验证数据库配置
        if 'database' in env_config:
            db_config = env_config['database']
            required_db_fields = ['host', 'port', 'name', 'user']
            for field in required_db_fields:
                if field not in db_config:
                    self.warnings.append(f"建议在 environment.database 中添加 '{field}' 配置")
            
            # 验证数据库端口
            if 'port' in db_config:
                try:
                    port = int(db_config['port'])
                    if not (1 <= port <= 65535):
                        self.errors.append(f"environment.database.port 端口值超出范围: {port}")
                except (ValueError, TypeError):
                    self.errors.append("environment.database.port 必须是有效的端口号")

        # 验证Redis配置
        if 'redis' in env_config:
            redis_config = env_config['redis']
            required_redis_fields = ['host', 'port', 'db']
            for field in required_redis_fields:
                if field not in redis_config:
                    self.warnings.append(f"建议在 environment.redis 中添加 '{field}' 配置")
            
            # 验证Redis端口
            if 'port' in redis_config:
                try:
                    port = int(redis_config['port'])
                    if not (1 <= port <= 65535):
                        self.errors.append(f"environment.redis.port 端口值超出范围: {port}")
                except (ValueError, TypeError):
                    self.errors.append("environment.redis.port 必须是有效的端口号")

        # 验证安全配置
        if 'security' in env_config:
            security_config = env_config['security']
            required_security_fields = ['session_secret', 'jwt_secret']
            for field in required_security_fields:
                if field not in security_config:
                    self.warnings.append(f"建议在 environment.security 中添加 '{field}' 配置")
                elif isinstance(security_config[field], str):
                    # 检查是否使用了默认的不安全密钥
                    if 'change-this' in security_config[field].lower() or len(security_config[field]) < 32:
                        self.warnings.append(f"environment.security.{field} 建议使用更安全的密钥")

        # 输出验证结果
        self._report_validation_results()

        return len(self.errors) == 0

    def _validate_environment_variables(self, env_config: Dict[str, Any]) -> None:
        """验证环境变量配置（内部方法，不清空错误和警告列表）

        Args:
            env_config: 环境变量配置字典
        """
        # 验证应用配置
        if 'app' in env_config:
            app_config = env_config['app']
            required_app_fields = ['name', 'version', 'port', 'api_port']
            for field in required_app_fields:
                if field not in app_config:
                    self.warnings.append(f"建议在 environment.app 中添加 '{field}' 配置")
            
            # 验证端口配置
            for port_field in ['port', 'api_port']:
                if port_field in app_config:
                    try:
                        port = int(app_config[port_field])
                        if not (1 <= port <= 65535):
                            self.errors.append(f"environment.app.{port_field} 端口值超出范围: {port}")
                    except (ValueError, TypeError):
                        self.errors.append(f"environment.app.{port_field} 必须是有效的端口号")

        # 验证数据库配置
        if 'database' in env_config:
            db_config = env_config['database']
            required_db_fields = ['host', 'port', 'name', 'user']
            for field in required_db_fields:
                if field not in db_config:
                    self.warnings.append(f"建议在 environment.database 中添加 '{field}' 配置")
            
            # 验证数据库端口
            if 'port' in db_config:
                try:
                    port = int(db_config['port'])
                    if not (1 <= port <= 65535):
                        self.errors.append(f"environment.database.port 端口值超出范围: {port}")
                except (ValueError, TypeError):
                    self.errors.append("environment.database.port 必须是有效的端口号")

        # 验证Redis配置
        if 'redis' in env_config:
            redis_config = env_config['redis']
            required_redis_fields = ['host', 'port', 'db']
            for field in required_redis_fields:
                if field not in redis_config:
                    self.warnings.append(f"建议在 environment.redis 中添加 '{field}' 配置")
            
            # 验证Redis端口
            if 'port' in redis_config:
                try:
                    port = int(redis_config['port'])
                    if not (1 <= port <= 65535):
                        self.errors.append(f"environment.redis.port 端口值超出范围: {port}")
                except (ValueError, TypeError):
                    self.errors.append("environment.redis.port 必须是有效的端口号")

        # 验证安全配置
        if 'security' in env_config:
            security_config = env_config['security']
            required_security_fields = ['session_secret', 'jwt_secret']
            for field in required_security_fields:
                if field not in security_config:
                    self.warnings.append(f"建议在 environment.security 中添加 '{field}' 配置")
                elif isinstance(security_config[field], str):
                    # 检查是否使用了默认的不安全密钥
                    if 'change-this' in security_config[field].lower() or len(security_config[field]) < 32:
                        self.warnings.append(f"environment.security.{field} 建议使用更安全的密钥")

    def validate_structure_check_config(self, config: Dict[str, Any]) -> bool:
        """验证结构检查配置

        Args:
            config: 结构检查配置字典

        Returns:
            bool: 验证是否通过
        """
        self.errors.clear()
        self.warnings.clear()

        # 验证版本信息
        self._validate_version(config)
        # 验证性能配置
        self._validate_performance_config(config)
        # 验证文件类型配置
        self._validate_file_types_config(config)
        # 验证日志配置
        self._validate_logging_config(config)
        # 验证规则配置
        self._validate_rules_config(config)

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
    """验证结构检查配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        bool: 验证是否通过
    """
    try:
        # 强制重新加载配置，避免缓存问题
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        validator = ConfigValidator()
        # 验证结构检查配置（检查structure_check节）
        if 'structure_check' in config:
            sc_config = config['structure_check']
            return validator.validate_structure_check_config(sc_config)
        else:
            validator.warnings.append("缺少 'structure_check' 配置节")
            validator._report_validation_results()
            return False
    except Exception as e:
        logger.error(f"验证结构检查配置文件失败: {e}")
        return False


def validate_project_config_file(config_path: Union[str, Path]) -> bool:
    """验证项目配置文件

    Args:
        config_path: 项目配置文件路径

    Returns:
        bool: 验证是否通过
    """
    try:
        # 强制重新加载配置文件，不使用缓存
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        

        
        validator = ConfigValidator()
        return validator.validate_project_config(config)
    except Exception as e:
        error_handler.handle_error(e, "项目配置文件验证失败")
        return False


def main():
    """主函数 - 验证默认配置文件"""
    try:
        # 验证结构检查配置
        logger.info("开始验证结构检查配置...")
        if validate_config_file(PROJECT_CONFIG_PATH):
            logger.info("结构检查配置验证通过")
        else:
            logger.error("结构检查配置验证失败")

        # 验证项目配置
        project_config_path = Path(PROJECT_CONFIG_PATH).parent / "project_config.yaml"
        if project_config_path.exists():
            logger.info("开始验证项目配置...")
            if validate_project_config_file(project_config_path):
                logger.info("项目配置验证通过")
            else:
                logger.error("项目配置验证失败")
        else:
            logger.warning(f"项目配置文件不存在: {project_config_path}")

        # 环境变量验证已禁用 - 环境变量已整合到 project_config.yaml 中
        # env_file_path = Path(PROJECT_CONFIG_PATH).parent / ".env"
        # if env_file_path.exists():
        #     logger.info("开始验证环境变量文件...")
        #     validator = ConfigValidator()
        #     if validator.validate_env_file(env_file_path):
        #         logger.info("环境变量文件验证通过")
        #     else:
        #         logger.error("环境变量文件验证失败")
        # else:
        #     logger.warning(f"环境变量文件不存在: {env_file_path}")
        logger.info("环境变量配置已整合到 project_config.yaml 中，跳过 .env 文件验证")

    except Exception as e:
        error_handler.handle_error(e, "配置验证过程中发生错误")


if __name__ == "__main__":
    main()
