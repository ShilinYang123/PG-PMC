#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-PMC AI设计助理 - 设计解释器
"""

# import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from src.utils.logger import get_logger


class DesignIntent(Enum):
    """设计意图类型"""

    CREATE_PART = "create_part"  # 创建零件
    MODIFY_PART = "modify_part"  # 修改零件
    CREATE_ASSEMBLY = "create_assembly"  # 创建装配体
    CREATE_DRAWING = "create_drawing"  # 创建工程图
    ANALYZE_DESIGN = "analyze_design"  # 分析设计
    OPTIMIZE_DESIGN = "optimize_design"  # 优化设计
    UNKNOWN = "unknown"  # 未知意图


class GeometryType(Enum):
    """几何体类型"""

    CYLINDER = "cylinder"  # 圆柱体
    BOX = "box"  # 长方体
    SPHERE = "sphere"  # 球体
    CONE = "cone"  # 圆锥体
    TORUS = "torus"  # 环形体
    EXTRUDE = "extrude"  # 拉伸
    REVOLVE = "revolve"  # 旋转
    SWEEP = "sweep"  # 扫描
    LOFT = "loft"  # 放样
    CUSTOM = "custom"  # 自定义


class FeatureType(Enum):
    """特征类型"""

    FILLET = "fillet"  # 圆角
    CHAMFER = "chamfer"  # 倒角
    HOLE = "hole"  # 孔
    SHELL = "shell"  # 抽壳
    PATTERN = "pattern"  # 阵列
    MIRROR = "mirror"  # 镜像
    DRAFT = "draft"  # 拔模
    RIB = "rib"  # 筋
    THREAD = "thread"  # 螺纹


@dataclass
class DesignParameter:
    """设计参数"""

    name: str
    value: Union[float, int, str]
    unit: str = ""
    description: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    def __post_init__(self):
        # 验证数值范围
        if isinstance(self.value, (int, float)):
            if self.min_value is not None and self.value < self.min_value:
                raise ValueError(
                    f"参数 {self.name} 的值 {self.value} 小于最小值 {self.min_value}"
                )
            if self.max_value is not None and self.value > self.max_value:
                raise ValueError(
                    f"参数 {self.name} 的值 {self.value} 大于最大值 {self.max_value}"
                )


@dataclass
class DesignInstruction:
    """设计指令"""

    intent: DesignIntent
    geometry_type: Optional[GeometryType] = None
    feature_type: Optional[FeatureType] = None
    parameters: List[DesignParameter] = None
    constraints: List[str] = None
    materials: List[str] = None
    description: str = ""
    confidence: float = 0.0

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
        if self.constraints is None:
            self.constraints = []
        if self.materials is None:
            self.materials = []


class DesignInterpreter:
    """设计解释器

    负责解析用户的设计意图，提取几何参数和约束条件
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

        # 意图识别模式
        self.intent_patterns = {
            DesignIntent.CREATE_PART: [
                r"创建|制作|建立|生成.*零件",
                r"画一个|做一个|建一个",
                r"新建.*零件",
                r"create.*part",
                r"make.*part",
            ],
            DesignIntent.MODIFY_PART: [
                r"修改|更改|调整.*零件",
                r"改变.*尺寸",
                r"modify.*part",
                r"change.*dimension",
            ],
            DesignIntent.CREATE_ASSEMBLY: [
                r"创建|制作.*装配体",
                r"组装|装配",
                r"create.*assembly",
                r"assemble",
            ],
            DesignIntent.CREATE_DRAWING: [
                r"创建|制作.*工程图",
                r"出图|制图",
                r"create.*drawing",
                r"make.*drawing",
            ],
        }

        # 几何体识别模式
        self.geometry_patterns = {
            GeometryType.CYLINDER: [r"圆柱|柱体|圆筒|管子", r"cylinder|tube|pipe"],
            GeometryType.BOX: [r"长方体|立方体|方块|盒子|箱子", r"box|cube|block|case"],
            GeometryType.SPHERE: [r"球|球体|圆球", r"sphere|ball"],
            GeometryType.CONE: [r"圆锥|锥体|锥形", r"cone|conical"],
            GeometryType.TORUS: [r"环|环形|圆环|甜甜圈", r"torus|ring|donut"],
        }

        # 特征识别模式
        self.feature_patterns = {
            FeatureType.FILLET: [r"圆角|倒圆角|R角", r"fillet|round"],
            FeatureType.CHAMFER: [r"倒角|斜角|切角", r"chamfer|bevel"],
            FeatureType.HOLE: [r"孔|洞|钻孔|打孔", r"hole|drill|bore"],
            FeatureType.SHELL: [r"抽壳|薄壁|壳体", r"shell|hollow"],
        }

        # 参数提取模式
        self.parameter_patterns = {
            "diameter": r"直径[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m)?",
            "radius": r"半径[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m)?",
            "length": r"长度[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m)?",
            "width": r"宽度[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m)?",
            "height": r"高度[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m)?",
            "thickness": r"厚度[：:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m)?",
            "angle": r"角度[：:=]?\s*(\d+(?:\.\d+)?)\s*(度|°|deg)?",
        }

        # 单位转换表（转换为毫米）
        self.unit_conversion = {
            "mm": 1.0,
            "cm": 10.0,
            "m": 1000.0,
            "in": 25.4,
            "ft": 304.8,
            "度": 1.0,
            "°": 1.0,
            "deg": 1.0,
            "rad": 57.2958,  # 弧度转度
        }

        # 材料识别模式
        self.material_patterns = {
            "steel": r"钢|钢材|碳钢|不锈钢|steel|stainless",
            "aluminum": r"铝|铝合金|aluminum|aluminium",
            "plastic": r"塑料|塑胶|ABS|PVC|plastic",
            "copper": r"铜|黄铜|青铜|copper|brass|bronze",
            "titanium": r"钛|钛合金|titanium",
            "carbon_fiber": r"碳纤维|carbon.*fiber",
        }

    def interpret(self, user_input: str) -> DesignInstruction:
        """解释用户输入

        Args:
            user_input: 用户输入文本

        Returns:
            DesignInstruction: 设计指令
        """
        try:
            self.logger.info(f"解释用户输入: {user_input}")

            # 预处理输入
            processed_input = self._preprocess_input(user_input)

            # 识别设计意图
            intent = self._identify_intent(processed_input)

            # 识别几何体类型
            geometry_type = self._identify_geometry_type(processed_input)

            # 识别特征类型
            feature_type = self._identify_feature_type(processed_input)

            # 提取参数
            parameters = self._extract_parameters(processed_input)

            # 提取约束
            constraints = self._extract_constraints(processed_input)

            # 识别材料
            materials = self._identify_materials(processed_input)

            # 计算置信度
            confidence = self._calculate_confidence(
                intent, geometry_type, feature_type, parameters
            )

            instruction = DesignInstruction(
                intent=intent,
                geometry_type=geometry_type,
                feature_type=feature_type,
                parameters=parameters,
                constraints=constraints,
                materials=materials,
                description=user_input,
                confidence=confidence,
            )

            self.logger.info(f"解释结果: {instruction}")
            return instruction

        except Exception as e:
            self.logger.error(f"解释用户输入失败: {e}")
            return DesignInstruction(
                intent=DesignIntent.UNKNOWN, description=user_input, confidence=0.0
            )

    def _preprocess_input(self, text: str) -> str:
        """预处理输入文本"""
        try:
            # 转换为小写
            text = text.lower()

            # 移除多余空格
            text = re.sub(r"\s+", " ", text).strip()

            # 标准化标点符号
            text = text.replace("：", ":")
            text = text.replace("，", ",")
            text = text.replace("。", ".")

            return text

        except Exception as e:
            self.logger.error(f"预处理输入失败: {e}")
            return text

    def _identify_intent(self, text: str) -> DesignIntent:
        """识别设计意图"""
        try:
            for intent, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        return intent

            # 默认为创建零件
            return DesignIntent.CREATE_PART

        except Exception as e:
            self.logger.error(f"识别设计意图失败: {e}")
            return DesignIntent.UNKNOWN

    def _identify_geometry_type(self, text: str) -> Optional[GeometryType]:
        """识别几何体类型"""
        try:
            for geometry, patterns in self.geometry_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        return geometry

            return None

        except Exception as e:
            self.logger.error(f"识别几何体类型失败: {e}")
            return None

    def _identify_feature_type(self, text: str) -> Optional[FeatureType]:
        """识别特征类型"""
        try:
            for feature, patterns in self.feature_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        return feature

            return None

        except Exception as e:
            self.logger.error(f"识别特征类型失败: {e}")
            return None

    def _extract_parameters(self, text: str) -> List[DesignParameter]:
        """提取设计参数"""
        try:
            parameters = []

            for param_name, pattern in self.parameter_patterns.items():
                matches = re.finditer(pattern, text, re.IGNORECASE)

                for match in matches:
                    value_str = match.group(1)
                    unit = match.group(2) or "mm"  # 默认单位为毫米

                    try:
                        value = float(value_str)

                        # 单位转换
                        if unit in self.unit_conversion:
                            if param_name == "angle":
                                # 角度不需要转换为毫米
                                converted_value = value
                                final_unit = "度"
                            else:
                                converted_value = value * self.unit_conversion[unit]
                                final_unit = "mm"
                        else:
                            converted_value = value
                            final_unit = unit

                        parameter = DesignParameter(
                            name=param_name,
                            value=converted_value,
                            unit=final_unit,
                            description=f"从用户输入提取的{param_name}",
                        )

                        parameters.append(parameter)

                    except ValueError:
                        self.logger.warning(f"无法解析参数值: {value_str}")

            return parameters

        except Exception as e:
            self.logger.error(f"提取参数失败: {e}")
            return []

    def _extract_constraints(self, text: str) -> List[str]:
        """提取约束条件"""
        try:
            constraints = []

            # 约束关键词模式
            constraint_patterns = [
                r"对称|symmetric",
                r"同心|concentric",
                r"平行|parallel",
                r"垂直|perpendicular",
                r"相切|tangent",
                r"重合|coincident",
                r"固定|fixed",
                r"等距|equal",
            ]

            for pattern in constraint_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    constraints.append(pattern.split("|")[0])  # 使用中文描述

            return constraints

        except Exception as e:
            self.logger.error(f"提取约束失败: {e}")
            return []

    def _identify_materials(self, text: str) -> List[str]:
        """识别材料"""
        try:
            materials = []

            for material, pattern in self.material_patterns.items():
                if re.search(pattern, text, re.IGNORECASE):
                    materials.append(material)

            return materials

        except Exception as e:
            self.logger.error(f"识别材料失败: {e}")
            return []

    def _calculate_confidence(
        self,
        intent: DesignIntent,
        geometry_type: Optional[GeometryType],
        feature_type: Optional[FeatureType],
        parameters: List[DesignParameter],
    ) -> float:
        """计算置信度"""
        try:
            confidence = 0.0

            # 意图识别得分
            if intent != DesignIntent.UNKNOWN:
                confidence += 0.3

            # 几何体类型得分
            if geometry_type is not None:
                confidence += 0.3

            # 特征类型得分
            if feature_type is not None:
                confidence += 0.2

            # 参数提取得分
            if parameters:
                confidence += min(0.2, len(parameters) * 0.05)

            return min(1.0, confidence)

        except Exception as e:
            self.logger.error(f"计算置信度失败: {e}")
            return 0.0

    def validate_instruction(
        self, instruction: DesignInstruction
    ) -> Tuple[bool, List[str]]:
        """验证设计指令

        Args:
            instruction: 设计指令

        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        try:
            errors = []

            # 检查意图
            if instruction.intent == DesignIntent.UNKNOWN:
                errors.append("无法识别设计意图")

            # 检查几何体参数
            if instruction.geometry_type:
                required_params = self._get_required_parameters(
                    instruction.geometry_type
                )
                provided_params = {p.name for p in instruction.parameters}

                missing_params = required_params - provided_params
                if missing_params:
                    errors.append(f"缺少必需参数: {', '.join(missing_params)}")

            # 检查参数值的合理性
            for param in instruction.parameters:
                if isinstance(param.value, (int, float)):
                    if param.value <= 0:
                        errors.append(f"参数 {param.name} 的值必须大于0")

                    # 检查尺寸合理性
                    if param.name in [
                        "diameter",
                        "radius",
                        "length",
                        "width",
                        "height",
                    ]:
                        if param.value > 10000:  # 10米
                            errors.append(
                                f"参数 {param.name} 的值过大: {param.value}mm"
                            )
                        elif param.value < 0.1:  # 0.1毫米
                            errors.append(
                                f"参数 {param.name} 的值过小: {param.value}mm"
                            )

            # 检查置信度
            if instruction.confidence < 0.3:
                errors.append("指令置信度过低，可能存在理解错误")

            is_valid = len(errors) == 0
            return is_valid, errors

        except Exception as e:
            self.logger.error(f"验证设计指令失败: {e}")
            return False, [f"验证过程出错: {e}"]

    def _get_required_parameters(self, geometry_type: GeometryType) -> set:
        """获取几何体类型的必需参数"""
        required_params = {
            GeometryType.CYLINDER: {"diameter", "height"},
            GeometryType.BOX: {"length", "width", "height"},
            GeometryType.SPHERE: {"diameter"},
            GeometryType.CONE: {"diameter", "height"},
            GeometryType.TORUS: {"diameter", "thickness"},
        }

        return required_params.get(geometry_type, set())

    def get_parameter_suggestions(self, instruction: DesignInstruction) -> List[str]:
        """获取参数建议

        Args:
            instruction: 设计指令

        Returns:
            List[str]: 参数建议列表
        """
        try:
            suggestions = []

            if instruction.geometry_type:
                required_params = self._get_required_parameters(
                    instruction.geometry_type
                )
                provided_params = {p.name for p in instruction.parameters}

                missing_params = required_params - provided_params

                for param in missing_params:
                    if param == "diameter":
                        suggestions.append("请指定直径，例如：直径50mm")
                    elif param == "height":
                        suggestions.append("请指定高度，例如：高度100mm")
                    elif param == "length":
                        suggestions.append("请指定长度，例如：长度200mm")
                    elif param == "width":
                        suggestions.append("请指定宽度，例如：宽度150mm")
                    elif param == "thickness":
                        suggestions.append("请指定厚度，例如：厚度5mm")

            return suggestions

        except Exception as e:
            self.logger.error(f"获取参数建议失败: {e}")
            return []

    def to_dict(self, instruction: DesignInstruction) -> Dict[str, Any]:
        """将设计指令转换为字典

        Args:
            instruction: 设计指令

        Returns:
            Dict[str, Any]: 字典表示
        """
        try:
            return {
                "intent": instruction.intent.value,
                "geometry_type": (
                    instruction.geometry_type.value
                    if instruction.geometry_type
                    else None
                ),
                "feature_type": (
                    instruction.feature_type.value if instruction.feature_type else None
                ),
                "parameters": [
                    {
                        "name": p.name,
                        "value": p.value,
                        "unit": p.unit,
                        "description": p.description,
                    }
                    for p in instruction.parameters
                ],
                "constraints": instruction.constraints,
                "materials": instruction.materials,
                "description": instruction.description,
                "confidence": instruction.confidence,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"转换为字典失败: {e}")
            return {}

    def from_dict(self, data: Dict[str, Any]) -> DesignInstruction:
        """从字典创建设计指令

        Args:
            data: 字典数据

        Returns:
            DesignInstruction: 设计指令
        """
        try:
            intent = DesignIntent(data.get("intent", "unknown"))

            geometry_type = None
            if data.get("geometry_type"):
                geometry_type = GeometryType(data["geometry_type"])

            feature_type = None
            if data.get("feature_type"):
                feature_type = FeatureType(data["feature_type"])

            parameters = []
            for p_data in data.get("parameters", []):
                parameter = DesignParameter(
                    name=p_data["name"],
                    value=p_data["value"],
                    unit=p_data.get("unit", ""),
                    description=p_data.get("description", ""),
                )
                parameters.append(parameter)

            return DesignInstruction(
                intent=intent,
                geometry_type=geometry_type,
                feature_type=feature_type,
                parameters=parameters,
                constraints=data.get("constraints", []),
                materials=data.get("materials", []),
                description=data.get("description", ""),
                confidence=data.get("confidence", 0.0),
            )

        except Exception as e:
            self.logger.error(f"从字典创建设计指令失败: {e}")
            return DesignInstruction(intent=DesignIntent.UNKNOWN, confidence=0.0)