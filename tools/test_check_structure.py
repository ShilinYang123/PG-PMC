# -*- coding: utf-8 -*-
"""
测试 check_structure.py 功能

作者：雨俊
创建时间：2025-07-08
"""

import sys
from pathlib import Path
from check_structure import StructureChecker

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))


def test_structure_checker():
    """测试目录结构检查器"""
    print("开始测试 StructureChecker...")

    # 获取项目根目录和白名单文件路径
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    whitelist_file = root_dir / "docs" / "01-设计" / "目录结构标准清单.md"

    # 检查白名单文件是否存在
    if not whitelist_file.exists():
        print(f"❌ 白名单文件不存在: {whitelist_file}")
        return False

    try:
        # 创建检查器实例
        checker = StructureChecker(str(root_dir), str(whitelist_file))
        print("✅ 检查器实例创建成功")

        # 测试白名单解析
        whitelist_structure = checker.parse_whitelist()
        dirs_count = len(whitelist_structure["directories"])
        files_count = len(whitelist_structure["files"])
        print(f"✅ 白名单解析成功，目录: {dirs_count} 个，" f"文件: {files_count} 个")

        # 测试当前结构扫描
        current_structure = checker.scan_current_structure()
        curr_dirs = len(current_structure["directories"])
        curr_files = len(current_structure["files"])
        print(f"✅ 当前结构扫描成功，目录: {curr_dirs} 个，" f"文件: {curr_files} 个")

        # 测试结构对比
        checker.compare_structures(whitelist_structure, current_structure)
        compliance = checker.stats["compliance_rate"]
        print(f"✅ 结构对比完成，合规率: {compliance:.1f}%")

        # 测试报告生成
        report = checker.generate_report()
        print(f"✅ 报告生成成功，长度: {len(report)} 字符")

        print("\n🎉 所有测试通过！")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


if __name__ == "__main__":
    success = test_structure_checker()
    sys.exit(0 if success else 1)
