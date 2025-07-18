#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置迁移脚本

用于将项目中分散的配置文件迁移到统一配置管理中心

使用方法:
    python migrate_config.py [--dry-run] [--backup]

参数:
    --dry-run: 仅显示迁移计划，不执行实际迁移
    --backup: 迁移前创建备份
    --force: 强制迁移，覆盖现有配置
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.config_center import get_config_center
    from core.config_migration import ConfigMigration
    from utils.logger import get_logger
except ImportError:
    # 简单的logger替代
    class SimpleLogger:
        def error(self, msg):
            print(f"ERROR: {msg}")

        def info(self, msg):
            print(f"INFO: {msg}")

        def warning(self, msg):
            print(f"WARNING: {msg}")

        def debug(self, msg):
            print(f"DEBUG: {msg}")

    def get_logger(name):
        return SimpleLogger()

    # 如果无法导入，则创建简单的替代类
    def get_config_center():
        print("WARNING: 使用简化的配置中心")
        return None

    class ConfigMigration:
        def __init__(self, *args, **kwargs):
            print("WARNING: 使用简化的配置迁移")

        def scan_config_files(self, *args, **kwargs):
            print("INFO: 扫描配置文件功能暂不可用")
            return []

        def migrate(self, *args, **kwargs):
            print("INFO: 迁移功能暂不可用")
            return False


logger = get_logger(__name__)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="配置迁移脚本 - 将分散的配置文件迁移到统一配置管理中心"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="仅显示迁移计划，不执行实际迁移"
    )
    parser.add_argument("--backup", action="store_true", help="迁移前创建备份")
    parser.add_argument("--force", action="store_true", help="强制迁移，覆盖现有配置")
    parser.add_argument(
        "--scan-only", action="store_true", help="仅扫描配置文件，不执行迁移"
    )
    parser.add_argument(
        "--target-dir", type=str, help="指定扫描目录（默认为项目根目录）"
    )

    args = parser.parse_args()

    try:
        # 初始化配置迁移器
        migration = ConfigMigration()

        # 设置扫描目录
        scan_dir = Path(args.target_dir) if args.target_dir else project_root

        print("🔍 开始配置迁移流程...")
        print(f"📁 扫描目录: {scan_dir}")
        print()

        # 1. 扫描配置文件
        print("📋 步骤 1: 扫描配置文件")
        config_files = migration.scan_config_files(scan_dir)

        if not config_files:
            print("❌ 未找到任何配置文件")
            return 1

        print(f"✅ 找到 {len(config_files)} 个配置文件:")
        for file_path, file_type in config_files.items():
            print(f"  📄 {file_path} ({file_type})")
        print()

        if args.scan_only:
            print("🔍 仅扫描模式，退出")
            return 0

        # 2. 创建备份（如果需要）
        if args.backup:
            print("📋 步骤 2: 创建备份")
            backup_success = migration.backup_existing_configs()
            if backup_success:
                print("✅ 备份创建成功")
            else:
                print("⚠️ 备份创建失败，但继续迁移")
            print()

        # 3. 合并配置
        print("📋 步骤 3: 合并配置")
        merged_config = migration.merge_configs(config_files)

        if not merged_config:
            print("❌ 配置合并失败")
            return 1

        print(f"✅ 配置合并完成，包含 {len(merged_config)} 个配置项")

        # 显示合并后的配置结构
        print("📊 配置结构预览:")
        _print_config_structure(merged_config, indent=2)
        print()

        # 4. 干运行模式
        if args.dry_run:
            print("🔍 干运行模式 - 显示迁移计划:")
            print("  📝 将要执行的操作:")
            print("    1. 规范化配置数据")
            print("    2. 保存到统一配置文件")
            print("    3. 更新代码引用")
            print("    4. 生成迁移报告")
            print()
            print("💡 使用 --force 参数执行实际迁移")
            return 0

        # 5. 执行迁移
        if not args.force:
            response = input("❓ 确认执行迁移？这将修改配置文件和代码引用 (y/N): ")
            if response.lower() not in ["y", "yes"]:
                print("❌ 迁移已取消")
                return 0

        print("📋 步骤 4: 执行迁移")

        # 规范化配置
        normalized_config = migration.normalize_config(merged_config)

        # 保存配置
        save_success = migration.save_unified_config(normalized_config)
        if not save_success:
            print("❌ 保存统一配置失败")
            return 1

        print("✅ 统一配置保存成功")

        # 更新代码引用
        update_success = migration.update_code_references()
        if update_success:
            print("✅ 代码引用更新成功")
        else:
            print("⚠️ 代码引用更新失败，需要手动检查")

        # 6. 生成迁移报告
        print("📋 步骤 5: 生成迁移报告")
        report = migration.generate_migration_report()

        # 保存报告
        report_file = project_root / "config_migration_report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"✅ 迁移报告已保存: {report_file}")
        print()

        # 7. 验证迁移结果
        print("📋 步骤 6: 验证迁移结果")
        config_center = get_config_center()

        try:
            # 尝试加载配置
            config_data = config_center.load_config()
            print("✅ 新配置系统加载成功")

            # 验证关键配置项
            key_configs = ["app.name", "app.version", "server.host", "server.port"]

            print("🔍 验证关键配置项:")
            for key in key_configs:
                value = config_center.get_config(key)
                if value is not None:
                    print(f"  ✅ {key}: {value}")
                else:
                    print(f"  ⚠️ {key}: 未找到")

        except Exception as e:
            print(f"❌ 配置验证失败: {e}")
            return 1

        print()
        print("🎉 配置迁移完成！")
        print("📝 后续步骤:")
        print("  1. 检查迁移报告中的警告和建议")
        print("  2. 测试应用程序功能")
        print("  3. 删除旧的配置文件（可选）")
        print("  4. 更新文档和部署脚本")

        return 0

    except KeyboardInterrupt:
        print("\n❌ 迁移被用户中断")
        return 1
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        print(f"❌ 迁移失败: {e}")
        return 1


def _print_config_structure(
    config: Dict[str, Any], indent: int = 0, max_depth: int = 3
):
    """打印配置结构"""
    if indent > max_depth * 2:
        return

    for key, value in config.items():
        prefix = " " * indent + "├─ "

        if isinstance(value, dict):
            print(f"{prefix}{key}/")
            _print_config_structure(value, indent + 2, max_depth)
        elif isinstance(value, list):
            print(f"{prefix}{key}[] ({len(value)} items)")
        else:
            # 截断长值
            str_value = str(value)
            if len(str_value) > 50:
                str_value = str_value[:47] + "..."
            print(f"{prefix}{key}: {str_value}")


if __name__ == "__main__":
    sys.exit(main())
