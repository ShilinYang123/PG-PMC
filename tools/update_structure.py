#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目录结构更新工具

功能:
- 扫描项目目录结构
- 生成标准化的目录结构清单
- 支持排除特定目录和文件
- 生成Markdown格式的结构文档

作者: 雨俊
创建时间: 2024-12-20
最后更新: 2025-06-25
"""

import sys
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# 导入工具模块
from utils import get_project_root

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class DirectoryStructureGenerator:
    """目录结构生成器"""

    def __init__(self):
        self.excluded_dirs = {
            '__pycache__', '.git', '.vscode', '.idea', 'node_modules',
            '.pytest_cache', '.coverage', 'htmlcov', 'dist', 'build',
            '*.egg-info', '.tox', '.mypy_cache', '.DS_Store',
            'Thumbs.db', '.venv', 'venv', 'env'
        }

        self.excluded_files = {
            '.gitignore', '.gitkeep', '.DS_Store', 'Thumbs.db',
            '*.pyc', '*.pyo', '*.pyd', '__pycache__',
            '*.so', '*.dylib', '*.dll'
        }

        self.stats = {
            'total_dirs': 0,
            'total_files': 0,
            'template_files': 0
        }

    def should_exclude(self, path: Path) -> bool:
        """判断是否应该排除某个路径"""

        # 排除特定目录
        if path.name in self.excluded_dirs:
            return True

        # 排除特定文件
        if path.is_file() and path.name in self.excluded_files:
            return True

        return False

    def scan_directory(self, dir_path: Path, relative_path: str = "") -> List[Dict]:
        """扫描目录结构

        Args:
            dir_path: 要扫描的目录路径
            relative_path: 相对路径前缀

        Returns:
            目录结构列表
        """
        items = []

        try:
            # 获取目录下所有项目
            entries = list(dir_path.iterdir())
            # 按名称排序，目录在前
            entries.sort(key=lambda x: (x.is_file(), x.name.lower()))

            for entry in entries:
                if self.should_exclude(entry):
                    continue

                # 构建相对路径
                if relative_path:
                    item_relative_path = f"{relative_path}/{entry.name}"
                else:
                    item_relative_path = entry.name

                if entry.is_dir():
                    # 目录
                    self.stats['total_dirs'] += 1
                    item = {
                        'type': 'directory',
                        'name': entry.name,
                        'path': item_relative_path,
                        'children': self.scan_directory(entry, item_relative_path)
                    }
                    items.append(item)

                else:
                    # 文件
                    self.stats['total_files'] += 1
                    if self.is_template_file(entry):
                        self.stats['template_files'] += 1

                    item = {
                        'type': 'file',
                        'name': entry.name,
                        'path': item_relative_path,
                        'size': entry.stat().st_size if entry.exists() else 0
                    }
                    items.append(item)

        except PermissionError:
            print(f"⚠️  权限不足，跳过目录: {dir_path}")
        except Exception as e:
            print(f"❌ 扫描目录时出错 {dir_path}: {e}")

        return items

    def is_template_file(self, file_path: Path) -> bool:
        """判断是否为模板文件"""
        template_extensions = {'.template', '.tpl', '.tmpl', '.example'}
        return any(file_path.name.endswith(ext) for ext in template_extensions)

    def generate_markdown(self, structure: List[Dict], title: str = "项目目录结构") -> str:
        """生成Markdown格式的目录结构

        Args:
            structure: 目录结构数据
            title: 文档标题

        Returns:
            Markdown格式的字符串
        """
        lines = []
        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("## 目录结构")
        lines.append("")
        lines.append("```")

        def format_item(item: Dict, prefix: str = "", is_last: bool = True) -> None:
            """格式化单个项目"""
            # 选择合适的前缀符号
            if prefix == "":
                current_prefix = ""
                next_prefix = ""
            else:
                current_prefix = prefix + ("└── " if is_last else "├── ")
                next_prefix = prefix + ("    " if is_last else "│   ")

            # 添加项目名称
            if item['type'] == 'directory':
                lines.append(f"{current_prefix}{item['name']}/")
                # 处理子项目
                children = item.get('children', [])
                for i, child in enumerate(children):
                    is_last_child = (i == len(children) - 1)
                    format_item(child, next_prefix, is_last_child)
            else:
                lines.append(f"{current_prefix}{item['name']}")

        # 格式化所有顶级项目
        for i, item in enumerate(structure):
            is_last_item = (i == len(structure) - 1)
            format_item(item, "", is_last_item)

        lines.append("```")
        lines.append("")

        # 添加统计信息
        lines.append("## 统计信息")
        lines.append("")
        lines.append(f"- **目录数量**: {self.stats['total_dirs']}")
        lines.append(f"- **文件数量**: {self.stats['total_files']}")
        lines.append(f"- **模板文件**: {self.stats['template_files']}")
        lines.append("")

        # 添加说明
        lines.append("## 说明")
        lines.append("")
        lines.append("- 此文档由目录结构更新工具自动生成")
        lines.append("- 已排除常见的临时文件和缓存目录")
        lines.append("- 模板文件包括 .template、.tpl、.tmpl、.example 等扩展名的文件")
        lines.append("")

        return "\n".join(lines)

    def save_structure(self, structure: List[Dict], output_file: Path) -> None:
        """保存目录结构到文件

        Args:
            structure: 目录结构数据
            output_file: 输出文件路径
        """
        try:
            # 确保输出目录存在
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # 生成Markdown内容
            markdown_content = self.generate_markdown(structure)

            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print("\n✅ 目录结构标准清单已生成:")
            print(f"   {output_file}")

            print("📊 统计信息:")
            print(f"   - 目录数量: {self.stats['total_dirs']}")
            print(f"   - 文件数量: {self.stats['total_files']}")
            print(f"   - 模板文件: {self.stats['template_files']}")

        except Exception as e:
            print(f"❌ 保存文件失败: {e}")
            raise


def main():
    """主函数"""
    try:
        # 获取项目根目录
        project_root_str = get_project_root()
        project_root = Path(project_root_str)
        print(f"📁 项目根目录: {project_root}")

        # 创建生成器
        generator = DirectoryStructureGenerator()

        # 扫描目录结构
        print("🔍 正在扫描目录结构...")
        structure = generator.scan_directory(project_root)

        # 生成输出文件路径
        output_file = project_root / "docs" / "01-设计" / "目录结构标准清单.md"

        # 保存结构
        generator.save_structure(structure, output_file)

    except Exception as e:
        print(f"❌ 生成失败: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("生成完成")
    print("=" * 60)


if __name__ == "__main__":
    main()