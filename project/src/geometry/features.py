#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 几何特征操作
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from src.geometry.primitives import Plane, Point3D, Vector3D
from src.utils.logger import get_logger


class FeatureType(Enum):
    """特征类型"""

    EXTRUDE = "extrude"  # 拉伸
    REVOLVE = "revolve"  # 旋转
    SWEEP = "sweep"  # 扫描
    BLEND = "blend"  # 混合
    FILLET = "fillet"  # 圆角
    CHAMFER = "chamfer"  # 倒角
    SHELL = "shell"  # 抽壳
    PATTERN = "pattern"  # 阵列
    MIRROR = "mirror"  # 镜像
    HOLE = "hole"  # 孔
    THREAD = "thread"  # 螺纹
    RIB = "rib"  # 筋
    DRAFT = "draft"  # 拔模


class PatternType(Enum):
    """阵列类型"""

    LINEAR = "linear"  # 线性阵列
    CIRCULAR = "circular"  # 环形阵列
    RECTANGULAR = "rectangular"  # 矩形阵列
    CURVE = "curve"  # 曲线阵列


@dataclass
class ExtrudeParams:
    """拉伸参数"""

    sketch_name: str
    depth: float
    direction: Vector3D = None
    draft_angle: float = 0.0  # 拔模角度（度）
    taper_angle: float = 0.0  # 锥度角（度）

    def __post_init__(self):
        if self.direction is None:
            self.direction = Vector3D(0, 0, 1)


@dataclass
class RevolveParams:
    """旋转参数"""

    sketch_name: str
    axis_point: Point3D
    axis_direction: Vector3D
    angle: float = 360.0  # 旋转角度（度）

    def __post_init__(self):
        if self.axis_direction:
            self.axis_direction = self.axis_direction.normalize()


@dataclass
class SweepParams:
    """扫描参数"""

    sketch_name: str
    path_name: str
    twist_angle: float = 0.0  # 扭转角度（度）
    scale_factor: float = 1.0  # 缩放因子


@dataclass
class FilletParams:
    """圆角参数"""

    edge_names: List[str]
    radius: float
    variable_radius: bool = False
    radius_values: List[float] = None  # 可变半径值


@dataclass
class ChamferParams:
    """倒角参数"""

    edge_names: List[str]
    distance: float
    angle: float = 45.0  # 倒角角度（度）
    distance2: Optional[float] = None  # 第二个距离（不等距倒角）


@dataclass
class ShellParams:
    """抽壳参数"""

    thickness: float
    remove_faces: List[str] = None  # 要移除的面

    def __post_init__(self):
        if self.remove_faces is None:
            self.remove_faces = []


@dataclass
class PatternParams:
    """阵列参数"""

    feature_names: List[str]
    pattern_type: PatternType
    count: int
    spacing: float = None
    angle: float = None
    direction: Vector3D = None
    center_point: Point3D = None


@dataclass
class HoleParams:
    """孔参数"""

    position: Point3D
    diameter: float
    depth: float
    hole_type: str = "simple"  # simple, counterbore, countersink
    counterbore_diameter: float = None
    counterbore_depth: float = None
    countersink_angle: float = 90.0


