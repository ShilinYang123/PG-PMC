#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 基础几何形状
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from src.utils.logger import get_logger


class ShapeType(Enum):
    """几何形状类型"""

    CYLINDER = "cylinder"
    BOX = "box"
    SPHERE = "sphere"
    CONE = "cone"
    TORUS = "torus"
    EXTRUDE = "extrude"
    REVOLVE = "revolve"
    SWEEP = "sweep"
    BLEND = "blend"


class OperationType(Enum):
    """操作类型"""

    ADD = "add"  # 添加材料
    CUT = "cut"  # 切除材料
    INTERSECT = "intersect"  # 求交
    UNION = "union"  # 合并


@dataclass
class Point3D:
    """三维点"""

    x: float
    y: float
    z: float

    def __str__(self) -> str:
        return f"({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"


@dataclass
class Vector3D:
    """三维向量"""

    x: float
    y: float
    z: float

    def normalize(self) -> "Vector3D":
        """归一化向量"""
        length = math.sqrt(self.x**2 + self.y**2 + self.z**2)
        if length == 0:
            return Vector3D(0, 0, 0)
        return Vector3D(self.x / length, self.y / length, self.z / length)

    def __str__(self) -> str:
        return f"<{self.x:.2f}, {self.y:.2f}, {self.z:.2f}>"


@dataclass
class Plane:
    """平面定义"""

    origin: Point3D
    normal: Vector3D

    def __str__(self) -> str:
        return f"Plane(origin={self.origin}, normal={self.normal})"


@dataclass
class GeometryParameters:
    """几何参数基类"""

    name: str
    shape_type: ShapeType
    operation: OperationType = OperationType.ADD
    position: Point3D = None

    def __post_init__(self):
        if self.position is None:
            self.position = Point3D(0, 0, 0)


@dataclass
class CylinderParams(GeometryParameters):
    """圆柱体参数"""

    radius: float
    height: float
    axis: Vector3D = None

    def __post_init__(self):
        super().__post_init__()
        if self.axis is None:
            self.axis = Vector3D(0, 0, 1)  # 默认Z轴方向
        self.shape_type = ShapeType.CYLINDER

    @property
    def diameter(self) -> float:
        return self.radius * 2

    @diameter.setter
    def diameter(self, value: float):
        self.radius = value / 2


@dataclass
class BoxParams(GeometryParameters):
    """长方体参数"""

    length: float  # X方向
    width: float  # Y方向
    height: float  # Z方向

    def __post_init__(self):
        super().__post_init__()
        self.shape_type = ShapeType.BOX

    @property
    def volume(self) -> float:
        return self.length * self.width * self.height


@dataclass
class SphereParams(GeometryParameters):
    """球体参数"""

    radius: float

    def __post_init__(self):
        super().__post_init__()
        self.shape_type = ShapeType.SPHERE

    @property
    def diameter(self) -> float:
        return self.radius * 2

    @property
    def volume(self) -> float:
        return (4 / 3) * math.pi * self.radius**3


@dataclass
class ConeParams(GeometryParameters):
    """圆锥体参数"""

    bottom_radius: float
    top_radius: float
    height: float
    axis: Vector3D = None

    def __post_init__(self):
        super().__post_init__()
        if self.axis is None:
            self.axis = Vector3D(0, 0, 1)
        self.shape_type = ShapeType.CONE

    @property
    def is_cylinder(self) -> bool:
        """是否为圆柱体（上下半径相等）"""
        return abs(self.bottom_radius - self.top_radius) < 1e-6


@dataclass
class TorusParams(GeometryParameters):
    """环形体参数"""

    major_radius: float  # 主半径
    minor_radius: float  # 次半径
    axis: Vector3D = None

    def __post_init__(self):
        super().__post_init__()
        if self.axis is None:
            self.axis = Vector3D(0, 0, 1)
        self.shape_type = ShapeType.TORUS


