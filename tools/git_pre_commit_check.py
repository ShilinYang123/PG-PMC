#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git提交前检查脚本
防止错误内容被提交到仓库

作者: 雨俊
日期: 2025-01-08
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# 设置控制台编码为UTF-8，解决Windows下中文乱码问题
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# 添加tools目录到Python路径
tools_dir = Path(__file__).parent
sys.path.insert(0, str(tools_dir))

from logging_config import get_logger
from exceptions import ValidationError


class GitPreCommitChecker:
    """Git提交前检查器"""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.logger = get_logger("git_pre_commit_check")
        self.errors = []
        self.warnings = []

        # 项目结构标准配置
        self.expected_structure = {
            "project/src": {
                "required_dirs": [
                    "ai",
                    "config",
                    "core",
                    "ui",
                    "utils",
                ],
                "required_files": ["main.py"],
                "forbidden_files": [
                    ".eslintrc.js",
                    ".prettierrc",
                    "webpack_config.js",
                    "babel_config.js",
                    "jest_config.js",
                    "tsconfig.json",
                ],
            },
            "docs": {
                "required_dirs": ["01-设计", "02-开发", "03-管理", "04-模板"],
                "forbidden_files": ["README.md"],  # docs目录不应该有README
            },
            "tools": {
                "required_files": ["check_structure.py", "finish.py"],
                "forbidden_dirs": ["node_modules", "dist", "build"],
            },
        }

    def get_staged_files(self) -> List[str]:
        """获取暂存区的文件列表"""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return [f.strip() for f in result.stdout.split("\n") if f.strip()]
        except subprocess.CalledProcessError as e:
            self.logger.error(f"获取暂存文件失败: {e}")
            return []

    def check_project_structure(self) -> bool:
        """检查project目录结构"""
        self.logger.info("检查project目录结构...")
        project_dir = self.repo_path / "project"

        if not project_dir.exists():
            self.errors.append("project目录不存在")
            return False

        # 检查src目录结构
        src_dir = project_dir / "src"
        if not src_dir.exists():
            self.errors.append("project/src目录不存在")
            return False

        # 检查必需的子目录
        config = self.expected_structure["project/src"]
        for required_dir in config["required_dirs"]:
            dir_path = src_dir / required_dir
            if not dir_path.exists():
                self.errors.append(f"缺少必需目录: project/src/{required_dir}")

        # 检查必需的文件
        for required_file in config["required_files"]:
            file_path = src_dir / required_file
            if not file_path.exists():
                self.errors.append(f"缺少必需文件: project/src/{required_file}")

        # 检查禁止的文件（前端配置文件）
        for forbidden_file in config["forbidden_files"]:
            file_path = project_dir / forbidden_file
            if file_path.exists():
                self.errors.append(f"发现禁止的前端配置文件: project/{forbidden_file}")

        return len(self.errors) == 0

    def check_file_content_type(self, file_path: str) -> bool:
        """检查文件内容类型是否正确"""
        full_path = self.repo_path / file_path

        if not full_path.exists():
            return True  # 文件不存在，跳过检查

        # 检查project目录下的Python文件
        if file_path.startswith("project/src/") and file_path.endswith(".py"):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # 检查是否包含JavaScript/TypeScript特征
                # 使用更精确的模式，避免误报
                js_patterns = [
                    "import React",
                    "export default",
                    "console.log(",
                    "document.getElementById",
                    "window.",
                    "localStorage.",
                    "sessionStorage.",
                    "addEventListener(",
                ]

                # 检查行首的JavaScript关键字模式
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    stripped_line = line.strip()
                    
                    # 跳过注释和字符串
                    if stripped_line.startswith('#') or stripped_line.startswith('"""') or stripped_line.startswith("'''"):
                        continue
                    
                    # 检查行首的JavaScript模式
                    if (stripped_line.startswith('const ') or 
                        stripped_line.startswith('let ') or 
                        stripped_line.startswith('var ') or
                        stripped_line.startswith('function ')):
                        self.errors.append(f"Python文件包含JavaScript代码: {file_path} (第{line_num}行)")
                        return False
                
                # 检查其他JavaScript特征
                for pattern in js_patterns:
                    if pattern in content:
                        self.errors.append(f"Python文件包含JavaScript代码: {file_path}")
                        return False

            except Exception as e:
                self.warnings.append(f"无法读取文件内容: {file_path} - {e}")

        return True

    def check_docs_structure(self) -> bool:
        """检查docs目录结构"""
        self.logger.info("检查docs目录结构...")
        docs_dir = self.repo_path / "docs"

        if not docs_dir.exists():
            self.warnings.append("docs目录不存在")
            return True  # docs目录可选

        # 检查必需的子目录
        config = self.expected_structure["docs"]
        for required_dir in config["required_dirs"]:
            dir_path = docs_dir / required_dir
            if not dir_path.exists():
                self.warnings.append(f"建议添加目录: docs/{required_dir}")

        return True

    def check_tools_structure(self) -> bool:
        """检查tools目录结构"""
        self.logger.info("检查tools目录结构...")
        tools_dir = self.repo_path / "tools"

        if not tools_dir.exists():
            self.errors.append("tools目录不存在")
            return False

        # 检查必需的文件
        config = self.expected_structure["tools"]
        for required_file in config["required_files"]:
            file_path = tools_dir / required_file
            if not file_path.exists():
                self.errors.append(f"缺少必需文件: tools/{required_file}")

        # 检查禁止的目录
        for forbidden_dir in config["forbidden_dirs"]:
            dir_path = tools_dir / forbidden_dir
            if dir_path.exists():
                self.errors.append(f"发现禁止的目录: tools/{forbidden_dir}")

        return len(self.errors) == 0

    def check_file_encoding(self, file_path: str) -> bool:
        """检查文件编码"""
        full_path = self.repo_path / file_path

        if not full_path.exists() or not file_path.endswith(
            (".py", ".md", ".json", ".yaml", ".yml")
        ):
            return True

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                f.read()
            return True
        except UnicodeDecodeError:
            self.errors.append(f"文件编码不是UTF-8: {file_path}")
            return False
        except Exception as e:
            self.warnings.append(f"无法检查文件编码: {file_path} - {e}")
            return True

    def run_checks(self) -> bool:
        """运行所有检查"""
        self.logger.info("开始Git提交前检查...")

        # 获取暂存文件
        staged_files = self.get_staged_files()
        self.logger.info(f"检查 {len(staged_files)} 个暂存文件")

        # 基础结构检查
        structure_ok = True
        structure_ok &= self.check_project_structure()
        structure_ok &= self.check_docs_structure()
        structure_ok &= self.check_tools_structure()

        # 文件级检查
        files_ok = True
        for file_path in staged_files:
            files_ok &= self.check_file_content_type(file_path)
            files_ok &= self.check_file_encoding(file_path)

        # 输出检查结果
        self.print_results()

        return structure_ok and files_ok and len(self.errors) == 0

    def print_results(self):
        """输出检查结果"""
        print("\n" + "=" * 60)
        print("Git提交前检查结果")
        print("=" * 60)

        if self.errors:
            print(f"\n[ERROR] 发现 {len(self.errors)} 个错误:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")

        if self.warnings:
            print(f"\n[WARNING] 发现 {len(self.warnings)} 个警告:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        if not self.errors and not self.warnings:
            print("\n[SUCCESS] 所有检查通过！")
        elif not self.errors:
            print("\n[SUCCESS] 主要检查通过，但有警告需要注意")
        else:
            print("\n[FAILED] 检查失败，请修复错误后重新提交")

        print("=" * 60)


def main():
    """主函数"""
    # 获取Git仓库路径
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
    else:
        # 默认使用当前目录
        repo_path = os.getcwd()

        # 如果在tools目录下运行，使用父目录
        if Path(repo_path).name == "tools":
            repo_path = str(Path(repo_path).parent)

    checker = GitPreCommitChecker(repo_path)

    try:
        success = checker.run_checks()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"检查过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
