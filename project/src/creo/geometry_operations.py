#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 几何操作模块
"""

import math
from dataclasses import dataclass
from typing import Any, Dict, Tuple

from src.utils.logger import get_logger

from .api_wrapper import CreoAPIWrapper


@dataclass
class GeometryParams:
    """几何参数数据类"""

    shape_type: str  # 形状类型：cylinder, box, sphere等
    dimensions: Dict[str, float]  # 尺寸参数
    position: Tuple[float, float, float] = (0, 0, 0)  # 位置
    rotation: Tuple[float, float, float] = (0, 0, 0)  # 旋转角度
    material: str = "Steel"  # 材料


@dataclass
class CylinderParams(GeometryParams):
    """圆柱体参数"""

    def __init__(
        self,
        diameter: float,
        height: float,
        position: Tuple[float, float, float] = (0, 0, 0),
        material: str = "Steel",
    ):
        dimensions = {"diameter": diameter, "height": height, "radius": diameter / 2}
        super().__init__("cylinder", dimensions, position, (0, 0, 0), material)


class GeometryOperations:
    """几何操作类

    提供各种几何体的创建和操作功能
    """

    def __init__(self, api_wrapper: CreoAPIWrapper = None):
        """初始化几何操作

        Args:
            api_wrapper: Creo API封装器实例
        """
        self.api = api_wrapper or CreoAPIWrapper()
        self.logger = get_logger(self.__class__.__name__)

        # 材料映射表
        self.material_mapping = {
            "不锈钢": "Stainless Steel",
            "钢": "Steel",
            "铝": "Aluminum",
            "铜": "Copper",
            "塑料": "Plastic",
            "橡胶": "Rubber",
        }

    def create_cylinder(
        self,
        diameter: float,
        height: float,
        material: str = "Steel",
        position: Tuple[float, float, float] = (0, 0, 0),
    ) -> bool:
        """创建圆柱体

        Args:
            diameter: 直径（厘米）
            height: 高度（厘米）
            material: 材料名称
            position: 位置坐标

        Returns:
            bool: 创建是否成功
        """
        try:
            # 转换单位：厘米到毫米
            diameter_mm = diameter * 10
            height_mm = height * 10

            # 转换材料名称
            creo_material = self.material_mapping.get(material, material)

            self.logger.info(
                f"开始创建圆柱体: 直径{diameter}cm, 高度{height}cm, 材料{material}"
            )

            # 创建圆柱体
            success = self.api.create_cylinder(
                diameter=diameter_mm, height=height_mm, position=position
            )

            if success:
                # 设置材料
                self.api.set_material(creo_material)
                self.logger.info("圆柱体创建成功")
                return True
            else:
                self.logger.error("圆柱体创建失败")
                return False

        except Exception as e:
            self.logger.error(f"创建圆柱体时发生错误: {e}")
            return False

    def create_box(
        self,
        length: float,
        width: float,
        height: float,
        material: str = "Steel",
        position: Tuple[float, float, float] = (0, 0, 0),
    ) -> bool:
        """创建长方体

        Args:
            length: 长度（厘米）
            width: 宽度（厘米）
            height: 高度（厘米）
            material: 材料名称
            position: 位置坐标

        Returns:
            bool: 创建是否成功
        """
        try:
            # 转换单位：厘米到毫米
            length_mm = length * 10
            width_mm = width * 10
            height_mm = height * 10

            # 转换材料名称
            creo_material = self.material_mapping.get(material, material)

            self.logger.info(
                f"开始创建长方体: {length}x{width}x{height}cm "
                f"({length_mm}x{width_mm}x{height_mm}mm), 材料{creo_material}"
            )

            # 这里需要实现长方体创建逻辑
            # 暂时返回True作为占位符
            self.logger.info("长方体创建功能待实现")
            return True

        except Exception as e:
            self.logger.error(f"创建长方体时发生错误: {e}")
            return False

    def create_sphere(
        self,
        diameter: float,
        material: str = "Steel",
        position: Tuple[float, float, float] = (0, 0, 0),
    ) -> bool:
        """创建球体

        Args:
            diameter: 直径（厘米）
            material: 材料名称
            position: 位置坐标

        Returns:
            bool: 创建是否成功
        """
        try:
            # 转换单位：厘米到毫米
            diameter_mm = diameter * 10

            # 转换材料名称
            creo_material = self.material_mapping.get(material, material)

            self.logger.info(
                f"开始创建球体: 直径{diameter}cm ({diameter_mm}mm), 材料{creo_material}"
            )

            # 这里需要实现球体创建逻辑
            # 暂时返回True作为占位符
            self.logger.info("球体创建功能待实现")
            return True

        except Exception as e:
            self.logger.error(f"创建球体时发生错误: {e}")
            return False

    def calculate_volume(self, geometry_params: GeometryParams) -> float:
        """计算几何体体积

        Args:
            geometry_params: 几何参数

        Returns:
            float: 体积（立方厘米）
        """
        try:
            if geometry_params.shape_type == "cylinder":
                radius = geometry_params.dimensions["radius"] / 10  # 转换为厘米
                height = geometry_params.dimensions["height"] / 10  # 转换为厘米
                volume = math.pi * radius * radius * height
                return volume

            elif geometry_params.shape_type == "box":
                length = geometry_params.dimensions["length"] / 10
                width = geometry_params.dimensions["width"] / 10
                height = geometry_params.dimensions["height"] / 10
                volume = length * width * height
                return volume

            elif geometry_params.shape_type == "sphere":
                radius = geometry_params.dimensions["radius"] / 10
                volume = (4 / 3) * math.pi * radius * radius * radius
                return volume

            else:
                self.logger.warning(f"未知的几何体类型: {geometry_params.shape_type}")
                return 0.0

        except Exception as e:
            self.logger.error(f"计算体积时发生错误: {e}")
            return 0.0

    def calculate_surface_area(self, geometry_params: GeometryParams) -> float:
        """计算几何体表面积

        Args:
            geometry_params: 几何参数

        Returns:
            float: 表面积（平方厘米）
        """
        try:
            if geometry_params.shape_type == "cylinder":
                radius = geometry_params.dimensions["radius"] / 10  # 转换为厘米
                height = geometry_params.dimensions["height"] / 10  # 转换为厘米
                # 圆柱体表面积 = 2πr² + 2πrh
                surface_area = (
                    2 * math.pi * radius * radius + 2 * math.pi * radius * height
                )
                return surface_area

            elif geometry_params.shape_type == "box":
                length = geometry_params.dimensions["length"] / 10
                width = geometry_params.dimensions["width"] / 10
                height = geometry_params.dimensions["height"] / 10
                # 长方体表面积 = 2(lw + lh + wh)
                surface_area = 2 * (length * width + length * height + width * height)
                return surface_area

            elif geometry_params.shape_type == "sphere":
                radius = geometry_params.dimensions["radius"] / 10
                # 球体表面积 = 4πr²
                surface_area = 4 * math.pi * radius * radius
                return surface_area

            else:
                self.logger.warning(f"未知的几何体类型: {geometry_params.shape_type}")
                return 0.0

        except Exception as e:
            self.logger.error(f"计算表面积时发生错误: {e}")
            return 0.0

    def get_material_properties(self, material_name: str) -> Dict[str, Any]:
        """获取材料属性

        Args:
            material_name: 材料名称

        Returns:
            Dict: 材料属性字典
        """
        # 材料属性数据库（简化版）
        material_properties = {
            "不锈钢": {
                "density": 7.93,  # g/cm³
                "young_modulus": 200,  # GPa
                "yield_strength": 205,  # MPa
                "thermal_conductivity": 16.2,  # W/m·K
            },
            "钢": {
                "density": 7.85,
                "young_modulus": 210,
                "yield_strength": 250,
                "thermal_conductivity": 50,
            },
            "铝": {
                "density": 2.70,
                "young_modulus": 70,
                "yield_strength": 95,
                "thermal_conductivity": 237,
            },
        }

        return material_properties.get(
            material_name,
            {
                "density": 1.0,
                "young_modulus": 1.0,
                "yield_strength": 1.0,
                "thermal_conductivity": 1.0,
            },
        )

    def calculate_mass(self, geometry_params: GeometryParams) -> float:
        """计算几何体质量

        Args:
            geometry_params: 几何参数

        Returns:
            float: 质量（克）
        """
        try:
            volume = self.calculate_volume(geometry_params)  # 立方厘米
            material_props = self.get_material_properties(geometry_params.material)
            density = material_props["density"]  # g/cm³

            mass = volume * density  # 克
            return mass

        except Exception as e:
            self.logger.error(f"计算质量时发生错误: {e}")
            return 0.0
