#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 创建圆柱体脚本
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.creo.connector import CreoConnector
from src.creo.api_wrapper import CreoAPIWrapper
from src.creo.geometry_operations import GeometryOperations, CylinderParams
from src.utils.logger import get_logger
from src.config.config_manager import ConfigManager


def create_stainless_steel_cylinder():
    """创建不锈钢圆柱体
    
    规格：直径3cm，高10cm，材料不锈钢
    """
    logger = get_logger("create_cylinder")
    
    try:
        logger.info("开始创建不锈钢圆柱体...")
        
        # 加载配置
        config_manager = ConfigManager()
        settings = config_manager.get_settings()
        
        # 初始化Creo连接器
        connector = CreoConnector(
            creo_path=settings.creo.install_path,
            timeout=settings.creo.connection_timeout
        )
        
        # 初始化API封装器和几何操作
        api_wrapper = CreoAPIWrapper(connector)
        geometry_ops = GeometryOperations(api_wrapper)
        
        # 连接到Creo
        logger.info("正在连接到Creo...")
        if not api_wrapper.connect():
            logger.error("无法连接到Creo，请确保Creo已安装并可访问")
            return False
        
        logger.info("成功连接到Creo")
        
        # 创建新零件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        part_name = f"cylinder_stainless_{timestamp}"
        
        logger.info(f"创建新零件: {part_name}")
        if not api_wrapper.create_new_part(part_name):
            logger.error("创建新零件失败")
            return False
        
        # 创建圆柱体参数
        cylinder_params = CylinderParams(
            diameter=3.0,  # 3厘米
            height=10.0,   # 10厘米
            material="不锈钢"
        )
        
        # 创建圆柱体
        logger.info("创建圆柱体几何体...")
        success = geometry_ops.create_cylinder(
            diameter=cylinder_params.dimensions["diameter"],
            height=cylinder_params.dimensions["height"],
            material=cylinder_params.material
        )
        
        if not success:
            logger.error("创建圆柱体失败")
            return False
        
        # 计算几何属性
        volume = geometry_ops.calculate_volume(cylinder_params)
        surface_area = geometry_ops.calculate_surface_area(cylinder_params)
        mass = geometry_ops.calculate_mass(cylinder_params)
        
        logger.info(f"圆柱体属性:")
        logger.info(f"  - 体积: {volume:.2f} 立方厘米")
        logger.info(f"  - 表面积: {surface_area:.2f} 平方厘米")
        logger.info(f"  - 质量: {mass:.2f} 克")
        
        # 保存模型到指定目录
        output_dir = Path("s:\\PG-Dev\\AI助理生产成果")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"{part_name}.prt"
        
        logger.info(f"保存模型到: {output_file}")
        if api_wrapper.save_model(str(output_file)):
            logger.info("模型保存成功")
        else:
            logger.warning("模型保存失败，但几何体已创建")
        
        # 获取模型信息
        model_info = api_wrapper.get_model_info()
        logger.info(f"模型信息: {model_info}")
        
        logger.info("圆柱体创建完成！")
        return True
        
    except Exception as e:
        logger.error(f"创建圆柱体时发生错误: {e}")
        return False
    
    finally:
        # 断开连接
        try:
            if 'api_wrapper' in locals():
                api_wrapper.disconnect()
                logger.info("已断开Creo连接")
        except Exception as e:
            logger.error(f"断开连接时发生错误: {e}")


def main():
    """主函数"""
    logger = get_logger("main")
    
    print("=" * 60)
    print("PG-Dev AI设计助理 - 圆柱体创建工具")
    print("=" * 60)
    print("任务：创建直径3cm、高10cm的不锈钢圆柱体")
    print("输出目录：S:\\PG-Dev\\AI助理生产成果")
    print("=" * 60)
    
    try:
        success = create_stainless_steel_cylinder()
        
        if success:
            print("\n✅ 圆柱体创建成功！")
            print("请检查Creo软件和输出目录中的文件。")
        else:
            print("\n❌ 圆柱体创建失败！")
            print("请检查日志文件获取详细错误信息。")
            
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"\n❌ 程序执行失败: {e}")
    
    print("\n程序结束。")


if __name__ == "__main__":
    main()