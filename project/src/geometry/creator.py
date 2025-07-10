#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 几何创建器
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.ai.language_processor import DesignIntent
from src.creo.connector import CreoConnector
from src.utils.logger import get_logger


@dataclass
class ModelInfo:
    """模型信息"""

    name: str
    type: str
    features: List[str]
    parameters: Dict[str, Any]
    created: bool = False


class GeometryCreator:
    """几何创建器

    负责根据设计意图在Creo中创建3D几何体
    """

    def __init__(self, creo_connector: CreoConnector):
        """初始化几何创建器

        Args:
            creo_connector: Creo连接器实例
        """
        self.creo_connector = creo_connector
        self.logger = get_logger(self.__class__.__name__)

        # 当前模型信息
        self.current_model: Optional[ModelInfo] = None

    def create_from_intent(self, intent: DesignIntent) -> ModelInfo:
        """根据设计意图创建几何体

        Args:
            intent: 设计意图对象

        Returns:
            ModelInfo: 创建的模型信息
        """
        try:
            self.logger.info(f"开始创建几何体: {intent.object_type}")

            # 确保Creo连接
            if not self.creo_connector.is_connected:
                if not self.creo_connector.connect():
                    raise RuntimeError("无法连接到Creo")

            # 创建新模型
            model_name = self._generate_model_name(intent.object_type)
            self._create_new_model(model_name)

            # 根据对象类型选择创建策略
            if intent.object_type == "杯子":
                model_info = self._create_cup(intent, model_name)
            elif intent.object_type == "盒子":
                model_info = self._create_box(intent, model_name)
            elif intent.object_type == "支架":
                model_info = self._create_bracket(intent, model_name)
            else:
                model_info = self._create_generic_object(intent, model_name)

            self.current_model = model_info
            self.logger.info(f"✅ 几何体创建完成: {model_name}")

            return model_info

        except Exception as e:
            self.logger.error(f"几何体创建失败: {e}")
            raise

    def _generate_model_name(self, object_type: str) -> str:
        """生成模型名称"""
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{object_type}_{timestamp}"

    def _create_new_model(self, model_name: str):
        """创建新的Creo模型"""
        try:
            # session = self.creo_connector.session

            # 创建新的零件模型
            # 注意：这里需要根据实际的Creo API调整
            self.logger.info(f"创建新模型: {model_name}")

            # 示例代码（需要根据实际Creo COM API调整）
            # model = session.CreateModel(model_name, "Part")
            # session.CurrentModel = model

        except Exception as e:
            self.logger.error(f"创建新模型失败: {e}")
            raise

    def _create_cup(self, intent: DesignIntent, model_name: str) -> ModelInfo:
        """创建杯子几何体"""
        try:
            self.logger.info("创建杯子几何体")

            # 获取尺寸参数
            height = intent.dimensions.get("height", 100)
            diameter = intent.dimensions.get("diameter", 80)
            thickness = intent.dimensions.get("thickness", 2)

            features = []

            # 1. 创建外部圆柱体
            self.logger.info("创建外部圆柱体")
            self._create_cylinder(diameter=diameter, height=height, name="外壳")
            features.append("外部圆柱体")

            # 2. 创建内部空腔
            self.logger.info("创建内部空腔")
            inner_diameter = diameter - 2 * thickness
            inner_height = height - thickness

            self._create_cylinder(
                diameter=inner_diameter,
                height=inner_height,
                name="内腔",
                operation="cut",  # 切除操作
            )
            features.append("内部空腔")

            # 3. 添加手柄（如果需要）
            if "手柄" in intent.features:
                self.logger.info("添加手柄")
                self._create_handle(diameter, height)
                features.append("手柄")

            # 4. 倒角处理
            self.logger.info("添加倒角")
            self._add_fillets(["杯口", "底部"])
            features.append("倒角")

            return ModelInfo(
                name=model_name,
                type="杯子",
                features=features,
                parameters=intent.dimensions,
                created=True,
            )

        except Exception as e:
            self.logger.error(f"创建杯子失败: {e}")
            raise

    def _create_box(self, intent: DesignIntent, model_name: str) -> ModelInfo:
        """创建盒子几何体"""
        try:
            self.logger.info("创建盒子几何体")

            # 获取尺寸参数
            length = intent.dimensions.get("length", 200)
            width = intent.dimensions.get("width", 150)
            height = intent.dimensions.get("height", 100)
            thickness = intent.dimensions.get("thickness", 3)

            features = []

            # 1. 创建外部长方体
            self.logger.info("创建外部长方体")
            self._create_box_primitive(
                length=length, width=width, height=height, name="外壳"
            )
            features.append("外部长方体")

            # 2. 创建内部空腔
            self.logger.info("创建内部空腔")
            inner_length = length - 2 * thickness
            inner_width = width - 2 * thickness
            inner_height = height - thickness

            self._create_box_primitive(
                length=inner_length,
                width=inner_width,
                height=inner_height,
                name="内腔",
                operation="cut",
            )
            features.append("内部空腔")

            # 3. 添加盖子特征（如果需要）
            if "盖子" in intent.features:
                self.logger.info("添加盖子")
                self._create_lid(length, width, thickness)
                features.append("盖子")

            return ModelInfo(
                name=model_name,
                type="盒子",
                features=features,
                parameters=intent.dimensions,
                created=True,
            )

        except Exception as e:
            self.logger.error(f"创建盒子失败: {e}")
            raise

    def _create_bracket(self, intent: DesignIntent, model_name: str) -> ModelInfo:
        """创建支架几何体"""
        try:
            self.logger.info("创建支架几何体")

            # 获取尺寸参数
            height = intent.dimensions.get("height", 150)
            base_diameter = intent.dimensions.get("base_diameter", 100)
            thickness = intent.dimensions.get("thickness", 5)

            features = []

            # 1. 创建底座
            self.logger.info("创建底座")
            self._create_cylinder(
                diameter=base_diameter, height=thickness * 2, name="底座"
            )
            features.append("底座")

            # 2. 创建支撑柱
            self.logger.info("创建支撑柱")
            self._create_cylinder(diameter=thickness * 2, height=height, name="支撑柱")
            features.append("支撑柱")

            # 3. 创建托盘
            self.logger.info("创建托盘")
            self._create_cylinder(
                diameter=base_diameter * 0.8, height=thickness, name="托盘"
            )
            features.append("托盘")

            return ModelInfo(
                name=model_name,
                type="支架",
                features=features,
                parameters=intent.dimensions,
                created=True,
            )

        except Exception as e:
            self.logger.error(f"创建支架失败: {e}")
            raise

    def _create_generic_object(
        self, intent: DesignIntent, model_name: str
    ) -> ModelInfo:
        """创建通用对象"""
        try:
            self.logger.info(f"创建通用对象: {intent.object_type}")

            # 创建基础长方体
            length = intent.dimensions.get("length", 100)
            width = intent.dimensions.get("width", 100)
            height = intent.dimensions.get("height", 100)

            self._create_box_primitive(
                length=length, width=width, height=height, name="基础形状"
            )

            return ModelInfo(
                name=model_name,
                type=intent.object_type,
                features=["基础几何体"],
                parameters=intent.dimensions,
                created=True,
            )

        except Exception as e:
            self.logger.error(f"创建通用对象失败: {e}")
            raise

    def _create_cylinder(
        self, diameter: float, height: float, name: str, operation: str = "add"
    ) -> Any:
        """创建圆柱体特征"""
        try:
            self.logger.debug(f"创建圆柱体: {name}, 直径={diameter}, 高度={height}")

            # 这里需要实际的Creo API调用
            # 示例代码结构：
            # session = self.creo_connector.session
            # feature = session.CreateCylinder(diameter/2, height)
            # if operation == "cut":
            #     feature.SetOperation("Cut")

            # 暂时返回模拟对象
            return {
                "type": "cylinder",
                "name": name,
                "diameter": diameter,
                "height": height,
                "operation": operation,
            }

        except Exception as e:
            self.logger.error(f"创建圆柱体失败: {e}")
            raise

    def _create_box_primitive(
        self,
        length: float,
        width: float,
        height: float,
        name: str,
        operation: str = "add",
    ) -> Any:
        """创建长方体特征"""
        try:
            self.logger.debug(f"创建长方体: {name}, 尺寸={length}x{width}x{height}")

            # 这里需要实际的Creo API调用
            # 示例代码结构：
            # session = self.creo_connector.session
            # feature = session.CreateBox(length, width, height)
            # if operation == "cut":
            #     feature.SetOperation("Cut")

            # 暂时返回模拟对象
            return {
                "type": "box",
                "name": name,
                "length": length,
                "width": width,
                "height": height,
                "operation": operation,
            }

        except Exception as e:
            self.logger.error(f"创建长方体失败: {e}")
            raise

    def _create_handle(self, cup_diameter: float, cup_height: float) -> Any:
        """创建手柄特征"""
        try:
            self.logger.debug("创建手柄特征")

            # 计算手柄参数
            handle_width = cup_diameter * 0.3
            handle_height = cup_height * 0.6
            handle_thickness = 8

            # 这里需要实际的Creo API调用来创建复杂的手柄几何体
            # 可能需要使用扫描、混合等高级特征

            return {
                "type": "handle",
                "width": handle_width,
                "height": handle_height,
                "thickness": handle_thickness,
            }

        except Exception as e:
            self.logger.error(f"创建手柄失败: {e}")
            raise

    def _create_lid(self, box_length: float, box_width: float, thickness: float) -> Any:
        """创建盖子特征"""
        try:
            self.logger.debug("创建盖子特征")

            # 盖子稍大于盒子开口
            lid_length = box_length + 2
            lid_width = box_width + 2
            lid_height = thickness

            return self._create_box_primitive(
                length=lid_length, width=lid_width, height=lid_height, name="盖子"
            )

        except Exception as e:
            self.logger.error(f"创建盖子失败: {e}")
            raise

    def _add_fillets(self, edge_names: List[str], radius: float = 2.0):
        """添加倒角/圆角"""
        try:
            self.logger.debug(f"添加倒角: {edge_names}, 半径={radius}")

            # 这里需要实际的Creo API调用
            # 示例代码结构：
            # for edge_name in edge_names:
            #     edge = session.FindEdge(edge_name)
            #     session.CreateFillet(edge, radius)

        except Exception as e:
            self.logger.error(f"添加倒角失败: {e}")
            raise

    def get_model_info(self) -> Optional[ModelInfo]:
        """获取当前模型信息"""
        return self.current_model

    def save_model(self, file_path: str = None) -> bool:
        """保存模型

        Args:
            file_path: 保存路径，如果为None则使用默认路径

        Returns:
            bool: 保存是否成功
        """
        try:
            if not self.current_model:
                self.logger.warning("没有当前模型可保存")
                return False

            # 这里需要实际的Creo API调用
            # session = self.creo_connector.session
            # if file_path:
            #     session.SaveModel(file_path)
            # else:
            #     session.SaveModel()

            self.logger.info(f"模型已保存: {self.current_model.name}")
            return True

        except Exception as e:
            self.logger.error(f"保存模型失败: {e}")
            return False
