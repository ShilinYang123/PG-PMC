#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-PMC AI设计助理 - 语言处理器
"""

import json
import re
from dataclasses import dataclass
from typing import Dict, List

try:
    import openai
except ImportError:
    openai = None

from src.utils.logger import get_logger


@dataclass
class DesignIntent:
    """设计意图数据结构"""

    object_type: str  # 对象类型（如：杯子、盒子、支架等）
    dimensions: Dict[str, float]  # 尺寸参数
    features: List[str]  # 特征列表
    materials: List[str]  # 材料建议
    constraints: List[str]  # 设计约束
    operations: List[str]  # 建模操作序列
    confidence: float  # 解析置信度


class LanguageProcessor:
    """自然语言处理器

    负责理解用户的自然语言输入，提取设计意图和参数
    """

    def __init__(self, api_key: str = None, model: str = "gpt-4"):
        """初始化语言处理器

        Args:
            api_key: OpenAI API密钥
            model: 使用的模型名称
        """
        self.api_key = api_key
        self.model = model
        self.logger = get_logger(self.__class__.__name__)

        # 检查OpenAI依赖
        if openai is None:
            raise ImportError("缺少openai依赖，请运行: pip install openai")

        # 设置API密钥
        if api_key:
            openai.api_key = api_key

        # 小家电设计领域知识库
        self.appliance_knowledge = {
            "杯子": {
                "typical_dimensions": {"height": 100, "diameter": 80, "thickness": 2},
                "features": ["手柄", "底座", "杯口", "杯身"],
                "materials": ["塑料", "陶瓷", "玻璃", "不锈钢"],
            },
            "盒子": {
                "typical_dimensions": {
                    "length": 200,
                    "width": 150,
                    "height": 100,
                    "thickness": 3,
                },
                "features": ["盖子", "底部", "侧壁", "扣手"],
                "materials": ["塑料", "纸板", "金属"],
            },
            "支架": {
                "typical_dimensions": {
                    "height": 150,
                    "base_diameter": 100,
                    "thickness": 5,
                },
                "features": ["底座", "支撑柱", "托盘", "调节机构"],
                "materials": ["金属", "塑料", "复合材料"],
            },
        }

        # 尺寸单位转换
        self.unit_conversions = {
            "毫米": 1.0,
            "mm": 1.0,
            "厘米": 10.0,
            "cm": 10.0,
            "米": 1000.0,
            "m": 1000.0,
            "英寸": 25.4,
            "inch": 25.4,
            "in": 25.4,
        }

    def process_input(self, user_input: str) -> DesignIntent:
        """处理用户输入，提取设计意图

        Args:
            user_input: 用户的自然语言输入

        Returns:
            DesignIntent: 解析后的设计意图
        """
        try:
            self.logger.info(f"处理用户输入: {user_input}")

            # 预处理输入
            cleaned_input = self._preprocess_input(user_input)

            # 使用AI模型解析
            if self.api_key:
                intent = self._parse_with_ai(cleaned_input)
            else:
                # 使用规则基础解析作为后备
                intent = self._parse_with_rules(cleaned_input)

            # 后处理和验证
            intent = self._postprocess_intent(intent)

            self.logger.info(
                f"解析结果: {intent.object_type}, 置信度: {intent.confidence}"
            )
            return intent

        except Exception as e:
            self.logger.error(f"语言处理失败: {e}")
            # 返回默认意图
            return DesignIntent(
                object_type="未知对象",
                dimensions={},
                features=[],
                materials=[],
                constraints=[],
                operations=[],
                confidence=0.0,
            )

    def _preprocess_input(self, text: str) -> str:
        """预处理输入文本"""
        # 转换为小写
        text = text.lower()

        # 标准化数字和单位
        text = re.sub(r"(\d+)\s*(毫米|mm|厘米|cm|米|m|英寸|inch|in)", r"\1\2", text)

        # 移除多余空格
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _parse_with_ai(self, text: str) -> DesignIntent:
        """使用AI模型解析设计意图"""
        try:
            prompt = self._build_ai_prompt(text)

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的小家电CAD设计助理，擅长理解设计需求并转换为具体的建模参数。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1000,
            )

            result_text = response.choices[0].message.content
            return self._parse_ai_response(result_text)

        except Exception as e:
            self.logger.warning(f"AI解析失败，使用规则解析: {e}")
            return self._parse_with_rules(text)

    def _build_ai_prompt(self, text: str) -> str:
        """构建AI提示词"""
        return f"""
请分析以下设计需求，提取关键信息并以JSON格式返回：

用户输入："{text}"

请返回以下格式的JSON：
{{
    "object_type": "对象类型（如：杯子、盒子、支架等）",
    "dimensions": {{
        "参数名": 数值（毫米）
    }},
    "features": ["特征1", "特征2"],
    "materials": ["材料1", "材料2"],
    "constraints": ["约束1", "约束2"],
    "operations": ["操作1", "操作2"],
    "confidence": 0.0到1.0之间的置信度
}}

