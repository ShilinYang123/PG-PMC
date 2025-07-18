#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 圆柱体生成器
创建指定尺寸和材料的圆柱体模型
"""

import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core.config_center import get_config
    from src.core.unified_logging import get_logger
    from src.creo.api_wrapper import CreoAPIWrapper
    from src.creo.connector import CreoConnectionError, CreoConnector
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保项目路径正确")
    sys.exit(1)


class CylinderGenerator:
    """圆柱体生成器"""

    def __init__(self):
        """初始化生成器"""
        self.logger = get_logger(self.__class__.__name__)

        # 从配置中获取Creo路径
        creo_path = get_config("creo.install_path")
        timeout = get_config("creo.connection_timeout", 30)

        # 调试信息
        print(f"调试: 从配置读取的Creo路径: {creo_path}")
        print(f"调试: 连接超时时间: {timeout}")

        # 如果配置中没有路径，使用默认路径
        if not creo_path:
            creo_path = (
                r"D:\Program Files\PTC\Creo 11.0.0.0\Parametric\bin\parametric.exe"
            )
            print(f"调试: 使用默认Creo路径: {creo_path}")

        # 创建连接器和API包装器
        connector = CreoConnector(creo_path=creo_path, timeout=timeout)
        self.api_wrapper = CreoAPIWrapper(connector)

    def create_cylinder_model(
        self,
        diameter_cm: float,
        height_cm: float,
        material: str = "不锈钢",
        output_dir: str = None,
    ) -> bool:
        """创建圆柱体模型

        Args:
            diameter_cm: 直径（厘米）
            height_cm: 高度（厘米）
            material: 材料名称
            output_dir: 输出目录

        Returns:
            bool: 创建是否成功
        """
        try:
            # 转换单位：厘米到毫米
            diameter_mm = diameter_cm * 10
            height_mm = height_cm * 10

            self.logger.info("开始创建圆柱体模型...")
            self.logger.info(
                f"规格: 直径{diameter_cm}cm ({diameter_mm}mm), "
                f"高度{height_cm}cm ({height_mm}mm)"
            )
            self.logger.info(f"材料: {material}")

            # 连接Creo
            if not self.api_wrapper.connect():
                raise CreoConnectionError("无法连接到Creo")

            # 生成零件名称
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            part_name = f"圆柱体_D{diameter_cm}cm_H{height_cm}cm_{timestamp}"

            # 创建新零件
            if not self.api_wrapper.create_new_part(part_name):
                raise Exception("创建零件失败")

            # 创建圆柱体几何
            if not self.api_wrapper.create_cylinder(diameter_mm, height_mm):
                raise Exception("创建圆柱体几何失败")

            # 设置材料
            if not self.api_wrapper.set_material(material):
                self.logger.warning("设置材料失败，将使用默认材料")

            # 保存模型
            if output_dir:
                output_path = Path(output_dir) / f"{part_name}.prt"
                output_path.parent.mkdir(parents=True, exist_ok=True)

                if not self.api_wrapper.save_model(str(output_path)):
                    self.logger.warning("保存到指定路径失败，模型已保存到Creo默认位置")
                else:
                    self.logger.info(f"模型已保存到: {output_path}")

            # 获取模型信息
            model_info = self.api_wrapper.get_model_info()
            self.logger.info(f"模型信息: {model_info}")

            self.logger.info("✅ 圆柱体模型创建成功！")
            return True

        except Exception as e:
            self.logger.error(f"创建圆柱体模型失败: {e}")
            return False

        finally:
            # 断开连接
            try:
                self.api_wrapper.disconnect()
            except Exception as e:
                self.logger.warning(f"断开Creo连接时出现警告: {e}")

    def create_stainless_steel_cylinder(self, output_dir: str = None) -> bool:
        """创建不锈钢圆柱体（直径3cm，高10cm）

        Args:
            output_dir: 输出目录

        Returns:
            bool: 创建是否成功
        """
        return self.create_cylinder_model(
            diameter_cm=3.0, height_cm=10.0, material="不锈钢", output_dir=output_dir
        )


def main():
    """主函数"""
    print("=" * 60)
    print("PG-Dev AI设计助理 - 圆柱体生成器")
    print("=" * 60)

    # 设置输出目录
    output_dir = r"S:\PG-Dev\AI助理生产成果"

    # 创建生成器
    generator = CylinderGenerator()

    # 创建圆柱体模型
    print("\n正在创建不锈钢圆柱体模型...")
    print("规格: 直径3cm, 高度10cm")
    print("材料: 不锈钢")
    print(f"输出目录: {output_dir}")

    success = generator.create_stainless_steel_cylinder(output_dir)

    if success:
        print("\n🎉 圆柱体模型创建成功！")
        print(f"文件已保存到: {output_dir}")
        print("\n请在Creo中查看生成的模型。")
    else:
        print("\n❌ 圆柱体模型创建失败！")
        print("请检查日志获取详细错误信息。")

    print("\n" + "=" * 60)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
