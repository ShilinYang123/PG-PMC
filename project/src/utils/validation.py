#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证工具模块
提供各种数据验证功能，包括项目管理相关的验证
"""

import ipaddress
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

from src.utils.logger import get_logger


class ValidationLevel(Enum):
    """验证级别"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """验证结果"""

    is_valid: bool
    level: ValidationLevel
    message: str
    field: str = ""
    value: Any = None
    suggestion: str = ""

    def __str__(self) -> str:
        return f"[{self.level.value.upper()}] {self.field}: {self.message}"


class ValidationRule:
    """验证规则基类"""

    def __init__(
        self,
        name: str,
        message: str = "",
        level: ValidationLevel = ValidationLevel.ERROR,
    ):
        self.name = name
        self.message = message or f"验证规则 {name} 失败"
        self.level = level

    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        """执行验证

        Args:
            value: 待验证的值
            context: 验证上下文

        Returns:
            ValidationResult: 验证结果
        """
        raise NotImplementedError


class RequiredRule(ValidationRule):
    """必需字段验证规则"""

    def __init__(self):
        super().__init__("required", "字段为必需项")

    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        is_valid = value is not None and value != ""
        return ValidationResult(
            is_valid=is_valid,
            level=self.level,
            message=self.message if not is_valid else "验证通过",
            value=value,
        )


class TypeRule(ValidationRule):
    """类型验证规则"""

    def __init__(self, expected_type: type):
        self.expected_type = expected_type
        super().__init__("type", f"字段类型必须为 {expected_type.__name__}")

    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        is_valid = isinstance(value, self.expected_type)
        return ValidationResult(
            is_valid=is_valid,
            level=self.level,
            message=self.message if not is_valid else "验证通过",
            value=value,
        )


class RangeRule(ValidationRule):
    """数值范围验证规则"""

    def __init__(
        self, min_value: Optional[float] = None, max_value: Optional[float] = None
    ):
        self.min_value = min_value
        self.max_value = max_value

        message_parts = []
        if min_value is not None:
            message_parts.append(f"最小值 {min_value}")
        if max_value is not None:
            message_parts.append(f"最大值 {max_value}")

        message = f"数值必须在范围内: {', '.join(message_parts)}"
        super().__init__("range", message)

    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        if not isinstance(value, (int, float)):
            return ValidationResult(
                is_valid=False, level=self.level, message="值必须是数字", value=value
            )

        is_valid = True
        if self.min_value is not None and value < self.min_value:
            is_valid = False
        if self.max_value is not None and value > self.max_value:
            is_valid = False

        return ValidationResult(
            is_valid=is_valid,
            level=self.level,
            message=self.message if not is_valid else "验证通过",
            value=value,
        )


class LengthRule(ValidationRule):
    """长度验证规则"""

    def __init__(
        self, min_length: Optional[int] = None, max_length: Optional[int] = None
    ):
        self.min_length = min_length
        self.max_length = max_length

        message_parts = []
        if min_length is not None:
            message_parts.append(f"最小长度 {min_length}")
        if max_length is not None:
            message_parts.append(f"最大长度 {max_length}")

        message = f"长度必须在范围内: {', '.join(message_parts)}"
        super().__init__("length", message)

    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        if not hasattr(value, "__len__"):
            return ValidationResult(
                is_valid=False,
                level=self.level,
                message="值必须有长度属性",
                value=value,
            )

        length = len(value)
        is_valid = True

        if self.min_length is not None and length < self.min_length:
            is_valid = False
        if self.max_length is not None and length > self.max_length:
            is_valid = False

        return ValidationResult(
            is_valid=is_valid,
            level=self.level,
            message=self.message if not is_valid else "验证通过",
            value=value,
        )


class PatternRule(ValidationRule):
    """正则表达式验证规则"""

    def __init__(self, pattern: str, message: str = ""):
        self.pattern = re.compile(pattern)
        message = message or f"值必须匹配模式: {pattern}"
        super().__init__("pattern", message)

    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False, level=self.level, message="值必须是字符串", value=value
            )

        is_valid = bool(self.pattern.match(value))
        return ValidationResult(
            is_valid=is_valid,
            level=self.level,
            message=self.message if not is_valid else "验证通过",
            value=value,
        )


class EmailRule(ValidationRule):
    """邮箱验证规则"""

    def __init__(self):
        self.pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        super().__init__("email", "邮箱格式无效")

    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                level=self.level,
                message="邮箱必须是字符串",
                value=value,
            )

        is_valid = bool(self.pattern.match(value))
        return ValidationResult(
            is_valid=is_valid,
            level=self.level,
            message=self.message if not is_valid else "验证通过",
            value=value,
        )


class URLRule(ValidationRule):
    """URL验证规则"""

    def __init__(self):
        super().__init__("url", "URL格式无效")

    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False, level=self.level, message="URL必须是字符串", value=value
            )

        try:
            result = urlparse(value)
            is_valid = all([result.scheme, result.netloc])
        except Exception:
            is_valid = False

        return ValidationResult(
            is_valid=is_valid,
            level=self.level,
            message=self.message if not is_valid else "验证通过",
            value=value,
        )


class IPAddressRule(ValidationRule):
    """IP地址验证规则"""

    def __init__(self, version: Optional[int] = None):
        self.version = version  # 4 for IPv4, 6 for IPv6, None for both
        message = "IP地址格式无效"
        if version:
            message += f" (IPv{version})"
        super().__init__("ip_address", message)

    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                level=self.level,
                message="IP地址必须是字符串",
                value=value,
            )

        try:
            ip = ipaddress.ip_address(value)
            if self.version is None:
                is_valid = True
            elif self.version == 4:
                is_valid = isinstance(ip, ipaddress.IPv4Address)
            elif self.version == 6:
                is_valid = isinstance(ip, ipaddress.IPv6Address)
            else:
                is_valid = False
        except Exception:
            is_valid = False

        return ValidationResult(
            is_valid=is_valid,
            level=self.level,
            message=self.message if not is_valid else "验证通过",
            value=value,
        )


class FilePathRule(ValidationRule):
    """文件路径验证规则"""

    def __init__(self, must_exist: bool = False, must_be_file: bool = False):
        self.must_exist = must_exist
        self.must_be_file = must_be_file
        super().__init__("file_path", "文件路径无效")

    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        if not isinstance(value, (str, Path)):
            return ValidationResult(
                is_valid=False,
                level=self.level,
                message="文件路径必须是字符串或Path对象",
                value=value,
            )

        path = Path(value)

        if self.must_exist and not path.exists():
            return ValidationResult(
                is_valid=False,
                level=self.level,
                message=f"路径不存在: {path}",
                value=value,
            )

        if self.must_be_file and path.exists() and not path.is_file():
            return ValidationResult(
                is_valid=False,
                level=self.level,
                message=f"路径不是文件: {path}",
                value=value,
            )

        return ValidationResult(
            is_valid=True, level=self.level, message="验证通过", value=value
        )


class CustomRule(ValidationRule):
    """自定义验证规则"""

    def __init__(self, validator_func: Callable[[Any], bool], message: str):
        self.validator_func = validator_func
        super().__init__("custom", message)

    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        try:
            is_valid = self.validator_func(value)
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                level=self.level,
                message=f"验证函数执行失败: {e}",
                value=value,
            )

        return ValidationResult(
            is_valid=is_valid,
            level=self.level,
            message=self.message if not is_valid else "验证通过",
            value=value,
        )


class Validator:
    """验证器

    用于组合多个验证规则并执行验证
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.rules: Dict[str, List[ValidationRule]] = {}

    def add_rule(self, field: str, rule: ValidationRule) -> "Validator":
        """添加验证规则

        Args:
            field: 字段名
            rule: 验证规则

        Returns:
            Validator: 返回自身以支持链式调用
        """
        if field not in self.rules:
            self.rules[field] = []
        self.rules[field].append(rule)
        return self

    def validate(
        self, data: Dict[str, Any], context: Dict[str, Any] = None
    ) -> List[ValidationResult]:
        """执行验证

        Args:
            data: 待验证的数据
            context: 验证上下文

        Returns:
            List[ValidationResult]: 验证结果列表
        """
        results = []
        context = context or {}

        try:
            for field, rules in self.rules.items():
                value = data.get(field)

                for rule in rules:
                    result = rule.validate(value, context)
                    result.field = field
                    results.append(result)

                    # 如果是必需字段验证失败，跳过该字段的其他验证
                    if isinstance(rule, RequiredRule) and not result.is_valid:
                        break

            return results

        except Exception as e:
            self.logger.error(f"验证过程出错: {e}")
            return [
                ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message=f"验证过程出错: {e}",
                    field="_system",
                )
            ]

    def is_valid(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> bool:
        """检查数据是否有效

        Args:
            data: 待验证的数据
            context: 验证上下文

        Returns:
            bool: 是否有效
        """
        results = self.validate(data, context)
        return all(result.is_valid for result in results)

    def get_errors(
        self, data: Dict[str, Any], context: Dict[str, Any] = None
    ) -> List[ValidationResult]:
        """获取验证错误

        Args:
            data: 待验证的数据
            context: 验证上下文

        Returns:
            List[ValidationResult]: 错误列表
        """
        results = self.validate(data, context)
        return [result for result in results if not result.is_valid]

    def clear_rules(self, field: Optional[str] = None) -> "Validator":
        """清除验证规则

        Args:
            field: 字段名，如果为None则清除所有规则

        Returns:
            Validator: 返回自身以支持链式调用
        """
        if field is None:
            self.rules.clear()
        elif field in self.rules:
            del self.rules[field]
        return self


class GeometryValidator:
    """几何参数验证器"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def validate_dimension(
        self, value: float, min_value: float = 0.1, max_value: float = 10000.0
    ) -> ValidationResult:
        """验证尺寸参数

        Args:
            value: 尺寸值（毫米）
            min_value: 最小值
            max_value: 最大值

        Returns:
            ValidationResult: 验证结果
        """
        try:
            if not isinstance(value, (int, float)):
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message="尺寸值必须是数字",
                    value=value,
                )

            if value <= 0:
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message="尺寸值必须大于0",
                    value=value,
                )

            if value < min_value:
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    message=f"尺寸值 {value}mm 可能过小，建议不小于 {min_value}mm",
                    value=value,
                    suggestion=f"建议使用不小于 {min_value}mm 的尺寸",
                )

            if value > max_value:
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    message=f"尺寸值 {value}mm 可能过大，建议不超过 {max_value}mm",
                    value=value,
                    suggestion=f"建议使用不超过 {max_value}mm 的尺寸",
                )

            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.INFO,
                message="尺寸验证通过",
                value=value,
            )

        except Exception as e:
            self.logger.error(f"验证尺寸参数失败: {e}")
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"验证过程出错: {e}",
                value=value,
            )

    def validate_angle(self, value: float) -> ValidationResult:
        """验证角度参数

        Args:
            value: 角度值（度）

        Returns:
            ValidationResult: 验证结果
        """
        try:
            if not isinstance(value, (int, float)):
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message="角度值必须是数字",
                    value=value,
                )

            # 标准化角度到0-360范围
            normalized_angle = value % 360

            if normalized_angle < 0:
                normalized_angle += 360

            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.INFO,
                message="角度验证通过",
                value=normalized_angle,
            )

        except Exception as e:
            self.logger.error(f"验证角度参数失败: {e}")
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"验证过程出错: {e}",
                value=value,
            )

    def validate_coordinate(
        self, x: float, y: float, z: float = 0.0
    ) -> ValidationResult:
        """验证坐标参数

        Args:
            x: X坐标
            y: Y坐标
            z: Z坐标

        Returns:
            ValidationResult: 验证结果
        """
        try:
            coords = [x, y, z]

            for i, coord in enumerate(coords):
                if not isinstance(coord, (int, float)):
                    return ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.ERROR,
                        message=f"坐标值必须是数字: {'XYZ'[i]}={coord}",
                        value=(x, y, z),
                    )

            # 检查坐标是否在合理范围内
            max_coord = 100000.0  # 100米
            for i, coord in enumerate(coords):
                if abs(coord) > max_coord:
                    return ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.WARNING,
                        message=f"坐标值可能过大: {'XYZ'[i]}={coord}mm",
                        value=(x, y, z),
                        suggestion=f"建议坐标值不超过 ±{max_coord}mm",
                    )

            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.INFO,
                message="坐标验证通过",
                value=(x, y, z),
            )

        except Exception as e:
            self.logger.error(f"验证坐标参数失败: {e}")
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"验证过程出错: {e}",
                value=(x, y, z),
            )

    def validate_cylinder_params(
        self, diameter: float, height: float
    ) -> List[ValidationResult]:
        """验证圆柱体参数

        Args:
            diameter: 直径
            height: 高度

        Returns:
            List[ValidationResult]: 验证结果列表
        """
        results = []

        # 验证直径
        diameter_result = self.validate_dimension(diameter)
        diameter_result.field = "diameter"
        results.append(diameter_result)

        # 验证高度
        height_result = self.validate_dimension(height)
        height_result.field = "height"
        results.append(height_result)

        # 验证比例关系
        if diameter_result.is_valid and height_result.is_valid:
            ratio = height / diameter
            if ratio > 100:
                results.append(
                    ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.WARNING,
                        message=f"高径比过大: {ratio:.1f}，可能导致不稳定的几何体",
                        field="ratio",
                        value=ratio,
                        suggestion="建议高径比不超过100",
                    )
                )
            elif ratio < 0.01:
                results.append(
                    ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.WARNING,
                        message=f"高径比过小: {ratio:.3f}，可能导致过薄的几何体",
                        field="ratio",
                        value=ratio,
                        suggestion="建议高径比不小于0.01",
                    )
                )

        return results

    def validate_box_params(
        self, length: float, width: float, height: float
    ) -> List[ValidationResult]:
        """验证长方体参数

        Args:
            length: 长度
            width: 宽度
            height: 高度

        Returns:
            List[ValidationResult]: 验证结果列表
        """
        results = []

        # 验证各个尺寸
        length_result = self.validate_dimension(length)
        length_result.field = "length"
        results.append(length_result)

        width_result = self.validate_dimension(width)
        width_result.field = "width"
        results.append(width_result)

        height_result = self.validate_dimension(height)
        height_result.field = "height"
        results.append(height_result)

        # 验证尺寸比例
        if all(r.is_valid for r in results):
            dimensions = [length, width, height]
            max_dim = max(dimensions)
            min_dim = min(dimensions)

            if max_dim / min_dim > 1000:
                results.append(
                    ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.WARNING,
                        message=f"尺寸比例过大: {max_dim/min_dim:.1f}，可能导致显示或计算问题",
                        field="ratio",
                        value=max_dim / min_dim,
                        suggestion="建议最大尺寸与最小尺寸的比例不超过1000",
                    )
                )

        return results


# 全局验证器实例
geometry_validator = GeometryValidator()


# 项目管理相关验证函数
def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """验证手机号格式"""
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """验证必填字段"""
    missing_fields = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    return missing_fields

def validate_project_name(project_name: str) -> bool:
    """验证项目名称
    
    规则：
    - 长度在2-50个字符之间
    - 不能包含特殊字符（除了中文、英文、数字、下划线、短横线）
    - 不能以点开头或结尾
    """
    if not project_name or not isinstance(project_name, str):
        return False
    
    # 长度检查
    if len(project_name) < 2 or len(project_name) > 50:
        return False
    
    # 字符检查：允许中文、英文、数字、下划线、短横线
    pattern = r'^[\u4e00-\u9fa5a-zA-Z0-9_-]+$'
    if not re.match(pattern, project_name):
        return False
    
    # 不能以点开头或结尾
    if project_name.startswith('.') or project_name.endswith('.'):
        return False
    
    return True

def validate_project_id(project_id: str) -> bool:
    """验证项目ID
    
    规则：
    - 8位字符串
    - 只包含字母和数字
    """
    if not project_id or not isinstance(project_id, str):
        return False
    
    # 长度检查
    if len(project_id) != 8:
        return False
    
    # 字符检查：只允许字母和数字
    pattern = r'^[a-zA-Z0-9]{8}$'
    return bool(re.match(pattern, project_id))

def validate_project_type(project_type: str) -> bool:
    """验证项目类型
    
    允许的项目类型
    """
    valid_types = [
        '小家电产品开发', '生产线优化', '供应链改进', 
        '质量管理', '成本控制', '技术改进', '其他'
    ]
    return project_type in valid_types

def validate_project_status(status: str) -> bool:
    """验证项目状态"""
    valid_statuses = ['active', 'archived', 'completed', 'suspended']
    return status in valid_statuses

def sanitize_filename(filename: str) -> str:
    """清理文件名，移除不安全字符"""
    # 移除或替换不安全字符
    unsafe_chars = r'[<>:"/\|?*]'
    safe_filename = re.sub(unsafe_chars, '_', filename)
    
    # 移除前后空格和点
    safe_filename = safe_filename.strip(' .')
    
    # 确保不为空
    if not safe_filename:
        safe_filename = 'unnamed'
    
    return safe_filename


# 预定义的验证器
def create_creo_config_validator() -> Validator:
    """创建Creo配置验证器"""
    validator = Validator()

    # Creo安装路径
    validator.add_rule("creo_install_path", RequiredRule())
    validator.add_rule("creo_install_path", FilePathRule(must_exist=True))

    # 工作目录
    validator.add_rule("working_directory", RequiredRule())
    validator.add_rule("working_directory", FilePathRule())

    # 连接超时
    validator.add_rule("connection_timeout", TypeRule(int))
    validator.add_rule("connection_timeout", RangeRule(min_value=1, max_value=300))

    # 端口号
    validator.add_rule("port", TypeRule(int))
    validator.add_rule("port", RangeRule(min_value=1024, max_value=65535))

    return validator


def create_ai_config_validator() -> Validator:
    """创建AI配置验证器"""
    validator = Validator()

    # API密钥
    validator.add_rule("api_key", RequiredRule())
    validator.add_rule("api_key", LengthRule(min_length=10))

    # API URL
    validator.add_rule("api_url", URLRule())

    # 模型名称
    validator.add_rule("model_name", RequiredRule())
    validator.add_rule("model_name", LengthRule(min_length=1, max_length=100))

    # 温度参数
    validator.add_rule("temperature", TypeRule(float))
    validator.add_rule("temperature", RangeRule(min_value=0.0, max_value=2.0))

    # 最大令牌数
    validator.add_rule("max_tokens", TypeRule(int))
    validator.add_rule("max_tokens", RangeRule(min_value=1, max_value=100000))

    return validator
