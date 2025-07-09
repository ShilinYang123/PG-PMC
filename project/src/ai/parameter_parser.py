#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 参数解析器
"""

# import json
# import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.utils.logger import get_logger


class ParameterType(Enum):
    """参数类型"""

    DIMENSION = "dimension"  # 尺寸参数
    ANGLE = "angle"  # 角度参数
    COUNT = "count"  # 数量参数
    MATERIAL = "material"  # 材料参数
    BOOLEAN = "boolean"  # 布尔参数
    STRING = "string"  # 字符串参数
    COORDINATE = "coordinate"  # 坐标参数
    VECTOR = "vector"  # 向量参数


class UnitType(Enum):
    """单位类型"""

    LENGTH = "length"  # 长度单位
    ANGLE = "angle"  # 角度单位
    AREA = "area"  # 面积单位
    VOLUME = "volume"  # 体积单位
    MASS = "mass"  # 质量单位
    FORCE = "force"  # 力单位
    PRESSURE = "pressure"  # 压力单位
    TEMPERATURE = "temperature"  # 温度单位


@dataclass
class ParameterConstraint:
    """参数约束"""

    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None  # 正则表达式模式
    required: bool = False
    description: str = ""

    def validate(self, value: Any) -> Tuple[bool, str]:
        """验证参数值

        Args:
            value: 参数值

        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            # 检查必需参数
            if self.required and (value is None or value == ""):
                return False, "参数为必需项"

            if value is None:
                return True, ""

            # 检查数值范围
            if isinstance(value, (int, float)):
                if self.min_value is not None and value < self.min_value:
                    return False, f"值 {value} 小于最小值 {self.min_value}"
                if self.max_value is not None and value > self.max_value:
                    return False, f"值 {value} 大于最大值 {self.max_value}"

            # 检查允许的值
            if self.allowed_values is not None and value not in self.allowed_values:
                return False, f"值 {value} 不在允许的值列表中: {self.allowed_values}"

            # 检查模式匹配
            if self.pattern and isinstance(value, str):
                if not re.match(self.pattern, value):
                    return False, f"值 {value} 不匹配模式 {self.pattern}"

            return True, ""

        except Exception as e:
            return False, f"验证过程出错: {e}"


@dataclass
class ParsedParameter:
    """解析后的参数"""

    name: str
    value: Any
    original_value: str
    parameter_type: ParameterType
    unit: str = ""
    unit_type: Optional[UnitType] = None
    confidence: float = 0.0
    source_text: str = ""
    constraints: Optional[ParameterConstraint] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.constraints:
            is_valid, error_msg = self.constraints.validate(self.value)
            if not is_valid:
                raise ValueError(f"参数 {self.name} 验证失败: {error_msg}")