class PrimitiveShapes:
    """基础几何形状创建器

    提供创建各种基础几何形状的方法
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def create_cylinder(self, params: CylinderParams) -> Dict[str, Any]:
        """创建圆柱体

        Args:
            params: 圆柱体参数

        Returns:
            Dict: 圆柱体特征定义
        """
        try:
            self.logger.debug(
                f"创建圆柱体: {params.name}, 半径={params.radius}, 高度={params.height}"
            )

            # 验证参数
            if params.radius <= 0:
                raise ValueError("圆柱体半径必须大于0")
            if params.height <= 0:
                raise ValueError("圆柱体高度必须大于0")

            feature_def = {
                "type": "cylinder",
                "name": params.name,
                "operation": params.operation.value,
                "parameters": {
                    "radius": params.radius,
                    "diameter": params.diameter,
                    "height": params.height,
                    "position": {
                        "x": params.position.x,
                        "y": params.position.y,
                        "z": params.position.z,
                    },
                    "axis": {
                        "x": params.axis.x,
                        "y": params.axis.y,
                        "z": params.axis.z,
                    },
                },
                "volume": math.pi * params.radius**2 * params.height,
                "surface_area": 2
                * math.pi
                * params.radius
                * (params.radius + params.height),
            }

            return feature_def

        except Exception as e:
            self.logger.error(f"创建圆柱体失败: {e}")
            raise

    def create_box(self, params: BoxParams) -> Dict[str, Any]:
        """创建长方体

        Args:
            params: 长方体参数

        Returns:
            Dict: 长方体特征定义
        """
        try:
            self.logger.debug(
                f"创建长方体: {params.name}, 尺寸={params.length}x{params.width}x{params.height}"
            )

            # 验证参数
            if params.length <= 0 or params.width <= 0 or params.height <= 0:
                raise ValueError("长方体尺寸必须大于0")

            feature_def = {
                "type": "box",
                "name": params.name,
                "operation": params.operation.value,
                "parameters": {
                    "length": params.length,
                    "width": params.width,
                    "height": params.height,
                    "position": {
                        "x": params.position.x,
                        "y": params.position.y,
                        "z": params.position.z,
                    },
                },
                "volume": params.volume,
                "surface_area": 2
                * (
                    params.length * params.width
                    + params.width * params.height
                    + params.height * params.length
                ),
            }

            return feature_def

        except Exception as e:
            self.logger.error(f"创建长方体失败: {e}")
            raise

    def create_sphere(self, params: SphereParams) -> Dict[str, Any]:
        """创建球体

        Args:
            params: 球体参数

        Returns:
            Dict: 球体特征定义
        """
        try:
            self.logger.debug(f"创建球体: {params.name}, 半径={params.radius}")

            # 验证参数
            if params.radius <= 0:
                raise ValueError("球体半径必须大于0")

            feature_def = {
                "type": "sphere",
                "name": params.name,
                "operation": params.operation.value,
                "parameters": {
                    "radius": params.radius,
                    "diameter": params.diameter,
                    "position": {
                        "x": params.position.x,
                        "y": params.position.y,
                        "z": params.position.z,
                    },
                },
                "volume": params.volume,
                "surface_area": 4 * math.pi * params.radius**2,
            }

            return feature_def

        except Exception as e:
            self.logger.error(f"创建球体失败: {e}")
            raise

    def create_cone(self, params: ConeParams) -> Dict[str, Any]:
        """创建圆锥体

        Args:
            params: 圆锥体参数

        Returns:
            Dict: 圆锥体特征定义
        """
        try:
            self.logger.debug(
                f"创建圆锥体: {params.name}, 底半径={params.bottom_radius}, 顶半径={params.top_radius}, 高度={params.height}"
            )

            # 验证参数
            if params.bottom_radius < 0 or params.top_radius < 0:
                raise ValueError("圆锥体半径不能为负数")
            if params.height <= 0:
                raise ValueError("圆锥体高度必须大于0")
            if params.bottom_radius == 0 and params.top_radius == 0:
                raise ValueError("圆锥体底面和顶面半径不能同时为0")

            # 计算体积
            volume = (
                (1 / 3)
                * math.pi
                * params.height
                * (
                    params.bottom_radius**2
                    + params.bottom_radius * params.top_radius
                    + params.top_radius**2
                )
            )

            feature_def = {
                "type": "cone",
                "name": params.name,
                "operation": params.operation.value,
                "parameters": {
                    "bottom_radius": params.bottom_radius,
                    "top_radius": params.top_radius,
                    "height": params.height,
                    "position": {
                        "x": params.position.x,
                        "y": params.position.y,
                        "z": params.position.z,
                    },
                    "axis": {
                        "x": params.axis.x,
                        "y": params.axis.y,
                        "z": params.axis.z,
                    },
                },
                "volume": volume,
                "is_cylinder": params.is_cylinder,
            }

            return feature_def

        except Exception as e:
            self.logger.error(f"创建圆锥体失败: {e}")
            raise

    def create_torus(self, params: TorusParams) -> Dict[str, Any]:
        """创建环形体

        Args:
            params: 环形体参数

        Returns:
            Dict: 环形体特征定义
        """
        try:
            self.logger.debug(
                f"创建环形体: {params.name}, 主半径={params.major_radius}, 次半径={params.minor_radius}"
            )

            # 验证参数
            if params.major_radius <= 0 or params.minor_radius <= 0:
                raise ValueError("环形体半径必须大于0")
            if params.minor_radius >= params.major_radius:
                raise ValueError("次半径必须小于主半径")

            # 计算体积和表面积
            volume = 2 * math.pi**2 * params.major_radius * params.minor_radius**2
            surface_area = 4 * math.pi**2 * params.major_radius * params.minor_radius

            feature_def = {
                "type": "torus",
                "name": params.name,
                "operation": params.operation.value,
                "parameters": {
                    "major_radius": params.major_radius,
                    "minor_radius": params.minor_radius,
                    "position": {
                        "x": params.position.x,
                        "y": params.position.y,
                        "z": params.position.z,
                    },
                    "axis": {
                        "x": params.axis.x,
                        "y": params.axis.y,
                        "z": params.axis.z,
                    },
                },
                "volume": volume,
                "surface_area": surface_area,
            }

            return feature_def

        except Exception as e:
            self.logger.error(f"创建环形体失败: {e}")
            raise

    def validate_parameters(self, params: GeometryParameters) -> bool:
        """验证几何参数

        Args:
            params: 几何参数

        Returns:
            bool: 参数是否有效
        """
        try:
            if not params.name or not params.name.strip():
                self.logger.error("几何体名称不能为空")
                return False

            if params.shape_type == ShapeType.CYLINDER:
                cylinder_params = params
                return cylinder_params.radius > 0 and cylinder_params.height > 0

            elif params.shape_type == ShapeType.BOX:
                box_params = params
                return (
                    box_params.length > 0
                    and box_params.width > 0
                    and box_params.height > 0
                )

            elif params.shape_type == ShapeType.SPHERE:
                sphere_params = params
                return sphere_params.radius > 0

            elif params.shape_type == ShapeType.CONE:
                cone_params = params
                return cone_params.height > 0 and (
                    cone_params.bottom_radius > 0 or cone_params.top_radius > 0
                )

            elif params.shape_type == ShapeType.TORUS:
                torus_params = params
                return (
                    torus_params.major_radius > 0
                    and torus_params.minor_radius > 0
                    and torus_params.minor_radius < torus_params.major_radius
                )

            return True

        except Exception as e:
            self.logger.error(f"参数验证失败: {e}")
            return False

    def get_bounding_box(self, params: GeometryParameters) -> Dict[str, Point3D]:
        """获取几何体的包围盒

        Args:
            params: 几何参数

        Returns:
            Dict: 包围盒的最小点和最大点
        """
        try:
            pos = params.position

            if params.shape_type == ShapeType.CYLINDER:
                cylinder_params = params
                r = cylinder_params.radius
                h = cylinder_params.height
                min_point = Point3D(pos.x - r, pos.y - r, pos.z)
                max_point = Point3D(pos.x + r, pos.y + r, pos.z + h)

            elif params.shape_type == ShapeType.BOX:
                box_params = params
                l, w, h = box_params.length, box_params.width, box_params.height
                min_point = Point3D(pos.x, pos.y, pos.z)
                max_point = Point3D(pos.x + l, pos.y + w, pos.z + h)

            elif params.shape_type == ShapeType.SPHERE:
                sphere_params = params
                r = sphere_params.radius
                min_point = Point3D(pos.x - r, pos.y - r, pos.z - r)
                max_point = Point3D(pos.x + r, pos.y + r, pos.z + r)

            elif params.shape_type == ShapeType.CONE:
                cone_params = params
                max_r = max(cone_params.bottom_radius, cone_params.top_radius)
                h = cone_params.height
                min_point = Point3D(pos.x - max_r, pos.y - max_r, pos.z)
                max_point = Point3D(pos.x + max_r, pos.y + max_r, pos.z + h)

            elif params.shape_type == ShapeType.TORUS:
                torus_params = params
                outer_r = torus_params.major_radius + torus_params.minor_radius
                min_point = Point3D(
                    pos.x - outer_r, pos.y - outer_r, pos.z - torus_params.minor_radius
                )
                max_point = Point3D(
                    pos.x + outer_r, pos.y + outer_r, pos.z + torus_params.minor_radius
                )

            else:
                # 默认包围盒
                min_point = Point3D(pos.x - 50, pos.y - 50, pos.z - 50)
                max_point = Point3D(pos.x + 50, pos.y + 50, pos.z + 50)

            return {"min": min_point, "max": max_point}

        except Exception as e:
            self.logger.error(f"计算包围盒失败: {e}")
            raise

    def calculate_center_of_mass(self, params: GeometryParameters) -> Point3D:
        """计算几何体的质心

        Args:
            params: 几何参数

        Returns:
            Point3D: 质心坐标
        """
        try:
            pos = params.position

            if params.shape_type == ShapeType.CYLINDER:
                cylinder_params = params
                # 圆柱体质心在底面中心上方height/2处
                return Point3D(pos.x, pos.y, pos.z + cylinder_params.height / 2)

            elif params.shape_type == ShapeType.BOX:
                box_params = params
                # 长方体质心在几何中心
                return Point3D(
                    pos.x + box_params.length / 2,
                    pos.y + box_params.width / 2,
                    pos.z + box_params.height / 2,
                )

            elif params.shape_type == ShapeType.SPHERE:
                # 球体质心在球心
                return Point3D(pos.x, pos.y, pos.z)

            elif params.shape_type == ShapeType.CONE:
                cone_params = params
                # 圆锥体质心计算（简化为均匀密度）
                if cone_params.top_radius == 0:  # 标准圆锥
                    z_center = pos.z + cone_params.height / 4
                else:  # 圆台
                    r1, r2 = cone_params.bottom_radius, cone_params.top_radius
                    z_center = pos.z + cone_params.height * (
                        r1**2 + 2 * r1 * r2 + 3 * r2**2
                    ) / (4 * (r1**2 + r1 * r2 + r2**2))
                return Point3D(pos.x, pos.y, z_center)

            elif params.shape_type == ShapeType.TORUS:
                # 环形体质心在环心
                return Point3D(pos.x, pos.y, pos.z)

            else:
                # 默认返回位置点
                return pos

        except Exception as e:
            self.logger.error(f"计算质心失败: {e}")
            return params.position