class FeatureOperations:
    """几何特征操作类

    提供各种高级几何特征的创建和操作方法
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.feature_history: List[Dict[str, Any]] = []

    def create_extrude(self, params: ExtrudeParams) -> Dict[str, Any]:
        """创建拉伸特征

        Args:
            params: 拉伸参数

        Returns:
            Dict: 拉伸特征定义
        """
        try:
            self.logger.debug(
                f"创建拉伸特征: {params.sketch_name}, 深度={params.depth}"
            )

            # 验证参数
            if params.depth <= 0:
                raise ValueError("拉伸深度必须大于0")
            if not params.sketch_name:
                raise ValueError("必须指定草图名称")

            feature_def = {
                "type": "extrude",
                "name": f"拉伸_{params.sketch_name}",
                "parameters": {
                    "sketch_name": params.sketch_name,
                    "depth": params.depth,
                    "direction": {
                        "x": params.direction.x,
                        "y": params.direction.y,
                        "z": params.direction.z,
                    },
                    "draft_angle": params.draft_angle,
                    "taper_angle": params.taper_angle,
                },
                "feature_type": FeatureType.EXTRUDE.value,
            }

            self.feature_history.append(feature_def)
            return feature_def

        except Exception as e:
            self.logger.error(f"创建拉伸特征失败: {e}")
            raise

    def create_revolve(self, params: RevolveParams) -> Dict[str, Any]:
        """创建旋转特征

        Args:
            params: 旋转参数

        Returns:
            Dict: 旋转特征定义
        """
        try:
            self.logger.debug(
                f"创建旋转特征: {params.sketch_name}, 角度={params.angle}"
            )

            # 验证参数
            if not params.sketch_name:
                raise ValueError("必须指定草图名称")
            if params.angle <= 0 or params.angle > 360:
                raise ValueError("旋转角度必须在0-360度之间")

            feature_def = {
                "type": "revolve",
                "name": f"旋转_{params.sketch_name}",
                "parameters": {
                    "sketch_name": params.sketch_name,
                    "axis_point": {
                        "x": params.axis_point.x,
                        "y": params.axis_point.y,
                        "z": params.axis_point.z,
                    },
                    "axis_direction": {
                        "x": params.axis_direction.x,
                        "y": params.axis_direction.y,
                        "z": params.axis_direction.z,
                    },
                    "angle": params.angle,
                },
                "feature_type": FeatureType.REVOLVE.value,
            }

            self.feature_history.append(feature_def)
            return feature_def

        except Exception as e:
            self.logger.error(f"创建旋转特征失败: {e}")
            raise

    def create_sweep(self, params: SweepParams) -> Dict[str, Any]:
        """创建扫描特征

        Args:
            params: 扫描参数

        Returns:
            Dict: 扫描特征定义
        """
        try:
            self.logger.debug(
                f"创建扫描特征: {params.sketch_name} 沿 {params.path_name}"
            )

            # 验证参数
            if not params.sketch_name or not params.path_name:
                raise ValueError("必须指定草图名称和路径名称")

            feature_def = {
                "type": "sweep",
                "name": f"扫描_{params.sketch_name}",
                "parameters": {
                    "sketch_name": params.sketch_name,
                    "path_name": params.path_name,
                    "twist_angle": params.twist_angle,
                    "scale_factor": params.scale_factor,
                },
                "feature_type": FeatureType.SWEEP.value,
            }

            self.feature_history.append(feature_def)
            return feature_def

        except Exception as e:
            self.logger.error(f"创建扫描特征失败: {e}")
            raise

    def create_fillet(self, params: FilletParams) -> Dict[str, Any]:
        """创建圆角特征

        Args:
            params: 圆角参数

        Returns:
            Dict: 圆角特征定义
        """
        try:
            self.logger.debug(
                f"创建圆角特征: {len(params.edge_names)}条边, 半径={params.radius}"
            )

            # 验证参数
            if not params.edge_names:
                raise ValueError("必须指定至少一条边")
            if params.radius <= 0:
                raise ValueError("圆角半径必须大于0")

            feature_def = {
                "type": "fillet",
                "name": f"圆角_R{params.radius}",
                "parameters": {
                    "edge_names": params.edge_names,
                    "radius": params.radius,
                    "variable_radius": params.variable_radius,
                    "radius_values": params.radius_values or [],
                },
                "feature_type": FeatureType.FILLET.value,
            }

            self.feature_history.append(feature_def)
            return feature_def

        except Exception as e:
            self.logger.error(f"创建圆角特征失败: {e}")
            raise

    def create_chamfer(self, params: ChamferParams) -> Dict[str, Any]:
        """创建倒角特征

        Args:
            params: 倒角参数

        Returns:
            Dict: 倒角特征定义
        """
        try:
            self.logger.debug(
                f"创建倒角特征: {len(params.edge_names)}条边, 距离={params.distance}"
            )

            # 验证参数
            if not params.edge_names:
                raise ValueError("必须指定至少一条边")
            if params.distance <= 0:
                raise ValueError("倒角距离必须大于0")

            feature_def = {
                "type": "chamfer",
                "name": f"倒角_{params.distance}",
                "parameters": {
                    "edge_names": params.edge_names,
                    "distance": params.distance,
                    "angle": params.angle,
                    "distance2": params.distance2,
                },
                "feature_type": FeatureType.CHAMFER.value,
            }

            self.feature_history.append(feature_def)
            return feature_def

        except Exception as e:
            self.logger.error(f"创建倒角特征失败: {e}")
            raise

    def create_shell(self, params: ShellParams) -> Dict[str, Any]:
        """创建抽壳特征

        Args:
            params: 抽壳参数

        Returns:
            Dict: 抽壳特征定义
        """
        try:
            self.logger.debug(f"创建抽壳特征: 厚度={params.thickness}")

            # 验证参数
            if params.thickness <= 0:
                raise ValueError("抽壳厚度必须大于0")

            feature_def = {
                "type": "shell",
                "name": f"抽壳_{params.thickness}",
                "parameters": {
                    "thickness": params.thickness,
                    "remove_faces": params.remove_faces,
                },
                "feature_type": FeatureType.SHELL.value,
            }

            self.feature_history.append(feature_def)
            return feature_def

        except Exception as e:
            self.logger.error(f"创建抽壳特征失败: {e}")
            raise

    def create_pattern(self, params: PatternParams) -> Dict[str, Any]:
        """创建阵列特征

        Args:
            params: 阵列参数

        Returns:
            Dict: 阵列特征定义
        """
        try:
            self.logger.debug(f"创建{params.pattern_type.value}阵列: {params.count}个")

            # 验证参数
            if not params.feature_names:
                raise ValueError("必须指定要阵列的特征")
            if params.count <= 1:
                raise ValueError("阵列数量必须大于1")

            feature_def = {
                "type": "pattern",
                "name": f"{params.pattern_type.value}阵列_{params.count}",
                "parameters": {
                    "feature_names": params.feature_names,
                    "pattern_type": params.pattern_type.value,
                    "count": params.count,
                    "spacing": params.spacing,
                    "angle": params.angle,
                    "direction": (
                        {
                            "x": params.direction.x if params.direction else 0,
                            "y": params.direction.y if params.direction else 0,
                            "z": params.direction.z if params.direction else 0,
                        }
                        if params.direction
                        else None
                    ),
                    "center_point": (
                        {
                            "x": params.center_point.x if params.center_point else 0,
                            "y": params.center_point.y if params.center_point else 0,
                            "z": params.center_point.z if params.center_point else 0,
                        }
                        if params.center_point
                        else None
                    ),
                },
                "feature_type": FeatureType.PATTERN.value,
            }

            self.feature_history.append(feature_def)
            return feature_def

        except Exception as e:
            self.logger.error(f"创建阵列特征失败: {e}")
            raise

    def create_hole(self, params: HoleParams) -> Dict[str, Any]:
        """创建孔特征

        Args:
            params: 孔参数

        Returns:
            Dict: 孔特征定义
        """
        try:
            self.logger.debug(
                f"创建{params.hole_type}孔: 直径={params.diameter}, 深度={params.depth}"
            )

            # 验证参数
            if params.diameter <= 0:
                raise ValueError("孔直径必须大于0")
            if params.depth <= 0:
                raise ValueError("孔深度必须大于0")

            feature_def = {
                "type": "hole",
                "name": f"{params.hole_type}孔_D{params.diameter}",
                "parameters": {
                    "position": {
                        "x": params.position.x,
                        "y": params.position.y,
                        "z": params.position.z,
                    },
                    "diameter": params.diameter,
                    "depth": params.depth,
                    "hole_type": params.hole_type,
                    "counterbore_diameter": params.counterbore_diameter,
                    "counterbore_depth": params.counterbore_depth,
                    "countersink_angle": params.countersink_angle,
                },
                "feature_type": FeatureType.HOLE.value,
            }

            self.feature_history.append(feature_def)
            return feature_def

        except Exception as e:
            self.logger.error(f"创建孔特征失败: {e}")
            raise

    def create_mirror(
        self, feature_names: List[str], mirror_plane: Plane
    ) -> Dict[str, Any]:
        """创建镜像特征

        Args:
            feature_names: 要镜像的特征名称列表
            mirror_plane: 镜像平面

        Returns:
            Dict: 镜像特征定义
        """
        try:
            self.logger.debug(f"创建镜像特征: {len(feature_names)}个特征")

            # 验证参数
            if not feature_names:
                raise ValueError("必须指定要镜像的特征")

            feature_def = {
                "type": "mirror",
                "name": f"镜像_{len(feature_names)}特征",
                "parameters": {
                    "feature_names": feature_names,
                    "mirror_plane": {
                        "origin": {
                            "x": mirror_plane.origin.x,
                            "y": mirror_plane.origin.y,
                            "z": mirror_plane.origin.z,
                        },
                        "normal": {
                            "x": mirror_plane.normal.x,
                            "y": mirror_plane.normal.y,
                            "z": mirror_plane.normal.z,
                        },
                    },
                },
                "feature_type": FeatureType.MIRROR.value,
            }

            self.feature_history.append(feature_def)
            return feature_def

        except Exception as e:
            self.logger.error(f"创建镜像特征失败: {e}")
            raise

    def get_feature_history(self) -> List[Dict[str, Any]]:
        """获取特征历史记录

        Returns:
            List: 特征历史记录列表
        """
        return self.feature_history.copy()

    def clear_feature_history(self):
        """清空特征历史记录"""
        self.feature_history.clear()
        self.logger.info("特征历史记录已清空")

    def validate_feature_sequence(self, features: List[Dict[str, Any]]) -> bool:
        """验证特征序列的有效性

        Args:
            features: 特征列表

        Returns:
            bool: 序列是否有效
        """
        try:
            # 检查特征依赖关系
            feature_names = set()

            for feature in features:
                feature_type = feature.get("feature_type")
                feature_name = feature.get("name")

                if not feature_name:
                    self.logger.error("特征缺少名称")
                    return False

                if feature_name in feature_names:
                    self.logger.error(f"特征名称重复: {feature_name}")
                    return False

                feature_names.add(feature_name)

                # 检查特征类型特定的依赖
                if feature_type in [
                    FeatureType.PATTERN.value,
                    FeatureType.MIRROR.value,
                ]:
                    referenced_features = feature.get("parameters", {}).get(
                        "feature_names", []
                    )
                    for ref_feature in referenced_features:
                        if ref_feature not in feature_names:
                            self.logger.error(
                                f"特征 {feature_name} 引用了不存在的特征: {ref_feature}"
                            )
                            return False

            return True

        except Exception as e:
            self.logger.error(f"验证特征序列失败: {e}")
            return False

    def optimize_feature_sequence(
        self, features: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """优化特征序列

        Args:
            features: 原始特征列表

        Returns:
            List: 优化后的特征列表
        """
        try:
            self.logger.debug("优化特征序列")

            # 简单的优化策略：将基础几何体放在前面，修饰特征放在后面
            base_features = []
            modification_features = []

            for feature in features:
                feature_type = feature.get("feature_type")

                if feature_type in [
                    FeatureType.EXTRUDE.value,
                    FeatureType.REVOLVE.value,
                    FeatureType.SWEEP.value,
                    FeatureType.BLEND.value,
                ]:
                    base_features.append(feature)
                else:
                    modification_features.append(feature)

            # 在修饰特征中，圆角和倒角通常放在最后
            finishing_features = []
            other_modifications = []

            for feature in modification_features:
                feature_type = feature.get("feature_type")
                if feature_type in [
                    FeatureType.FILLET.value,
                    FeatureType.CHAMFER.value,
                ]:
                    finishing_features.append(feature)
                else:
                    other_modifications.append(feature)

            optimized_sequence = (
                base_features + other_modifications + finishing_features
            )

            self.logger.info(
                f"特征序列优化完成: {len(features)} -> {len(optimized_sequence)}"
            )
            return optimized_sequence

        except Exception as e:
            self.logger.error(f"优化特征序列失败: {e}")
            return features
