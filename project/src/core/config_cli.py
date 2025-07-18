#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 配置管理CLI工具

本模块提供命令行接口来管理项目配置。

主要功能：
1. 查看配置信息
2. 获取和设置配置值
3. 验证配置
4. 备份和恢复配置
5. 配置迁移
6. 配置导入导出

作者: 雨俊
创建时间: 2025-01-10
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

try:
    from core.config_center import ConfigCenter, get_config_center
    from core.config_migration import ConfigMigration
    from core.unified_logging import get_logger
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

    # 如果无法导入，则跳过这些功能
    ConfigCenter = None
    get_config_center = None
    ConfigMigration = None


class ConfigCLI:
    """配置管理CLI工具

    提供命令行接口来管理项目配置。
    """

    def __init__(self, project_root: Optional[Path] = None):
        """初始化CLI工具

        Args:
            project_root: 项目根目录路径
        """
        self.logger = get_logger(self.__class__.__name__)
        self.config_center = get_config_center(project_root)

    def show_info(self) -> None:
        """显示配置信息"""
        try:
            info = self.config_center.get_config_info()

            print("\n=== 配置管理中心信息 ===")
            print(f"项目根目录: {info['project_root']}")
            print(f"配置目录: {info['config_dir']}")
            print(f"当前环境: {info['environment']}")
            print(f"配置已加载: {'是' if info['config_loaded'] else '否'}")
            print(f"验证规则数: {info['validation_rules_count']}")

            print("\n=== 配置文件状态 ===")
            for config_type, path in info["config_files"].items():
                exists = info["config_exists"][config_type]
                status = "✅ 存在" if exists else "❌ 不存在"
                print(f"{config_type:10}: {status} - {path}")

        except Exception as e:
            print(f"❌ 获取配置信息失败: {e}")
            sys.exit(1)

    def show_config(
        self, key_path: Optional[str] = None, format_type: str = "yaml"
    ) -> None:
        """显示配置内容

        Args:
            key_path: 配置键路径，如果为None则显示全部配置
            format_type: 输出格式 (yaml, json)
        """
        try:
            config = self.config_center.get_config(key_path)

            if config is None:
                print(f"❌ 配置项不存在: {key_path}")
                return

            print(f"\n=== 配置内容 {'(' + key_path + ')' if key_path else ''} ===")

            if format_type == "json":
                print(json.dumps(config, indent=2, ensure_ascii=False))
            else:
                if isinstance(config, dict):
                    print(
                        yaml.dump(
                            config,
                            default_flow_style=False,
                            allow_unicode=True,
                            sort_keys=False,
                            indent=2,
                        )
                    )
                else:
                    print(f"{key_path}: {config}")

        except Exception as e:
            print(f"❌ 获取配置失败: {e}")
            sys.exit(1)

    def set_config(self, key_path: str, value: str, value_type: str = "auto") -> None:
        """设置配置值

        Args:
            key_path: 配置键路径
            value: 配置值
            value_type: 值类型 (auto, str, int, float, bool, json)
        """
        try:
            # 类型转换
            converted_value = self._convert_value(value, value_type)

            # 设置配置
            success = self.config_center.set_config(key_path, converted_value)

            if success:
                print(f"✅ 配置已更新: {key_path} = {converted_value}")
            else:
                print(f"❌ 配置更新失败: {key_path}")
                sys.exit(1)

        except Exception as e:
            print(f"❌ 设置配置失败: {e}")
            sys.exit(1)

    def validate_config(self) -> None:
        """验证配置"""
        try:
            config = self.config_center.load_config()
            errors = self.config_center._validate_config(config)

            print("\n=== 配置验证结果 ===")

            if not errors:
                print("✅ 配置验证通过，未发现问题")
            else:
                print(f"❌ 发现 {len(errors)} 个配置问题：")
                for i, error in enumerate(errors, 1):
                    print(f"  {i}. {error}")
                sys.exit(1)

        except Exception as e:
            print(f"❌ 配置验证失败: {e}")
            sys.exit(1)

    def backup_config(self, backup_name: Optional[str] = None) -> None:
        """备份配置

        Args:
            backup_name: 备份名称
        """
        try:
            success = self.config_center.backup_config(backup_name)

            if success:
                print(f"✅ 配置备份成功: {backup_name or '自动命名'}")
            else:
                print("❌ 配置备份失败")
                sys.exit(1)

        except Exception as e:
            print(f"❌ 备份配置失败: {e}")
            sys.exit(1)

    def restore_config(self, backup_name: str) -> None:
        """恢复配置

        Args:
            backup_name: 备份名称
        """
        try:
            success = self.config_center.restore_config(backup_name)

            if success:
                print(f"✅ 配置恢复成功: {backup_name}")
            else:
                print(f"❌ 配置恢复失败: {backup_name}")
                sys.exit(1)

        except Exception as e:
            print(f"❌ 恢复配置失败: {e}")
            sys.exit(1)

    def list_backups(self) -> None:
        """列出备份文件"""
        try:
            backup_dir = self.config_center.paths.backup_dir

            if not backup_dir.exists():
                print("❌ 备份目录不存在")
                return

            backup_files = list(backup_dir.glob("*.yaml"))

            if not backup_files:
                print("📁 备份目录为空")
                return

            print("\n=== 配置备份列表 ===")
            for backup_file in sorted(backup_files):
                backup_name = backup_file.stem
                file_size = backup_file.stat().st_size
                from datetime import datetime

                modified_time = datetime.fromtimestamp(backup_file.stat().st_mtime)

                print(f"📄 {backup_name}")
                print(f"   大小: {file_size} 字节")
                print(f"   时间: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print()

        except Exception as e:
            print(f"❌ 列出备份失败: {e}")
            sys.exit(1)

    def reload_config(self) -> None:
        """重新加载配置"""
        try:
            config = self.config_center.reload_config()
            print("✅ 配置重新加载完成")
            print(f"配置项总数: {len(self._flatten_config(config))}")

        except Exception as e:
            print(f"❌ 重新加载配置失败: {e}")
            sys.exit(1)

    def export_config(self, output_path: Path, format_type: str = "yaml") -> None:
        """导出配置

        Args:
            output_path: 输出文件路径
            format_type: 输出格式 (yaml, json)
        """
        try:
            config = self.config_center.load_config()

            # 确保目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存配置
            if format_type == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            else:
                with open(output_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        config,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        sort_keys=False,
                        indent=2,
                    )

            print(f"✅ 配置已导出: {output_path}")

        except Exception as e:
            print(f"❌ 导出配置失败: {e}")
            sys.exit(1)

    def import_config(self, input_path: Path, merge: bool = True) -> None:
        """导入配置

        Args:
            input_path: 输入文件路径
            merge: 是否与现有配置合并
        """
        try:
            if not input_path.exists():
                print(f"❌ 配置文件不存在: {input_path}")
                sys.exit(1)

            # 加载配置文件
            if input_path.suffix.lower() == ".json":
                with open(input_path, "r", encoding="utf-8") as f:
                    imported_config = json.load(f)
            else:
                with open(input_path, "r", encoding="utf-8") as f:
                    imported_config = yaml.safe_load(f)

            if merge:
                # 合并配置
                current_config = self.config_center.load_config()
                merged_config = self.config_center._deep_merge_dict(
                    current_config, imported_config
                )
            else:
                # 替换配置
                merged_config = imported_config

            # 验证配置
            errors = self.config_center._validate_config(merged_config)
            if errors:
                print(f"⚠️ 配置验证发现 {len(errors)} 个问题：")
                for error in errors:
                    print(f"  - {error}")

                response = input("是否继续导入？(y/N): ")
                if response.lower() != "y":
                    print("❌ 导入已取消")
                    return

            # 保存配置
            success = self.config_center._save_config_to_file(merged_config, "user")

            if success:
                # 重新加载
                self.config_center.reload_config()
                print(f"✅ 配置已导入: {input_path}")
            else:
                print("❌ 配置导入失败")
                sys.exit(1)

        except Exception as e:
            print(f"❌ 导入配置失败: {e}")
            sys.exit(1)

    def migrate_configs(self, dry_run: bool = False) -> None:
        """迁移配置

        Args:
            dry_run: 是否为试运行
        """
        try:
            migration = ConfigMigration(self.config_center.paths.project_root)

            print(f"开始配置迁移{'（试运行）' if dry_run else ''}...")

            success = migration.migrate_configs(dry_run)

            if success:
                print("✅ 配置迁移完成")

                # 生成报告
                report_path = migration.generate_migration_report()
                print(f"📄 迁移报告: {report_path}")
            else:
                print("❌ 配置迁移失败")
                sys.exit(1)

        except Exception as e:
            print(f"❌ 配置迁移失败: {e}")
            sys.exit(1)

    def search_config(self, pattern: str, case_sensitive: bool = False) -> None:
        """搜索配置项

        Args:
            pattern: 搜索模式
            case_sensitive: 是否区分大小写
        """
        try:
            config = self.config_center.load_config()
            flat_config = self._flatten_config(config)

            # 搜索匹配的配置项
            matches = []
            search_pattern = pattern if case_sensitive else pattern.lower()

            for key, value in flat_config.items():
                search_key = key if case_sensitive else key.lower()
                search_value = str(value) if case_sensitive else str(value).lower()

                if search_pattern in search_key or search_pattern in search_value:
                    matches.append((key, value))

            print(f"\n=== 搜索结果 ('{pattern}') ===")

            if not matches:
                print("❌ 未找到匹配的配置项")
                return

            print(f"找到 {len(matches)} 个匹配项：\n")

            for key, value in matches:
                print(f"📍 {key}: {value}")

        except Exception as e:
            print(f"❌ 搜索配置失败: {e}")
            sys.exit(1)

    def _convert_value(self, value: str, value_type: str) -> Any:
        """转换值类型

        Args:
            value: 字符串值
            value_type: 目标类型

        Returns:
            Any: 转换后的值
        """
        if value_type == "str":
            return value
        elif value_type == "int":
            return int(value)
        elif value_type == "float":
            return float(value)
        elif value_type == "bool":
            return value.lower() in ["true", "1", "yes", "on"]
        elif value_type == "json":
            return json.loads(value)
        elif value_type == "auto":
            # 自动检测类型
            if value.lower() in ["true", "false"]:
                return value.lower() == "true"
            elif value.isdigit():
                return int(value)
            elif value.replace(".", "", 1).isdigit():
                return float(value)
            elif value.startswith("{") or value.startswith("["):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            else:
                return value
        else:
            raise ValueError(f"不支持的值类型: {value_type}")

    def _flatten_config(
        self, config: Dict[str, Any], prefix: str = ""
    ) -> Dict[str, Any]:
        """扁平化配置字典

        Args:
            config: 配置字典
            prefix: 键前缀

        Returns:
            Dict[str, Any]: 扁平化后的配置
        """
        flat = {}

        for key, value in config.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                flat.update(self._flatten_config(value, full_key))
            else:
                flat[full_key] = value

        return flat


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器

    Returns:
        argparse.ArgumentParser: 参数解析器
    """
    parser = argparse.ArgumentParser(
        description="PG-Dev AI设计助理 - 配置管理CLI工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s info                           # 显示配置信息
  %(prog)s show                           # 显示全部配置
  %(prog)s show app.name                  # 显示特定配置项
  %(prog)s set app.debug true             # 设置配置值
  %(prog)s validate                       # 验证配置
  %(prog)s backup my_backup               # 备份配置
  %(prog)s restore my_backup              # 恢复配置
  %(prog)s export config.yaml             # 导出配置
  %(prog)s import config.yaml             # 导入配置
  %(prog)s migrate --dry-run              # 试运行配置迁移
  %(prog)s search "api_key"                # 搜索配置项
""",
    )

    parser.add_argument("--project-root", type=Path, help="项目根目录路径")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # info 命令
    subparsers.add_parser("info", help="显示配置信息")

    # show 命令
    show_parser = subparsers.add_parser("show", help="显示配置内容")
    show_parser.add_argument("key", nargs="?", help="配置键路径")
    show_parser.add_argument(
        "--format", choices=["yaml", "json"], default="yaml", help="输出格式"
    )

    # set 命令
    set_parser = subparsers.add_parser("set", help="设置配置值")
    set_parser.add_argument("key", help="配置键路径")
    set_parser.add_argument("value", help="配置值")
    set_parser.add_argument(
        "--type",
        choices=["auto", "str", "int", "float", "bool", "json"],
        default="auto",
        help="值类型",
    )

    # validate 命令
    subparsers.add_parser("validate", help="验证配置")

    # backup 命令
    backup_parser = subparsers.add_parser("backup", help="备份配置")
    backup_parser.add_argument("name", nargs="?", help="备份名称")

    # restore 命令
    restore_parser = subparsers.add_parser("restore", help="恢复配置")
    restore_parser.add_argument("name", help="备份名称")

    # list-backups 命令
    subparsers.add_parser("list-backups", help="列出备份文件")

    # reload 命令
    subparsers.add_parser("reload", help="重新加载配置")

    # export 命令
    export_parser = subparsers.add_parser("export", help="导出配置")
    export_parser.add_argument("output", type=Path, help="输出文件路径")
    export_parser.add_argument(
        "--format", choices=["yaml", "json"], default="yaml", help="输出格式"
    )

    # import 命令
    import_parser = subparsers.add_parser("import", help="导入配置")
    import_parser.add_argument("input", type=Path, help="输入文件路径")
    import_parser.add_argument(
        "--replace", action="store_true", help="替换而不是合并配置"
    )

    # migrate 命令
    migrate_parser = subparsers.add_parser("migrate", help="迁移配置")
    migrate_parser.add_argument(
        "--dry-run", action="store_true", help="试运行（不实际修改文件）"
    )

    # search 命令
    search_parser = subparsers.add_parser("search", help="搜索配置项")
    search_parser.add_argument("pattern", help="搜索模式")
    search_parser.add_argument(
        "--case-sensitive", action="store_true", help="区分大小写"
    )

    return parser


def main() -> None:
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        cli = ConfigCLI(args.project_root)

        if args.command == "info":
            cli.show_info()

        elif args.command == "show":
            cli.show_config(args.key, args.format)

        elif args.command == "set":
            cli.set_config(args.key, args.value, args.type)

        elif args.command == "validate":
            cli.validate_config()

        elif args.command == "backup":
            cli.backup_config(args.name)

        elif args.command == "restore":
            cli.restore_config(args.name)

        elif args.command == "list-backups":
            cli.list_backups()

        elif args.command == "reload":
            cli.reload_config()

        elif args.command == "export":
            cli.export_config(args.output, args.format)

        elif args.command == "import":
            cli.import_config(args.input, not args.replace)

        elif args.command == "migrate":
            cli.migrate_configs(args.dry_run)

        elif args.command == "search":
            cli.search_config(args.pattern, args.case_sensitive)

        else:
            print(f"❌ 未知命令: {args.command}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n❌ 操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
