#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目名称标准化工具

用于统一管理和更新项目中所有硬编码的项目名称引用，
确保通过配置文件统一管理，支持迁移时自动更新。

作者: 3AI工作室
创建时间: 2025-07-08
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from config_loader import get_config
from utils import get_project_root


class ProjectNameStandardizer:
    """项目名称标准化器"""

    def __init__(self, project_root: Optional[Path] = None):
        """初始化标准化器

        Args:
            project_root: 项目根目录，如果为None则自动获取
        """
        self.project_root = Path(project_root) if project_root else get_project_root()
        if isinstance(self.project_root, str):
            self.project_root = Path(self.project_root)
        self.config = get_config()

        # 需要标准化的文件模式
        self.file_patterns = [
            "*.md",
            "*.py",
            "*.js",
            "*.json",
            "*.yaml",
            "*.yml",
            "*.html",
            "*.css",
            "*.sh",
            "*.sql",
            "*.cfg",
            "*.ini",
            "*.txt",
            "*.dockerfile",
            "Dockerfile*",
        ]

        # 排除的目录
        self.exclude_dirs = {"bak", "logs", "__pycache__", ".git", "node_modules"}

        # 从统一配置获取项目名称
        project_name = self.config.get("project_name", "3AI")

        # 项目名称替换规则
        self.replacement_rules = [
            # 直接的项目名称引用
            (r"\b3AI\b", project_name),
            (r"\b3ai\b", project_name),
            # 容器名称
            (r'container_name:\s*"3ai-([\w-]+)"', r'container_name: "3AI-\1"'),
            # 数据库名称
            (r"3ai_db", "3AI_db"),
            (r"3ai_test_db", "3AI_test_db"),
            (r"3ai_dev_db", "3AI_dev_db"),
            # 网络名称
            (r"3ai-network", "3AI-network"),
            (r"3ai-dev-network", "3AI-dev-network"),
            # 项目描述和标题
            (r"3AI工作室", "3AI工作室"),
            (r"3AI项目", "3AI项目"),
            (r"3AI\s*工作室", "3AI工作室"),
            # 邮箱和域名
            (r"@3ai\.studio", "@3AI.studio"),
            (r"3ai-studio", "3AI-studio"),
            # 包名和模块名
            (r'"name":\s*"3ai-([\w-]+)"', r'"name": "3AI-\1"'),
            (r"name\s*=\s*3ai-([\w-]+)", r"name = 3AI-\1"),
        ]

    def scan_files(self) -> List[Path]:
        """扫描需要处理的文件

        Returns:
            需要处理的文件路径列表
        """
        files = []

        for pattern in self.file_patterns:
            for file_path in self.project_root.rglob(pattern):
                # 检查是否在排除目录中
                if any(
                    exclude_dir in file_path.parts for exclude_dir in self.exclude_dirs
                ):
                    continue

                if file_path.is_file():
                    files.append(file_path)

        return sorted(files)

    def analyze_file(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """分析文件中的项目名称引用

        Args:
            file_path: 文件路径

        Returns:
            (行号, 原始内容, 建议替换内容) 的列表
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except (UnicodeDecodeError, PermissionError):
            return []

        suggestions = []

        for line_num, line in enumerate(lines, 1):
            original_line = line.rstrip()
            modified_line = original_line

            # 应用替换规则
            for pattern, replacement in self.replacement_rules:
                if re.search(pattern, modified_line, re.IGNORECASE):
                    new_line = re.sub(
                        pattern, replacement, modified_line, flags=re.IGNORECASE
                    )
                    if new_line != modified_line:
                        suggestions.append((line_num, original_line, new_line))
                        modified_line = new_line

        return suggestions

    def apply_standardization(self, file_path: Path, dry_run: bool = True) -> bool:
        """应用项目名称标准化

        Args:
            file_path: 文件路径
            dry_run: 是否为试运行模式

        Returns:
            是否有修改
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError):
            return False

        original_content = content

        # 应用替换规则
        for pattern, replacement in self.replacement_rules:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

        # 检查是否有修改
        if content == original_content:
            return False

        # 如果不是试运行，写入文件
        if not dry_run:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        return True

    def generate_report(self, output_file: Optional[Path] = None) -> Dict:
        """生成项目名称标准化报告

        Args:
            output_file: 输出文件路径

        Returns:
            报告数据
        """
        files = self.scan_files()
        report = {
            "scan_time": str(Path().cwd()),
            "project_root": str(self.project_root),
            "total_files_scanned": len(files),
            "files_with_issues": [],
            "summary": {"total_issues": 0, "files_affected": 0},
        }

        for file_path in files:
            suggestions = self.analyze_file(file_path)
            if suggestions:
                relative_path = file_path.relative_to(self.project_root)
                file_report = {
                    "file": str(relative_path),
                    "issues_count": len(suggestions),
                    "suggestions": [
                        {"line": line_num, "original": original, "suggested": suggested}
                        for line_num, original, suggested in suggestions
                    ],
                }
                report["files_with_issues"].append(file_report)
                report["summary"]["total_issues"] += len(suggestions)

        report["summary"]["files_affected"] = len(report["files_with_issues"])

        # 保存报告
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

        return report

    def standardize_all(self, dry_run: bool = True) -> Dict:
        """标准化所有文件

        Args:
            dry_run: 是否为试运行模式

        Returns:
            处理结果统计
        """
        files = self.scan_files()
        results = {
            "total_files": len(files),
            "modified_files": 0,
            "modified_file_list": [],
        }

        for file_path in files:
            if self.apply_standardization(file_path, dry_run):
                results["modified_files"] += 1
                relative_path = file_path.relative_to(self.project_root)
                results["modified_file_list"].append(str(relative_path))

        return results


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="项目名称标准化工具")
    parser.add_argument("--scan", action="store_true", help="扫描并生成报告")
    parser.add_argument("--apply", action="store_true", help="应用标准化修改")
    parser.add_argument(
        "--dry-run", action="store_true", default=True, help="试运行模式（默认）"
    )
    parser.add_argument("--output", type=str, help="报告输出文件路径")

    args = parser.parse_args()

    standardizer = ProjectNameStandardizer()

    if args.scan:
        print("正在扫描项目名称引用...")
        output_file = Path(args.output) if args.output else None
        report = standardizer.generate_report(output_file)

        print("扫描完成！")
        print(f"总文件数: {report['total_files_scanned']}")
        print(f"需要修改的文件数: {report['summary']['files_affected']}")
        print(f"总问题数: {report['summary']['total_issues']}")

        if output_file:
            print(f"详细报告已保存到: {output_file}")

    elif args.apply:
        dry_run = args.dry_run
        mode_text = "试运行" if dry_run else "实际执行"
        print(f"正在{mode_text}项目名称标准化...")

        results = standardizer.standardize_all(dry_run)

        print("处理完成！")
        print(f"总文件数: {results['total_files']}")
        print(f"修改文件数: {results['modified_files']}")

        if results["modified_file_list"]:
            print("\n修改的文件:")
            for file_path in results["modified_file_list"]:
                print(f"  - {file_path}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
