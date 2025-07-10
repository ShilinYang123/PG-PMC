#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径标准化工具

用于扫描和标准化项目中的硬编码绝对路径，将其替换为相对路径或配置变量。
支持项目迁移时自动更新路径引用。

作者: 3AI工作室
创建时间: 2025-07-08
"""

# import os  # unused
# import sys  # unused
import re
import json
from pathlib import Path
from typing import Dict, List  # Optional, Tuple, Set unused
from datetime import datetime
from config_loader import get_project_root, get_config


class PathStandardizer:
    """路径标准化工具类"""

    def __init__(self, project_root: str = None):
        """初始化路径标准化工具

        Args:
            project_root: 项目根目录路径
        """
        if project_root:
            self.project_root = Path(project_root)
        else:
            config = get_config()
            if config and config.get("paths", {}).get("root"):
                self.project_root = Path(config["paths"]["root"])
            else:
                self.project_root = get_project_root()

        # 硬编码路径模式
        self.path_patterns = [
            # Windows绝对路径模式（只检测真正的硬编码路径）
            (r'[A-Za-z]:\\[^\s"\'\']*3[Aa][Ii][^\s"\'\']*', "absolute_path"),
            # 特定的3AI路径模式（排除已经标准化的模板变量）
            # 注意：不检测已经正确使用的{{PROJECT_ROOT}}模板变量
        ]

        # 路径替换规则
        self.replacement_rules = {
            "project_root": "{{PROJECT_ROOT}}",
            "backup_dir": "{{PROJECT_ROOT}}/bak",
            "logs_dir": "{{PROJECT_ROOT}}/logs",
            "docs_dir": "{{PROJECT_ROOT}}/docs",
            "tools_dir": "{{PROJECT_ROOT}}/tools",
            "project_dir": "{{PROJECT_ROOT}}/project",
            "absolute_path": "{{PROJECT_ROOT}}",  # 默认替换为项目根目录
        }

        # 需要排除的目录
        self.excluded_dirs = {
            "bak",
            "logs",
            "__pycache__",
            ".git",
            "node_modules",
            ".pytest_cache",
            ".vscode",
            ".idea",
            ".venv",
        }

        # 需要排除的文件扩展名
        self.excluded_extensions = {
            ".pyc",
            ".pyo",
            ".pyd",
            ".so",
            ".dll",
            ".exe",
            ".jpg",
            ".jpeg",
            ".png",
            ".gi",
            ".bmp",
            ".ico",
            ".mp3",
            ".mp4",
            ".avi",
            ".mov",
            ".zip",
            ".rar",
            ".7z",
        }

    def should_skip_file(self, file_path: Path) -> bool:
        """判断是否应该跳过文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否跳过
        """
        # 检查文件扩展名
        if file_path.suffix.lower() in self.excluded_extensions:
            return True

        # 检查路径中是否包含排除的目录
        for part in file_path.parts:
            if part in self.excluded_dirs:
                return True

        # 检查文件大小（跳过过大的文件）
        try:
            if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                return True
        except (OSError, IOError):
            return True

        return False

    def _is_already_standardized(self, line: str, path: str) -> bool:
        """判断路径是否已经正确标准化（避免误报）"""
        # 如果是在注释中的示例或文档说明，跳过
        if line.strip().startswith("#") or line.strip().startswith("//"):
            return True

        # 如果是在README或文档中的模板变量示例，跳过
        if "{{PROJECT_ROOT}}" in line and not path.startswith("s:"):
            return True

        # 如果是配置文件中的模板变量，跳过
        if "PROJECT_ROOT" in path and not path.startswith("s:"):
            return True

        # 如果是在代码中作为正则表达式模式或字符串字面量，跳过
        keywords = ["old_path_patterns", "pattern", "r'", 'r"']
        if any(keyword in line for keyword in keywords):
            return True

        # 如果是在列表或数组定义中的字符串字面量，跳过
        if line.strip().startswith("r'") or line.strip().startswith('r"'):
            return True

        return False

    def scan_file_for_paths(self, file_path: Path) -> List[Dict]:
        """扫描文件中的硬编码路径

        Args:
            file_path: 文件路径

        Returns:
            List[Dict]: 发现的路径问题列表
        """
        issues = []

        try:
            # 尝试以UTF-8编码读取文件
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                # 如果UTF-8失败，尝试其他编码
                try:
                    with open(file_path, "r", encoding="gbk") as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(file_path, "r", encoding="latin-1") as f:
                        content = f.read()

            lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                for pattern, path_type in self.path_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        original_path = match.group(0)

                        # 跳过已经正确标准化的路径（避免误报）
                        if self._is_already_standardized(line, original_path):
                            continue

                        replacement = self.replacement_rules.get(
                            path_type, "{{PROJECT_ROOT}}"
                        )

                        # 对于绝对路径，尝试转换为相对路径
                        if path_type == "absolute_path":
                            try:
                                abs_path = Path(original_path)
                                if abs_path.is_relative_to(self.project_root):
                                    rel_path = abs_path.relative_to(self.project_root)
                                    replacement = (
                                        "{{ PROJECT_ROOT }}/" + rel_path.as_posix()
                                    )
                            except (ValueError, OSError):
                                pass

                        issues.append(
                            {
                                "file": str(file_path.relative_to(self.project_root)),
                                "line": line_num,
                                "column": match.start() + 1,
                                "original": original_path,
                                "suggested": replacement,
                                "path_type": path_type,
                                "context": line.strip(),
                            }
                        )

        except Exception as e:
            print(f"警告：无法读取文件 {file_path}: {e}")

        return issues

    def scan_project(self) -> Dict:
        """扫描整个项目中的硬编码路径

        Returns:
            Dict: 扫描结果
        """
        print(f"开始扫描项目路径标准化问题: {self.project_root}")

        all_issues = []
        scanned_files = 0
        files_with_issues = 0

        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and not self.should_skip_file(file_path):
                scanned_files += 1
                issues = self.scan_file_for_paths(file_path)
                if issues:
                    files_with_issues += 1
                    all_issues.extend(issues)

                if scanned_files % 50 == 0:
                    print(f"已扫描 {scanned_files} 个文件...")

        # 统计信息
        total_issues = len(all_issues)
        path_types = {}
        for issue in all_issues:
            path_type = issue["path_type"]
            path_types[path_type] = path_types.get(path_type, 0) + 1

        result = {
            "scan_time": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "summary": {
                "scanned_files": scanned_files,
                "files_with_issues": files_with_issues,
                "total_issues": total_issues,
                "path_types": path_types,
            },
            "issues": all_issues,
        }

        print(
            f"扫描完成: {scanned_files} 个文件，{files_with_issues} 个文件有问题，"
            f"共 {total_issues} 个问题"
        )
        return result

    def apply_standardization(self, dry_run: bool = False) -> List[str]:
        """应用路径标准化

        Args:
            dry_run: 是否为试运行模式

        Returns:
            List[str]: 修改的文件列表
        """
        scan_result = self.scan_project()
        modified_files = set()

        # 按文件分组问题
        files_issues = {}
        for issue in scan_result["issues"]:
            file_path = issue["file"]
            if file_path not in files_issues:
                files_issues[file_path] = []
            files_issues[file_path].append(issue)

        print(
            f"{'试运行' if dry_run else '正式运行'}路径标准化，将修改 {len(files_issues)} 个文件"
        )

        for file_path, issues in files_issues.items():
            full_path = self.project_root / file_path

            try:
                # 读取文件内容
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    encoding = "utf-8"
                except UnicodeDecodeError:
                    try:
                        with open(full_path, "r", encoding="gbk") as f:
                            content = f.read()
                        encoding = "gbk"
                    except UnicodeDecodeError:
                        with open(full_path, "r", encoding="latin-1") as f:
                            content = f.read()
                        encoding = "latin-1"

                # 应用替换（按行号倒序处理，避免位置偏移）
                modified = False
                for issue in sorted(
                    issues, key=lambda x: (x["line"], x["column"]), reverse=True
                ):
                    original = issue["original"]
                    replacement = issue["suggested"]

                    if original in content:
                        content = content.replace(original, replacement)
                        modified = True

                if modified:
                    if not dry_run:
                        # 写回文件
                        with open(full_path, "w", encoding=encoding) as f:
                            f.write(content)

                    modified_files.add(file_path)
                    print(f"{'[试运行] ' if dry_run else ''}修改文件: {file_path}")

            except Exception as e:
                print(f"错误：无法处理文件 {file_path}: {e}")

        return list(modified_files)

    def generate_report(self, output_file: str = None) -> str:
        """生成路径标准化报告

        Args:
            output_file: 输出文件路径

        Returns:
            str: 报告文件路径
        """
        scan_result = self.scan_project()

        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = (
                self.project_root
                / "logs"
                / f"path_standardization_report_{timestamp}.json"
            )
        else:
            output_file = Path(output_file)

        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 保存报告
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(scan_result, f, ensure_ascii=False, indent=2)

        print(f"路径标准化报告已保存到: {output_file}")
        return str(output_file)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="项目路径标准化工具")
    parser.add_argument("--scan", action="store_true", help="扫描项目中的硬编码路径")
    parser.add_argument("--apply", action="store_true", help="应用路径标准化")
    parser.add_argument(
        "--dry-run", action="store_true", help="试运行模式（不实际修改文件）"
    )
    parser.add_argument("--report", type=str, help="生成报告到指定文件")
    parser.add_argument("--project-root", type=str, help="项目根目录路径")

    args = parser.parse_args()

    # 创建标准化工具实例
    standardizer = PathStandardizer(args.project_root)

    if args.scan or args.report:
        # 扫描并生成报告
        report_file = standardizer.generate_report(args.report)
        print(f"扫描完成，报告保存到: {report_file}")

    elif args.apply:
        # 应用标准化
        modified_files = standardizer.apply_standardization(dry_run=args.dry_run)
        if modified_files:
            print(
                f"\n{
                    '试运行完成' if args.dry_run else '标准化完成'}，共修改 {
                    len(modified_files)} 个文件:"
            )
            for file_path in sorted(modified_files):
                print(f"  - {file_path}")
        else:
            print("没有需要修改的文件")

    else:
        # 默认执行扫描
        standardizer.generate_report()


if __name__ == "__main__":
    main()
