#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - Creo API封装器
"""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import pythoncom
    import win32com.client
except ImportError:
    win32com = None
    pythoncom = None

from .connector import CreoConnector, CreoConnectionError
from src.utils.logger import get_logger


class CreoAPIWrapper:
    """Creo API封装器
    
    提供高级的Creo建模功能，包括几何体创建、材料设置等
    """
    
    def __init__(self, connector: CreoConnector = None):
        """初始化API封装器
        
        Args:
            connector: Creo连接器实例
        """
        self.connector = connector or CreoConnector()
        self.logger = get_logger(self.__class__.__name__)
        
    def connect(self) -> bool:
        """连接到Creo
        
        Returns:
            bool: 连接是否成功
        """
        try:
            return self.connector.connect()
        except Exception as e:
            self.logger.error(f"连接Creo失败: {e}")
            return False
    
    def disconnect(self):
        """断开Creo连接"""
        try:
            self.connector.disconnect()
        except Exception as e:
            self.logger.error(f"断开Creo连接失败: {e}")
    
    def create_new_part(self, part_name: str, template: str = "mmns_part_solid") -> bool:
        """创建新零件
        
        Args:
            part_name: 零件名称
            template: 模板名称
            
        Returns:
            bool: 创建是否成功
        """
        try:
            if not self.connector.is_connected:
                raise CreoConnectionError("未连接到Creo")
            
            # 获取Creo应用程序对象
            app = self.connector.application
            
            # 创建新零件
            part = app.FileNew(part_name, template, None)
            
            self.logger.info(f"成功创建零件: {part_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建零件失败: {e}")
            return False
    
    def create_cylinder(self, diameter: float, height: float, 
                       position: Tuple[float, float, float] = (0, 0, 0),
                       axis: Tuple[float, float, float] = (0, 0, 1)) -> bool:
        """创建圆柱体
        
        Args:
            diameter: 直径（毫米）
            height: 高度（毫米）
            position: 位置坐标 (x, y, z)
            axis: 轴向量 (x, y, z)
            
        Returns:
            bool: 创建是否成功
        """
        try:
            if not self.connector.is_connected:
                raise CreoConnectionError("未连接到Creo")
            
            app = self.connector.application
            
            # 获取当前模型
            model = app.CurrentModel
            if not model:
                raise CreoConnectionError("没有打开的模型")
            
            # 创建圆柱体特征
            # 这里使用Creo的特征创建API
            # 具体实现需要根据Creo版本调整
            
            # 创建草图平面
            sketch_plane = self._create_sketch_plane(model, position, axis)
            
            # 创建圆形草图
            circle_sketch = self._create_circle_sketch(model, sketch_plane, diameter/2)
            
            # 拉伸成圆柱体
            cylinder_feature = self._extrude_sketch(model, circle_sketch, height)
            
            self.logger.info(f"成功创建圆柱体: 直径{diameter}mm, 高度{height}mm")
            return True
            
        except Exception as e:
            self.logger.error(f"创建圆柱体失败: {e}")
            return False
    
    def set_material(self, material_name: str) -> bool:
        """设置材料
        
        Args:
            material_name: 材料名称
            
        Returns:
            bool: 设置是否成功
        """
        try:
            if not self.connector.is_connected:
                raise CreoConnectionError("未连接到Creo")
            
            app = self.connector.application
            model = app.CurrentModel
            
            if not model:
                raise CreoConnectionError("没有打开的模型")
            
            # 设置材料属性
            # 这里需要根据Creo的材料API实现
            model.SetMaterialName(material_name)
            
            self.logger.info(f"成功设置材料: {material_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置材料失败: {e}")
            return False
    
    def save_model(self, file_path: str) -> bool:
        """保存模型
        
        Args:
            file_path: 保存路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if not self.connector.is_connected:
                raise CreoConnectionError("未连接到Creo")
            
            app = self.connector.application
            model = app.CurrentModel
            
            if not model:
                raise CreoConnectionError("没有打开的模型")
            
            # 保存模型
            model.Save()
            
            # 如果指定了路径，则另存为
            if file_path:
                model.SaveAs(file_path)
            
            self.logger.info(f"成功保存模型: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存模型失败: {e}")
            return False
    
    def _create_sketch_plane(self, model, position: Tuple[float, float, float], 
                           axis: Tuple[float, float, float]):
        """创建草图平面
        
        Args:
            model: Creo模型对象
            position: 位置坐标
            axis: 轴向量
            
        Returns:
            草图平面对象
        """
        # 这里需要根据Creo API实现草图平面创建
        # 简化实现，使用默认平面
        return model.GetDefaultDatumPlane("TOP")
    
    def _create_circle_sketch(self, model, sketch_plane, radius: float):
        """创建圆形草图
        
        Args:
            model: Creo模型对象
            sketch_plane: 草图平面
            radius: 半径
            
        Returns:
            草图对象
        """
        # 这里需要根据Creo API实现圆形草图创建
        # 简化实现
        sketch = model.CreateSketch(sketch_plane)
        circle = sketch.CreateCircle(0, 0, radius)
        return sketch
    
    def _extrude_sketch(self, model, sketch, height: float):
        """拉伸草图
        
        Args:
            model: Creo模型对象
            sketch: 草图对象
            height: 拉伸高度
            
        Returns:
            拉伸特征对象
        """
        # 这里需要根据Creo API实现拉伸功能
        # 简化实现
        extrude_feature = model.CreateExtrudeFeature(sketch, height)
        return extrude_feature
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取当前模型信息
        
        Returns:
            Dict: 模型信息字典
        """
        try:
            if not self.connector.is_connected:
                return {"error": "未连接到Creo"}
            
            app = self.connector.application
            model = app.CurrentModel
            
            if not model:
                return {"error": "没有打开的模型"}
            
            return {
                "name": model.FileName,
                "type": model.Type,
                "units": model.PrincipalUnits,
                "features_count": model.ListFeatures().Count if hasattr(model, 'ListFeatures') else 0
            }
            
        except Exception as e:
            self.logger.error(f"获取模型信息失败: {e}")
            return {"error": str(e)}