class ParameterParser:
    """参数解析器

    负责从自然语言文本中提取和解析各种类型的参数
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

        # 单位转换表
        self.unit_conversions = {
            UnitType.LENGTH: {
                "mm": 1.0,
                "毫米": 1.0,
                "cm": 10.0,
                "厘米": 10.0,
                "m": 1000.0,
                "米": 1000.0,
                "km": 1000000.0,
                "千米": 1000000.0,
                "in": 25.4,
                "英寸": 25.4,
                "ft": 304.8,
                "英尺": 304.8,
                "yd": 914.4,
                "码": 914.4,
            },
            UnitType.ANGLE: {
                "度": 1.0,
                "°": 1.0,
                "deg": 1.0,
                "弧度": 57.2958,
                "rad": 57.2958,
                "转": 360.0,
                "圈": 360.0,
            },
            UnitType.AREA: {
                "mm²": 1.0,
                "平方毫米": 1.0,
                "cm²": 100.0,
                "平方厘米": 100.0,
                "m²": 1000000.0,
                "平方米": 1000000.0,
            },
            UnitType.VOLUME: {
                "mm³": 1.0,
                "立方毫米": 1.0,
                "cm³": 1000.0,
                "立方厘米": 1000.0,
                "m³": 1000000000.0,
                "立方米": 1000000000.0,
                "l": 1000000.0,
                "升": 1000000.0,
            },
        }

        # 参数模式定义
        self.parameter_patterns = {
            # 尺寸参数
            "diameter": {
                "patterns": [
                    r"直径[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|毫米|厘米|米|in|英寸)?",
                    r"φ\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|毫米|厘米|米|in|英寸)?",
                    r"diameter[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|in)?",
                ],
                "type": ParameterType.DIMENSION,
                "unit_type": UnitType.LENGTH,
                "default_unit": "mm",
            },
            "radius": {
                "patterns": [
                    r"半径[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|毫米|厘米|米|in|英寸)?",
                    r"r[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|毫米|厘米|米|in|英寸)?",
                    r"radius[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|in)?",
                ],
                "type": ParameterType.DIMENSION,
                "unit_type": UnitType.LENGTH,
                "default_unit": "mm",
            },
            "length": {
                "patterns": [
                    r"长度[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|毫米|厘米|米|in|英寸)?",
                    r"长[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|毫米|厘米|米|in|英寸)?",
                    r"length[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|in)?",
                ],
                "type": ParameterType.DIMENSION,
                "unit_type": UnitType.LENGTH,
                "default_unit": "mm",
            },
            "width": {
                "patterns": [
                    r"宽度[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|毫米|厘米|米|in|英寸)?",
                    r"宽[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|毫米|厘米|米|in|英寸)?",
                    r"width[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|in)?",
                ],
                "type": ParameterType.DIMENSION,
                "unit_type": UnitType.LENGTH,
                "default_unit": "mm",
            },
            "height": {
                "patterns": [
                    r"高度[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|毫米|厘米|米|in|英寸)?",
                    r"高[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|毫米|厘米|米|in|英寸)?",
                    r"height[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|in)?",
                ],
                "type": ParameterType.DIMENSION,
                "unit_type": UnitType.LENGTH,
                "default_unit": "mm",
            },
            "thickness": {
                "patterns": [
                    r"厚度[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|毫米|厘米|米|in|英寸)?",
                    r"厚[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|毫米|厘米|米|in|英寸)?",
                    r"thickness[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|in)?",
                ],
                "type": ParameterType.DIMENSION,
                "unit_type": UnitType.LENGTH,
                "default_unit": "mm",
            },
            # 角度参数
            "angle": {
                "patterns": [
                    r"角度[：:=]?\s*(\d+(?:\.\d+)?)\s*(度|°|deg|弧度|rad)?",
                    r"旋转[：:=]?\s*(\d+(?:\.\d+)?)\s*(度|°|deg|弧度|rad)?",
                    r"angle[：:=]?\s*(\d+(?:\.\d+)?)\s*(deg|rad|°)?",
                ],
                "type": ParameterType.ANGLE,
                "unit_type": UnitType.ANGLE,
                "default_unit": "度",
            },
            # 数量参数
            "count": {
                "patterns": [
                    r"数量[：:=]?\s*(\d+)\s*个?",
                    r"个数[：:=]?\s*(\d+)\s*个?",
                    r"(\d+)\s*个",
                    r"count[：:=]?\s*(\d+)",
                ],
                "type": ParameterType.COUNT,
                "unit_type": None,
                "default_unit": "",
            },
            # 坐标参数
            "position_x": {
                "patterns": [
                    r"x[：:=]?\s*([+-]?\d+(?:\.\d+)?)\s*(mm|cm|m|毫米|厘米|米)?",
                    r"横坐标[：:=]?\s*([+-]?\d+(?:\.\d+)?)\s*(mm|cm|m|毫米|厘米|米)?",
                ],
                "type": ParameterType.COORDINATE,
                "unit_type": UnitType.LENGTH,
                "default_unit": "mm",
            },
            "position_y": {
                "patterns": [
                    r"y[：:=]?\s*([+-]?\d+(?:\.\d+)?)\s*(mm|cm|m|毫米|厘米|米)?",
                    r"纵坐标[：:=]?\s*([+-]?\d+(?:\.\d+)?)\s*(mm|cm|m|毫米|厘米|米)?",
                ],
                "type": ParameterType.COORDINATE,
                "unit_type": UnitType.LENGTH,
                "default_unit": "mm",
            },
            "position_z": {
                "patterns": [
                    r"z[：:=]?\s*([+-]?\d+(?:\.\d+)?)\s*(mm|cm|m|毫米|厘米|米)?",
                    r"高度坐标[：:=]?\s*([+-]?\d+(?:\.\d+)?)\s*(mm|cm|m|毫米|厘米|米)?",
                ],
                "type": ParameterType.COORDINATE,
                "unit_type": UnitType.LENGTH,
                "default_unit": "mm",
            },
        }

        # 材料模式
        self.material_patterns = {
            "steel": ["钢", "钢材", "碳钢", "不锈钢", "steel", "stainless"],
            "aluminum": ["铝", "铝合金", "aluminum", "aluminium"],
            "plastic": ["塑料", "塑胶", "ABS", "PVC", "plastic"],
            "copper": ["铜", "黄铜", "青铜", "copper", "brass", "bronze"],
            "titanium": ["钛", "钛合金", "titanium"],
            "carbon_fiber": ["碳纤维", "carbon fiber"],
        }

        # 布尔值模式
        self.boolean_patterns = {
            True: ["是", "有", "开启", "启用", "true", "yes", "on", "1"],
            False: ["否", "无", "关闭", "禁用", "false", "no", "off", "0"],
        }

    def parse_parameters(self, text: str) -> List[ParsedParameter]:
        """解析文本中的所有参数

        Args:
            text: 输入文本

        Returns:
            List[ParsedParameter]: 解析后的参数列表
        """
        try:
            self.logger.info(f"解析参数: {text}")

            parameters = []

            # 预处理文本
            processed_text = self._preprocess_text(text)

            # 解析各种类型的参数
            parameters.extend(self._parse_dimension_parameters(processed_text))
            parameters.extend(self._parse_angle_parameters(processed_text))
            parameters.extend(self._parse_count_parameters(processed_text))
            parameters.extend(self._parse_coordinate_parameters(processed_text))
            parameters.extend(self._parse_material_parameters(processed_text))
            parameters.extend(self._parse_boolean_parameters(processed_text))

            # 去重和验证
            parameters = self._deduplicate_parameters(parameters)
            parameters = self._validate_parameters(parameters)

            self.logger.info(f"解析到 {len(parameters)} 个参数")
            return parameters

        except Exception as e:
            self.logger.error(f"解析参数失败: {e}")
            return []

    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        try:
            # 转换为小写
            text = text.lower()

            # 标准化标点符号
            text = text.replace("：", ":")
            text = text.replace("，", ",")
            text = text.replace("。", ".")

            # 移除多余空格
            text = re.sub(r"\s+", " ", text).strip()

            return text

        except Exception as e:
            self.logger.error(f"预处理文本失败: {e}")
            return text

    def _parse_dimension_parameters(self, text: str) -> List[ParsedParameter]:
        """解析尺寸参数"""
        parameters = []

        try:
            dimension_params = [
                "diameter",
                "radius",
                "length",
                "width",
                "height",
                "thickness",
            ]

            for param_name in dimension_params:
                param_config = self.parameter_patterns[param_name]

                for pattern in param_config["patterns"]:
                    matches = re.finditer(pattern, text, re.IGNORECASE)

                    for match in matches:
                        value_str = match.group(1)
                        unit = match.group(2) or param_config["default_unit"]

                        try:
                            value = float(value_str)

                            # 单位转换
                            converted_value, final_unit = self._convert_unit(
                                value, unit, param_config["unit_type"]
                            )

                            parameter = ParsedParameter(
                                name=param_name,
                                value=converted_value,
                                original_value=value_str,
                                parameter_type=param_config["type"],
                                unit=final_unit,
                                unit_type=param_config["unit_type"],
                                confidence=0.9,
                                source_text=match.group(0),
                            )

                            parameters.append(parameter)

                        except ValueError:
                            self.logger.warning(f"无法解析尺寸值: {value_str}")

            return parameters

        except Exception as e:
            self.logger.error(f"解析尺寸参数失败: {e}")
            return []

    def _parse_angle_parameters(self, text: str) -> List[ParsedParameter]:
        """解析角度参数"""
        parameters = []

        try:
            param_config = self.parameter_patterns["angle"]

            for pattern in param_config["patterns"]:
                matches = re.finditer(pattern, text, re.IGNORECASE)

                for match in matches:
                    value_str = match.group(1)
                    unit = match.group(2) or param_config["default_unit"]

                    try:
                        value = float(value_str)

                        # 单位转换
                        converted_value, final_unit = self._convert_unit(
                            value, unit, param_config["unit_type"]
                        )

                        parameter = ParsedParameter(
                            name="angle",
                            value=converted_value,
                            original_value=value_str,
                            parameter_type=param_config["type"],
                            unit=final_unit,
                            unit_type=param_config["unit_type"],
                            confidence=0.9,
                            source_text=match.group(0),
                        )

                        parameters.append(parameter)

                    except ValueError:
                        self.logger.warning(f"无法解析角度值: {value_str}")

            return parameters

        except Exception as e:
            self.logger.error(f"解析角度参数失败: {e}")
            return []

    def _parse_count_parameters(self, text: str) -> List[ParsedParameter]:
        """解析数量参数"""
        parameters = []

        try:
            param_config = self.parameter_patterns["count"]

            for pattern in param_config["patterns"]:
                matches = re.finditer(pattern, text, re.IGNORECASE)

                for match in matches:
                    value_str = match.group(1)

                    try:
                        value = int(value_str)

                        parameter = ParsedParameter(
                            name="count",
                            value=value,
                            original_value=value_str,
                            parameter_type=param_config["type"],
                            unit="",
                            unit_type=None,
                            confidence=0.9,
                            source_text=match.group(0),
                        )

                        parameters.append(parameter)

                    except ValueError:
                        self.logger.warning(f"无法解析数量值: {value_str}")

            return parameters

        except Exception as e:
            self.logger.error(f"解析数量参数失败: {e}")
            return []

    def _parse_coordinate_parameters(self, text: str) -> List[ParsedParameter]:
        """解析坐标参数"""
        parameters = []

        try:
            coord_params = ["position_x", "position_y", "position_z"]

            for param_name in coord_params:
                param_config = self.parameter_patterns[param_name]

                for pattern in param_config["patterns"]:
                    matches = re.finditer(pattern, text, re.IGNORECASE)

                    for match in matches:
                        value_str = match.group(1)
                        unit = match.group(2) or param_config["default_unit"]

                        try:
                            value = float(value_str)

                            # 单位转换
                            converted_value, final_unit = self._convert_unit(
                                value, unit, param_config["unit_type"]
                            )

                            parameter = ParsedParameter(
                                name=param_name,
                                value=converted_value,
                                original_value=value_str,
                                parameter_type=param_config["type"],
                                unit=final_unit,
                                unit_type=param_config["unit_type"],
                                confidence=0.8,
                                source_text=match.group(0),
                            )

                            parameters.append(parameter)

                        except ValueError:
                            self.logger.warning(f"无法解析坐标值: {value_str}")

            return parameters

        except Exception as e:
            self.logger.error(f"解析坐标参数失败: {e}")
            return []

    def _parse_material_parameters(self, text: str) -> List[ParsedParameter]:
        """解析材料参数"""
        parameters = []

        try:
            for material, keywords in self.material_patterns.items():
                for keyword in keywords:
                    if keyword in text:
                        parameter = ParsedParameter(
                            name="material",
                            value=material,
                            original_value=keyword,
                            parameter_type=ParameterType.MATERIAL,
                            unit="",
                            unit_type=None,
                            confidence=0.8,
                            source_text=keyword,
                        )

                        parameters.append(parameter)
                        break  # 找到一个就跳出内层循环

            return parameters

        except Exception as e:
            self.logger.error(f"解析材料参数失败: {e}")
            return []

    def _parse_boolean_parameters(self, text: str) -> List[ParsedParameter]:
        """解析布尔参数"""
        parameters = []

        try:
            # 查找布尔值模式
            for bool_value, keywords in self.boolean_patterns.items():
                for keyword in keywords:
                    if keyword in text:
                        # 尝试确定参数名称
                        param_name = self._infer_boolean_parameter_name(text, keyword)

                        parameter = ParsedParameter(
                            name=param_name,
                            value=bool_value,
                            original_value=keyword,
                            parameter_type=ParameterType.BOOLEAN,
                            unit="",
                            unit_type=None,
                            confidence=0.7,
                            source_text=keyword,
                        )

                        parameters.append(parameter)

            return parameters

        except Exception as e:
            self.logger.error(f"解析布尔参数失败: {e}")
            return []

    def _infer_boolean_parameter_name(self, text: str, keyword: str) -> str:
        """推断布尔参数的名称"""
        try:
            # 查找关键词前的词汇
            pattern = r"(\w+)\s*" + re.escape(keyword)
            match = re.search(pattern, text)

            if match:
                return match.group(1)
            else:
                return "boolean_param"

        except Exception:
            return "boolean_param"

    def _convert_unit(
        self, value: float, unit: str, unit_type: Optional[UnitType]
    ) -> Tuple[float, str]:
        """单位转换

        Args:
            value: 原始值
            unit: 原始单位
            unit_type: 单位类型

        Returns:
            Tuple[float, str]: (转换后的值, 标准单位)
        """
        try:
            if unit_type is None:
                return value, unit

            conversions = self.unit_conversions.get(unit_type, {})

            if unit in conversions:
                if unit_type == UnitType.LENGTH:
                    # 长度单位统一转换为毫米
                    converted_value = value * conversions[unit]
                    return converted_value, "mm"
                elif unit_type == UnitType.ANGLE:
                    # 角度单位统一转换为度
                    if unit in ["弧度", "rad"]:
                        converted_value = value * conversions[unit]
                    else:
                        converted_value = value
                    return converted_value, "度"
                else:
                    # 其他单位类型保持原样
                    return value, unit
            else:
                # 未知单位，保持原样
                return value, unit

        except Exception as e:
            self.logger.error(f"单位转换失败: {e}")
            return value, unit

    def _deduplicate_parameters(
        self, parameters: List[ParsedParameter]
    ) -> List[ParsedParameter]:
        """去除重复参数"""
        try:
            # 按参数名分组
            param_groups = {}
            for param in parameters:
                if param.name not in param_groups:
                    param_groups[param.name] = []
                param_groups[param.name].append(param)

            # 对每组参数选择置信度最高的
            deduplicated = []
            for param_name, param_list in param_groups.items():
                if len(param_list) == 1:
                    deduplicated.append(param_list[0])
                else:
                    # 选择置信度最高的参数
                    best_param = max(param_list, key=lambda p: p.confidence)
                    deduplicated.append(best_param)

            return deduplicated

        except Exception as e:
            self.logger.error(f"去重参数失败: {e}")
            return parameters

    def _validate_parameters(
        self, parameters: List[ParsedParameter]
    ) -> List[ParsedParameter]:
        """验证参数"""
        try:
            valid_parameters = []

            for param in parameters:
                try:
                    # 基本验证
                    if param.name and param.value is not None:
                        # 数值参数的合理性检查
                        if param.parameter_type == ParameterType.DIMENSION:
                            if (
                                isinstance(param.value, (int, float))
                                and param.value > 0
                            ):
                                valid_parameters.append(param)
                            else:
                                self.logger.warning(
                                    f"尺寸参数值无效: {param.name}={param.value}"
                                )
                        elif param.parameter_type == ParameterType.ANGLE:
                            if (
                                isinstance(param.value, (int, float))
                                and 0 <= param.value <= 360
                            ):
                                valid_parameters.append(param)
                            else:
                                self.logger.warning(
                                    f"角度参数值无效: {param.name}={param.value}"
                                )
                        elif param.parameter_type == ParameterType.COUNT:
                            if isinstance(param.value, int) and param.value > 0:
                                valid_parameters.append(param)
                            else:
                                self.logger.warning(
                                    f"数量参数值无效: {param.name}={param.value}"
                                )
                        else:
                            valid_parameters.append(param)
                    else:
                        self.logger.warning(f"参数名称或值为空: {param}")

                except Exception as e:
                    self.logger.error(f"验证参数 {param.name} 失败: {e}")

            return valid_parameters

        except Exception as e:
            self.logger.error(f"验证参数失败: {e}")
            return parameters

    def get_parameter_by_name(
        self, parameters: List[ParsedParameter], name: str
    ) -> Optional[ParsedParameter]:
        """根据名称获取参数

        Args:
            parameters: 参数列表
            name: 参数名称

        Returns:
            Optional[ParsedParameter]: 找到的参数，如果没有则返回None
        """
        try:
            for param in parameters:
                if param.name == name:
                    return param
            return None

        except Exception as e:
            self.logger.error(f"获取参数失败: {e}")
            return None

    def get_parameters_by_type(
        self, parameters: List[ParsedParameter], param_type: ParameterType
    ) -> List[ParsedParameter]:
        """根据类型获取参数

        Args:
            parameters: 参数列表
            param_type: 参数类型

        Returns:
            List[ParsedParameter]: 匹配的参数列表
        """
        try:
            return [param for param in parameters if param.parameter_type == param_type]

        except Exception as e:
            self.logger.error(f"根据类型获取参数失败: {e}")
            return []

    def to_dict(self, parameters: List[ParsedParameter]) -> Dict[str, Any]:
        """将参数列表转换为字典

        Args:
            parameters: 参数列表

        Returns:
            Dict[str, Any]: 字典表示
        """
        try:
            result = {
                "parameters": [],
                "summary": {
                    "total_count": len(parameters),
                    "by_type": {},
                    "timestamp": datetime.now().isoformat(),
                },
            }

            # 统计各类型参数数量
            type_counts = {}

            for param in parameters:
                param_dict = {
                    "name": param.name,
                    "value": param.value,
                    "original_value": param.original_value,
                    "type": param.parameter_type.value,
                    "unit": param.unit,
                    "unit_type": param.unit_type.value if param.unit_type else None,
                    "confidence": param.confidence,
                    "source_text": param.source_text,
                    "metadata": param.metadata,
                }

                result["parameters"].append(param_dict)

                # 统计类型
                param_type = param.parameter_type.value
                type_counts[param_type] = type_counts.get(param_type, 0) + 1

            result["summary"]["by_type"] = type_counts

            return result

        except Exception as e:
            self.logger.error(f"转换为字典失败: {e}")
            return {}

    def from_dict(self, data: Dict[str, Any]) -> List[ParsedParameter]:
        """从字典创建参数列表

        Args:
            data: 字典数据

        Returns:
            List[ParsedParameter]: 参数列表
        """
        try:
            parameters = []

            for param_data in data.get("parameters", []):
                try:
                    parameter = ParsedParameter(
                        name=param_data["name"],
                        value=param_data["value"],
                        original_value=param_data["original_value"],
                        parameter_type=ParameterType(param_data["type"]),
                        unit=param_data.get("unit", ""),
                        unit_type=(
                            UnitType(param_data["unit_type"])
                            if param_data.get("unit_type")
                            else None
                        ),
                        confidence=param_data.get("confidence", 0.0),
                        source_text=param_data.get("source_text", ""),
                        metadata=param_data.get("metadata", {}),
                    )

                    parameters.append(parameter)

                except Exception as e:
                    self.logger.error(f"创建参数失败: {e}")

            return parameters

        except Exception as e:
            self.logger.error(f"从字典创建参数列表失败: {e}")
            return []