注意：
1. 所有尺寸统一转换为毫米
2. 基于小家电设计经验推断合理的默认值
3. 操作序列应该是Creo建模的具体步骤
"""

    def _parse_ai_response(self, response_text: str) -> DesignIntent:
        """解析AI响应"""
        try:
            # 提取JSON部分
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)

                return DesignIntent(
                    object_type=data.get("object_type", "未知对象"),
                    dimensions=data.get("dimensions", {}),
                    features=data.get("features", []),
                    materials=data.get("materials", []),
                    constraints=data.get("constraints", []),
                    operations=data.get("operations", []),
                    confidence=data.get("confidence", 0.5),
                )
            else:
                raise ValueError("无法从AI响应中提取JSON")

        except Exception as e:
            self.logger.error(f"解析AI响应失败: {e}")
            raise

    def _parse_with_rules(self, text: str) -> DesignIntent:
        """使用规则基础方法解析"""
        # 识别对象类型
        object_type = self._extract_object_type(text)

        # 提取尺寸
        dimensions = self._extract_dimensions(text)

        # 获取默认知识
        knowledge = self.appliance_knowledge.get(object_type, {})

        # 合并默认尺寸
        default_dims = knowledge.get("typical_dimensions", {})
        for key, value in default_dims.items():
            if key not in dimensions:
                dimensions[key] = value

        return DesignIntent(
            object_type=object_type,
            dimensions=dimensions,
            features=knowledge.get("features", []),
            materials=knowledge.get("materials", []),
            constraints=[],
            operations=self._generate_basic_operations(object_type),
            confidence=0.7 if object_type != "未知对象" else 0.3,
        )

    def _extract_object_type(self, text: str) -> str:
        """提取对象类型"""
        for obj_type in self.appliance_knowledge.keys():
            if obj_type in text:
                return obj_type

        # 尝试其他常见对象
        common_objects = ["瓶子", "罐子", "托盘", "架子", "底座", "外壳"]
        for obj in common_objects:
            if obj in text:
                return obj

        return "未知对象"

    def _extract_dimensions(self, text: str) -> Dict[str, float]:
        """提取尺寸信息"""
        dimensions = {}

        # 匹配数字+单位的模式
        patterns = [
            r"长度?[：:是为]?\s*(\d+(?:\.\d+)?)\s*(毫米|mm|厘米|cm|米|m)",
            r"宽度?[：:是为]?\s*(\d+(?:\.\d+)?)\s*(毫米|mm|厘米|cm|米|m)",
            r"高度?[：:是为]?\s*(\d+(?:\.\d+)?)\s*(毫米|mm|厘米|cm|米|m)",
            r"直径[：:是为]?\s*(\d+(?:\.\d+)?)\s*(毫米|mm|厘米|cm|米|m)",
            r"厚度?[：:是为]?\s*(\d+(?:\.\d+)?)\s*(毫米|mm|厘米|cm|米|m)",
            r"(\d+(?:\.\d+)?)\s*(毫米|mm|厘米|cm|米|m)\s*[×x*]\s*(\d+(?:\.\d+)?)\s*(毫米|mm|厘米|cm|米|m)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if "长" in pattern:
                    value = float(match.group(1))
                    unit = match.group(2)
                    dimensions["length"] = value * self.unit_conversions.get(unit, 1.0)
                elif "宽" in pattern:
                    value = float(match.group(1))
                    unit = match.group(2)
                    dimensions["width"] = value * self.unit_conversions.get(unit, 1.0)
                elif "高" in pattern:
                    value = float(match.group(1))
                    unit = match.group(2)
                    dimensions["height"] = value * self.unit_conversions.get(unit, 1.0)
                elif "直径" in pattern:
                    value = float(match.group(1))
                    unit = match.group(2)
                    dimensions["diameter"] = value * self.unit_conversions.get(
                        unit, 1.0
                    )
                elif "厚" in pattern:
                    value = float(match.group(1))
                    unit = match.group(2)
                    dimensions["thickness"] = value * self.unit_conversions.get(
                        unit, 1.0
                    )

        return dimensions

    def _generate_basic_operations(self, object_type: str) -> List[str]:
        """生成基础建模操作序列"""
        if object_type == "杯子":
            return ["创建圆柱体作为杯身", "创建内部空腔", "添加手柄特征", "倒角处理"]
        elif object_type == "盒子":
            return ["创建长方体外壳", "创建内部空腔", "添加盖子特征", "添加扣手"]
        elif object_type == "支架":
            return ["创建底座", "创建支撑柱", "添加托盘", "装配连接"]
        else:
            return ["创建基础几何体", "添加特征", "完善细节"]

    def _postprocess_intent(self, intent: DesignIntent) -> DesignIntent:
        """后处理设计意图"""
        # 验证尺寸合理性
        for key, value in intent.dimensions.items():
            if value <= 0:
                self.logger.warning(f"无效尺寸 {key}: {value}，使用默认值")
                intent.dimensions[key] = 100.0  # 默认100mm
            elif value > 10000:  # 超过10米认为不合理
                self.logger.warning(f"尺寸过大 {key}: {value}，调整为合理值")
                intent.dimensions[key] = value / 10  # 可能是单位错误

        return intent